from sentence_transformers import SentenceTransformer
import chromadb
import re
import spacy
from collections import Counter
import json
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.document_manager import EnhancedFileDocumentManager as DocumentManager
import os
from pathlib import Path


os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOFILE"] = "1"


def fix_metadata(metadata):
    """Convert list values to strings for ChromaDB compatibility"""
    if not metadata:
        return metadata
    
    fixed = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            fixed[key] = ", ".join(str(v) for v in value)
        else:
            fixed[key] = value
    return fixed



class RailAdviceAI:
    def __init__(self, use_manual_docs=True):
        print("🚀 Initializing RailAdvice AI...")
        
        # Load NLP models
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Try to load Norwegian spaCy model, fallback to English
        try:
            self.nlp = spacy.load("nb_core_news_sm")
            print("✅ Norwegian NLP model loaded")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ English NLP model loaded")
            except:
                print("⚠️ No spaCy model found - install: python -m spacy download nb_core_news_sm")
                self.nlp = None
        
        # Setup vector database
        self.client = chromadb.PersistentClient(path="./data/chromadb")
        
        # Clear existing collection if using manual docs
        if use_manual_docs:
            try:
                self.client.delete_collection("railadvice")
                print("🗑️ Cleared existing synthetic data")
            except:
                pass
        
        self.collection = self.client.get_or_create_collection("railadvice")
        
        # Document manager for manual documents
        self.doc_manager = DocumentManager()
        self.use_manual_docs = use_manual_docs
        
        # TF-IDF for keyword matching
        self.tfidf = TfidfVectorizer(stop_words=None, ngram_range=(1, 3))
        self.documents_text = []
        self.documents_metadata = []
        
        # Enhanced patterns for better recognition
        self.greeting_patterns = [
            r'\b(hei|hi|hallo|god\s*morgen|god\s*dag|god\s*kveld)\b',
            r'^(hey|hello|yo|halla)$',
            r'(hva\s*skjer|hvordan\s*har\s*du\s*det|hvordan\s*går\s*det)',
        ]
        
        self.identity_patterns = [
            r'\b(hvem\s*er\s*du|who\s*are\s*you|hva\s*er\s*du|what\s*are\s*you)\b',
            r'\b(kan\s*du\s*presentere\s*deg|introduce\s*yourself)\b',
            r'\b(fortell\s*om\s*deg\s*selv|tell\s*me\s*about\s*yourself)\b'
        ]
        
        self.help_patterns = [
            r'\b(hjelp|help|hva\s*kan\s*du|what\s*can\s*you)\b',
            r'\b(kommandoer|commands|funksjonalitet|functionality)\b'
        ]
        
        # Enhanced keyword patterns for better matching
        self.keyword_patterns = {
            "kostnad": ["kostnad", "pris", "budget", "økonomi", "millioner", "nok", "kroner", "estimat", "verdi", "investering"],
            "tid": ["tid", "varighet", "år", "måneder", "tidsplan", "ferdig", "implementering", "deadline", "fremdrift"],
            "personer": ["lars", "mortvedt", "konsulent", "ansvarlig", "prosjektleder", "team", "ansatte", "kompetanse"],
            "teknologi": ["etcs", "rams", "tsi", "signal", "sikkerhet", "infrastruktur", "level", "system", "teknisk", "ertms"],
            "prosjekt": ["prosjekt", "oppdrag", "kunde", "kontrakt", "flytoget", "fornebubanen", "bybanen", "jernbane"],
            "bedrift": ["railadvice", "selskap", "firma", "ansatte", "tjenester", "kompetanse", "konsulent"],
            "erfaring": ["erfaring", "kompetanse", "ekspertise", "kunnskap", "sertifisering", "utdanning"]
        }
        
        # Load manual documents if enabled
        if use_manual_docs:
            self.load_manual_documents()
        
        print("✅ RailAdvice AI ready!")
        
        # Show knowledge base status
        doc_count = len(self.collection.get()['ids'])
        manual_count = len(self.doc_manager.list_documents())
        print(f"📊 Knowledge base: {doc_count} loaded documents ({manual_count} manual documents available)")

    def classify_input_type(self, text):
        """Classify the type of input to handle it appropriately"""
        text_lower = text.lower().strip()
        
        # Single word inputs
        if len(text.split()) == 1:
            word = text_lower
            # Check if it's a greeting
            if word in ['hei', 'hi', 'hallo', 'hey', 'hello']:
                return "greeting"
            # Check if it's a technical term we might know about
            for category, keywords in self.keyword_patterns.items():
                if word in keywords:
                    return f"single_keyword_{category}"
            return "single_word"
        
        # Check for greetings
        for pattern in self.greeting_patterns:
            if re.search(pattern, text_lower):
                return "greeting"
        
        # Check for identity questions
        for pattern in self.identity_patterns:
            if re.search(pattern, text_lower):
                return "identity"
        
        # Check for help requests
        for pattern in self.help_patterns:
            if re.search(pattern, text_lower):
                return "help"
        
        # Check for questions vs statements
        if text.strip().endswith('?') or text_lower.startswith(('hva', 'hvem', 'hvor', 'når', 'hvorfor', 'hvordan', 'kan', 'vil', 'what', 'who', 'where', 'when', 'why', 'how', 'can', 'will')):
            return "question"
        
        return "statement"

    def get_identity_response(self):
        """Response for identity questions"""
        doc_count = len(self.doc_manager.list_documents())
        
        if doc_count == 0:
            return """Jeg er RailAdvice AI, din jernbanetekniske assistent. 

Jeg er utviklet for å hjelpe med jernbanerelaterte spørsmål, men har ingen dokumenter å jobbe med ennå. Legg til dokumenter via document manager, så kan jeg gi deg svar basert på din kunnskap!"""
        
        return f"""Jeg er RailAdvice AI, din intelligente assistent for jernbanetekniske spørsmål.

Jeg har tilgang til {doc_count} dokumenter og kan hjelpe deg med:
• Tekniske spørsmål om jernbane (ETCS, RAMS, TSI)  
• Prosjektinformasjon og kostnadsestimat
• Kompetanse og erfaring
• Generelle jernbanerelaterte emner

Still meg gjerne spørsmål - jeg svarer basert på dokumentasjonen din!"""

    def get_help_response(self):
        """Response for help requests"""
        return """Her er hva jeg kan hjelpe deg med:

**Spørsmålstyper jeg forstår:**
• Tekniske spørsmål: "Hva er ETCS?" "Fortell om RAMS"
• Kostnadsspørsmål: "Hva koster prosjektet?" 
• Tidsspørsmål: "Hvor lang tid tar implementering?"
• Kompetanse: "Hvem er ekspert på signalsystemer?"
• Prosjektinfo: "Fortell om Flytoget-oppdraget"

**Tips for bedre svar:**
• Vær spesifikk i spørsmålene dine
• Bruk fagtermer jeg kjenner til  
• Spør oppfølgingsspørsmål for mer detaljer

Prøv å spørre om noe - jeg lærer fra dokumentene dine!"""

    def handle_single_word(self, word, word_type):
        """Handle single word inputs intelligently"""
        word_lower = word.lower()
        
        if word_type == "single_word":
            # Try to find relevant information about the word
            if len(self.documents_text) > 0:
                # Search for the word in documents
                try:
                    query_embedding = self.embedder.encode([word])[0].tolist()
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=1
                    )
                    
                    if results['documents'] and results['documents'][0]:
                        doc_text = results['documents'][0][0]
                        # Extract context around the word
                        sentences = [s.strip() for s in doc_text.split('.') if word_lower in s.lower()]
                        if sentences:
                            best_sentence = sentences[0][:200] + "..." if len(sentences[0]) > 200 else sentences[0]
                            return f"Angående '{word}': {best_sentence}. Ønsker du mer informasjon?"
                except:
                    pass
            
            return f"Du skrev '{word}'. Kan du utdype hva du vil vite om dette, eller still et mer spesifikt spørsmål?"
        
        elif word_type.startswith("single_keyword_"):
            category = word_type.replace("single_keyword_", "")
            category_names = {
                "teknologi": "tekniske løsninger",
                "kostnad": "kostnader og økonomi", 
                "tid": "tidsplaner og fremdrift",
                "personer": "personer og kompetanse",
                "prosjekt": "prosjekter og oppdrag",
                "bedrift": "RailAdvice og våre tjenester",
                "erfaring": "erfaring og ekspertise"
            }
            
            category_name = category_names.get(category, category)
            return f"Du spør om {category_name}. Hva spesifikt vil du vite? For eksempel: kostnader, implementering, eller tekniske detaljer?"

    def extract_meaningful_content(self, text, max_sentences=3):
        """Extract meaningful content, avoiding metadata and JSON"""
        if not text:
            return []
        
        # Split into sentences
        sentences = []
        for delimiter in ['.', '!', '?', '\n']:
            if delimiter in text:
                parts = text.split(delimiter)
                sentences.extend([s.strip() for s in parts if s.strip()])
                break
        
        if not sentences:
            sentences = [text.strip()]
        
        good_sentences = []
        for sentence in sentences:
            # Skip if too short or looks like metadata
            if (len(sentence) < 20 or 
                sentence.startswith(('{', '[', '"')) or
                'json' in sentence.lower() or
                'metadata' in sentence.lower() or
                sentence.count('"') > 2):
                continue
            
            # Clean up the sentence
            sentence = re.sub(r'\s+', ' ', sentence)
            sentence = sentence.strip()
            
            if sentence and len(sentence) > 20:
                good_sentences.append(sentence)
            
            if len(good_sentences) >= max_sentences:
                break
        
        return good_sentences

    def generate_smart_response(self, question, docs, confidence, input_type):
        """Generate intelligent, natural responses based on input type"""
        
        # Handle special input types first
        if input_type == "greeting":
            doc_count = len(self.doc_manager.list_documents())
            if doc_count == 0:
                return "Hei! Jeg er RailAdvice AI. Jeg har ingen dokumenter å jobbe med ennå - legg til dokumenter så kan jeg hjelpe deg!"
            return f"Hei! Jeg er RailAdvice AI med {doc_count} dokumenter tilgjengelig. Hva kan jeg hjelpe deg med?"
        
        elif input_type == "identity":
            return self.get_identity_response()
        
        elif input_type == "help":
            return self.get_help_response()
        
        elif input_type.startswith("single_"):
            return self.handle_single_word(question, input_type)
        
        # Handle cases with no relevant documents
        if not docs:
            return self.generate_intelligent_fallback(question, input_type)
        
        # Process documents and generate response
        question_lower = question.lower()
        response_parts = []
        
        # Extract meaningful content from documents
        for doc in docs[:2]:  # Use max 2 documents
            if isinstance(doc, str):
                meaningful_sentences = self.extract_meaningful_content(doc, max_sentences=2)
                response_parts.extend(meaningful_sentences)
        
        if not response_parts:
            return "Jeg fant relevante dokumenter, men ikke klart innhold som svarer på spørsmålet ditt. Kan du være mer spesifikk?"
        
        # Build natural response
        if input_type == "question":
            # For questions, provide direct answers
            main_content = response_parts[0]
            
            # Add specific handling for common question types
            if any(word in question_lower for word in ['hva er', 'what is', 'kan du forklare']):
                response = f"{main_content}"
                if len(response_parts) > 1:
                    response += f" {response_parts[1]}"
            else:
                response = main_content
            
            # Add follow-up based on confidence
            if confidence == "High" and len(response_parts) > 1:
                response += " Ønsker du mer detaljert informasjon?"
            elif confidence == "Medium":
                response += " Trenger du mer spesifikke detaljer?"
            
        else:
            # For statements, provide relevant information
            response = f"Basert på dokumentasjonen: {response_parts[0]}"
            if len(response_parts) > 1:
                response += f" {response_parts[1]}"
        
        # Clean up response
        response = re.sub(r'\s+', ' ', response).strip()
        response = re.sub(r'([.!?])\s*([.!?])', r'\1', response)
        
        # Ensure response ends properly
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        return response

    def generate_intelligent_fallback(self, question, input_type):
        """Generate intelligent responses when no documents match"""
        manual_doc_count = len(self.doc_manager.list_documents())
        
        if manual_doc_count == 0:
            return """Jeg har ingen dokumenter å svare basert på ennå. 
            
Legg til dokumenter via document manager (python main.py), så kan jeg hjelpe deg med jernbanerelaterte spørsmål!"""
        
        question_lower = question.lower()
        
        # Try to be helpful based on question content
        if any(word in question_lower for word in ['etcs', 'ertms']):
            return f"Jeg ser du spør om ETCS/ERTMS, men fant ikke spesifikk informasjon i de {manual_doc_count} dokumentene. Legg gjerne til mer teknisk dokumentasjon om signalsystemer."
        
        elif any(word in question_lower for word in ['kostnad', 'pris', 'kost']):
            return f"Du spør om kostnader, men jeg fant ikke prisopplysninger i dokumentene. Har du budsjett- eller kostnadsdokumenter du kan legge til?"
        
        elif any(word in question_lower for word in ['rams', 'sikkerhet']):
            return f"RAMS og sikkerhet er viktige tema. Jeg har {manual_doc_count} dokumenter, men fant ikke svar på ditt spesifikke spørsmål. Prøv å være mer spesifikk eller legg til flere tekniske dokumenter."
        
        else:
            return f"Jeg forstår spørsmålet ditt, men fant ikke svar i de {manual_doc_count} dokumentene. Prøv å omformulere spørsmålet eller legg til mer relevant dokumentasjon."
    
    def load_manual_documents(self):
        """Load all manually added documents into the AI"""
        manual_docs = self.doc_manager.load_all_documents()
        
        if not manual_docs:
            print("⚠️ No manual documents found. Use document_manager.py to add documents.")
            return
        
        print(f"📄 Loading {len(manual_docs)} manual documents...")
        
        for doc in manual_docs:
            try:
                content = None
                if isinstance(doc, dict):
                    content = (doc.get('content') or 
                              doc.get('text') or 
                              doc.get('body') or
                              doc.get('description') or
                              str(doc))
                else:
                    content = str(doc)
                
                if not content:
                    print(f"⚠️ Skipping document with no content: {doc.get('title', 'Unknown')}")
                    continue
                
                metadata = {
                    "type": doc.get('type', 'unknown'),
                    "category": doc.get('category', 'general'),
                    "title": doc.get('title', 'Untitled'),
                    "tags": doc.get('tags', []),
                    "source": "manual",
                    "doc_id": doc.get('id', 'unknown'),
                    "added_date": doc.get('added_date', datetime.now().isoformat())
                }
                
                self.add_document_to_ai(
                    text=content,
                    metadata=metadata
                )
                
            except Exception as e:
                print(f"⚠️ Error loading document {doc.get('title', 'Unknown')}: {e}")
                continue
        
        print(f"✅ Loaded documents into AI (attempted {len(manual_docs)})")
    
    def reload_documents(self):
        """Reload all manual documents (call this after adding/removing documents)"""
        try:
            self.client.delete_collection("railadvice")
        except:
            pass
        self.collection = self.client.get_or_create_collection("railadvice")
        
        self.documents_text = []
        self.documents_metadata = []
        
        self.load_manual_documents()
        
        print("🔄 Documents reloaded successfully")
    
    def add_document_to_ai(self, text, metadata):
        """Add document to AI (internal method)"""
        try:
            if not isinstance(text, str):
                text = str(text)
            
            if not text.strip():
                print("⚠️ Skipping empty document")
                return
            
            embedding = self.embedder.encode([text])[0].tolist()
            
            self.documents_text.append(text)
            self.documents_metadata.append(metadata)
            
            metadata = metadata.copy()
            metadata['ai_added_date'] = datetime.now().isoformat()
            metadata['text_length'] = len(text)
            metadata['doc_index'] = len(self.documents_text) - 1
            
            doc_id = f"doc_{len(self.collection.get()['ids']) + 1}"
            
            fixed_metadata = fix_metadata(metadata)
            
            self.collection.add(
                documents=[text],
                metadatas=[fixed_metadata],
                ids=[doc_id],
                embeddings=[embedding]
            )
            
            if len(self.documents_text) > 1:
                try:
                    self.tfidf.fit(self.documents_text)
                except Exception as e:
                    print(f"⚠️ TF-IDF update failed: {e}")
                    
        except Exception as e:
            print(f"⚠️ Failed to add document to AI: {e}")
    
    def extract_keywords_and_intent(self, text):
        """Enhanced keyword extraction and intent recognition"""
        text_lower = text.lower()
        
        # Extract entities if spaCy is available
        entities = []
        if self.nlp:
            try:
                doc = self.nlp(text)
                entities = [(ent.text, ent.label_) for ent in doc.ents]
            except:
                pass
        
        # Find keyword categories
        found_categories = []
        for category, keywords in self.keyword_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                found_categories.append(category)
        
        # Extract specific terms from document tags and titles
        specific_terms = []
        for doc_meta in self.documents_metadata:
            title_words = doc_meta.get('title', '').lower().split()
            for word in title_words:
                if len(word) > 3 and word in text_lower:
                    specific_terms.append(word)
            
            for tag in doc_meta.get('tags', []):
                if isinstance(tag, str) and tag.lower() in text_lower:
                    specific_terms.append(tag)
        
        specific_terms = list(set(specific_terms))
        
        return {
            "categories": found_categories,
            "entities": entities,
            "specific_terms": specific_terms,
            "length": len(text.split())
        }
    
    def find_best_response(self, question, intent_analysis):
        """Find best response using semantic search with improved relevance"""
        
        if not self.documents_text:
            return [], "No Documents", intent_analysis
        
        try:
            query_embedding = self.embedder.encode([question])[0].tolist()
            
            # Adjust number of results based on query complexity
            max_results = min(5, len(self.documents_text))
            if intent_analysis['length'] < 3:  # Simple queries
                max_results = min(2, len(self.documents_text))
            
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            print(f"🔍 Semantic search returned {len(semantic_results.get('documents', [[]])[0])} documents")
            
            best_docs = []
            confidence = "Medium"
            
            if semantic_results['documents'] and semantic_results['documents'][0]:
                documents = semantic_results['documents'][0]
                distances = semantic_results.get('distances', [[]])[0] if semantic_results.get('distances') else []
                
                # Filter documents by relevance
                for i, doc in enumerate(documents):
                    # Skip if document is too irrelevant (distance too high)
                    if distances and len(distances) > i and distances[i] > 1.2:
                        continue
                    best_docs.append(doc)
                    if len(best_docs) >= 2:  # Limit to 2 most relevant documents
                        break
                
                # Determine confidence based on relevance and matches
                if distances and len(distances) > 0:
                    best_distance = distances[0]
                    if best_distance < 0.7:
                        confidence = "High"
                    elif best_distance < 1.0:
                        confidence = "Medium"
                    else:
                        confidence = "Low"
            
            print(f"🔍 Returning {len(best_docs)} documents with confidence: {confidence}")
            return best_docs, confidence, intent_analysis
            
        except Exception as e:
            print(f"⚠️ Error in find_best_response: {e}")
            return [], "Error", intent_analysis
    
    def query(self, question):
        """Main query function with enhanced response generation"""
        print(f"❓ Processing: {question}")
        
        # Classify input type for better handling
        input_type = self.classify_input_type(question)
        print(f"🎯 Input type: {input_type}")
        
        # Handle special cases that don't need document search
        if input_type in ["greeting", "identity", "help"]:
            if input_type == "greeting":
                response = self.generate_smart_response(question, [], "Greeting", input_type)
            elif input_type == "identity":
                response = self.get_identity_response()
            else:  # help
                response = self.get_help_response()
            
            return {
                "answer": response,
                "sources": 0,
                "confidence": input_type.title(),
                "input_type": input_type,
                "intent_categories": [input_type],
                "specific_terms": [],
                "analysis": {}
            }
        
        # Check if we have any documents for content queries
        if not self.documents_text and input_type not in ["single_word", "single_keyword"]:
            return {
                "answer": "Jeg har ingen dokumenter å svare basert på. Legg til dokumenter med document manager, så kan jeg hjelpe deg!",
                "sources": 0,
                "confidence": "No Documents",
                "input_type": input_type,
                "intent_categories": [],
                "specific_terms": [],
                "analysis": {}
            }
        
        try:
            intent_analysis = self.extract_keywords_and_intent(question)
            print(f"🔍 Intent: Categories={intent_analysis['categories']}, Terms={intent_analysis['specific_terms']}")
            
            best_docs, confidence, analysis = self.find_best_response(question, intent_analysis)
            
            response = self.generate_smart_response(question, best_docs, confidence, input_type)
            
            return {
                "answer": response,
                "sources": len(best_docs),
                "confidence": confidence,
                "input_type": input_type,
                "intent_categories": intent_analysis['categories'],
                "specific_terms": intent_analysis['specific_terms'],
                "analysis": analysis
            }
        except Exception as e:
            print(f"⚠️ Error in query processing: {e}")
            return {
                "answer": f"Beklager, det oppstod en feil under behandling av spørsmålet ditt. Prøv igjen med et annet spørsmål.",
                "sources": 0,
                "confidence": "Error",
                "input_type": input_type,
                "intent_categories": [],
                "specific_terms": [],
                "analysis": {}
            }


class ContextualRailAdviceAI(RailAdviceAI):
    def __init__(self, use_manual_docs=True, memory_file="conversation_memory.json"):
        super().__init__(use_manual_docs)
        self.memory_file = Path(memory_file)
        self.conversation_history = self.load_memory()
        self.farewell_patterns = [
            r"\b(hade|ha det|bye|farvel|snakkes|vi ses)\b",
            r"(takk for hjelpen|takk skal du ha)"
        ]

    def load_memory(self):
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_memory(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)

    def classify_input_type(self, text):
        text_lower = text.lower().strip()
        for pattern in self.farewell_patterns:
            if re.search(pattern, text_lower):
                return "farewell"
        return super().classify_input_type(text)

    def generate_smart_response(self, question, docs, confidence, input_type):
        if input_type == "farewell":
            return "Takk for praten! 🚆 Ta kontakt igjen når du trenger hjelp med jernbaneprosjekter."
        return super().generate_smart_response(question, docs, confidence, input_type)

    def query(self, question):
        result = super().query(question)
        self.conversation_history.append({"user": question, "ai": result["answer"]})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        self.save_memory()
        return result


# Test function
if __name__ == "__main__":
    ai = RailAdviceAI(use_manual_docs=True)
    
    # Test different input types
    test_inputs = [
        "hei",
        "hvem er du?",
        "etcs",
        "Hva er ETCS?",
        "kostnad",
        "Hva koster prosjektet?",
        "hjelp"
    ]
    
    print("\n" + "="*50)
    print("Testing Enhanced RailAdvice AI")
    print("="*50)
    
    for test_input in test_inputs:
        print(f"\nInput: '{test_input}'")
        result = ai.query(test_input)
        print(f"Answer: {result['answer']}")
        print(f"Type: {result.get('input_type', 'unknown')}, Confidence: {result['confidence']}")
        print("-" * 40)