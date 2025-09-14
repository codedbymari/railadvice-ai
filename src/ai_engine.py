import os
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter
import numpy as np


# Set environment variables before any imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_NOFILE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Global variables for lazy loading
_embedder = None
_nlp = None
_chroma_client = None
_loading_lock = asyncio.Lock() if 'asyncio' in globals() else None


def fix_metadata(metadata):
    """Convert list values to strings for ChromaDB compatibility"""
    if not metadata:
        return metadata
    
    fixed = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            fixed[key] = ", ".join(str(v) for v in value)
        else:
            fixed[key] = str(value) if value is not None else ""
    return fixed


class LazyLoader:
    """Handles lazy loading of heavy dependencies"""
    
    @staticmethod
    def get_embedder():
        global _embedder
        if _embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("🧠 Loading SentenceTransformer model...")
                _embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ SentenceTransformer loaded")
            except Exception as e:
                print(f"❌ Failed to load SentenceTransformer: {e}")
                raise
        return _embedder
    
    @staticmethod
    def get_nlp():
        global _nlp
        if _nlp is None:
            try:
                import spacy
                try:
                    _nlp = spacy.load("nb_core_news_sm")
                    print("✅ Norwegian NLP model loaded")
                except:
                    try:
                        _nlp = spacy.load("en_core_web_sm")
                        print("✅ English NLP model loaded")
                    except:
                        print("⚠️ No spaCy model found - using basic processing")
                        _nlp = None
            except Exception as e:
                print(f"⚠️ spaCy not available: {e}")
                _nlp = None
        return _nlp
    
    @staticmethod
    def get_chroma_client():
        global _chroma_client
        if _chroma_client is None:
            try:
                import chromadb
                print("🗄️ Initializing ChromaDB...")
                _chroma_client = chromadb.PersistentClient(path="./data/chromadb")
                print("✅ ChromaDB client ready")
            except Exception as e:
                print(f"❌ Failed to initialize ChromaDB: {e}")
                raise
        return _chroma_client


class RailAdviceAI:
    def __init__(self, lazy_init=True):
        print("🚀 Initializing RailAdvice AI...")
        
        # Initialize light components immediately
        self.lazy_init = lazy_init
        self.documents_text = []
        self.documents_metadata = []
        self.collection = None
        self.tfidf = None
        self._initialized = False
        self._doc_manager = None
        
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
        
        if not lazy_init:
            self.initialize_heavy_components()
        
        print("✅ RailAdvice AI ready for queries!")

    def initialize_heavy_components(self):
        """Initialize the heavy ML components"""
        if self._initialized:
            return
        
        try:
            print("🔄 Loading ML components...")
            
            # Load embedder
            self.embedder = LazyLoader.get_embedder()
            
            # Load NLP
            self.nlp = LazyLoader.get_nlp()
            
            # Setup ChromaDB
            self.client = LazyLoader.get_chroma_client()
            
            # Get or create collection (don't delete existing unless explicitly needed)
            try:
                self.collection = self.client.get_collection("railadvice")
                print("✅ Using existing ChromaDB collection")
            except:
                self.collection = self.client.create_collection("railadvice")
                print("✅ Created new ChromaDB collection")
            
            # Initialize document manager
            try:
                from document_manager import EnhancedFileDocumentManager
                self._doc_manager = EnhancedFileDocumentManager()
                print("✅ Document manager loaded")
            except Exception as e:
                print(f"⚠️ Document manager failed to load: {e}")
            
            # Initialize TF-IDF
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.tfidf = TfidfVectorizer(stop_words=None, ngram_range=(1, 3))
            except Exception as e:
                print(f"⚠️ TF-IDF not available: {e}")
                self.tfidf = None
            
            self._initialized = True
            
            # Load documents if document manager is available
            if self._doc_manager:
                self.load_knowledge_base()
            
            print("✅ Heavy components loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize heavy components: {e}")
            self._initialized = False
            raise

    def ensure_initialized(self):
        """Ensure heavy components are loaded"""
        if not self._initialized:
            self.initialize_heavy_components()
        return self._initialized

    def get_initialization_status(self):
        """Get current initialization status"""
        return {
            "initialized": self._initialized,
            "embedder_ready": _embedder is not None,
            "nlp_ready": _nlp is not None,
            "chroma_ready": _chroma_client is not None,
            "documents_loaded": len(self.documents_text),
            "collection_ready": self.collection is not None
        }

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
        doc_count = len(self.documents_text)
        
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
            if len(self.documents_text) > 0 and self.ensure_initialized():
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
                except Exception as e:
                    print(f"⚠️ Error in single word search: {e}")
            
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
        
        # Clean up metadata patterns
        cleaned_text = re.sub(r'^(PROSJEKT|TEKNISK KUNNSKAP|KOMPETANSE|MARKEDSINNSATS|INNHOLD):.*?\s*', '', text, flags=re.IGNORECASE | re.DOTALL)
        cleaned_text = re.sub(r'(Kunde|Type|Status|År|Kode|Kategori|Tittel):\s*[^ \n]+', '', cleaned_text, flags=re.IGNORECASE)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        
        good_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Skip if too short or looks like metadata
            if (len(sentence) < 30 or 
                sentence.startswith(('{', '[', '"')) or
                'json' in sentence.lower() or
                'metadata' in sentence.lower() or
                sentence.count('"') > 2 or
                'ID:' in sentence or
                len(sentence.split()) < 5):
                continue
            
            # Clean up
            sentence = re.sub(r'\(ID: [0-9a-f-]+\)', '', sentence)
            sentence = re.sub(r'\s+', ' ', sentence).strip()
            
            if sentence:
                good_sentences.append(sentence)
            
            if len(good_sentences) >= max_sentences:
                break
        
        return good_sentences

    def generate_smart_response(self, question, docs, confidence, input_type):
        """Generate intelligent, natural responses based on input type"""
        
        # Handle special input types first
        if input_type == "greeting":
            doc_count = len(self.documents_text)
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
        response_parts = []
        
        # Extract meaningful content from documents
        for doc in docs:
            meaningful_sentences = self.extract_meaningful_content(doc, max_sentences=2)
            response_parts.extend(meaningful_sentences)
        
        if not response_parts:
            return "Jeg fant relevante dokumenter, men ikke klart innhold som svarer på spørsmålet ditt. Kan du være mer spesifikk?"
        
        # Build natural response
        intro_phrases = ["Basert på min kunnskapsbase", "Dokumentasjon viser at", "Angående ditt spørsmål", "Jeg fant følgende informasjon"]
        intro = intro_phrases[np.random.randint(0, len(intro_phrases))] if len(intro_phrases) > 0 else "Basert på dokumentene"
        
        if confidence == "High":
            main_content = " ".join(response_parts)
            response = f"{intro}: {main_content}"
            if len(response_parts) > 1:
                response += " Ønsker du mer detaljert informasjon?"
        elif confidence == "Medium":
            main_content = " ".join(response_parts)
            response = f"Basert på min kunnskapsbase: {main_content}."
        else:  # Low confidence
            main_content = " ".join(response_parts[:1])
            response = f"Jeg fant noe relevant informasjon: {main_content} Kan du omformulere spørsmålet?"
        
        # Clean up response
        response = re.sub(r'\s+', ' ', response).strip()
        if not response.endswith(('.', '!', '?')):
            response += '.'
        
        return response

    def generate_intelligent_fallback(self, question, input_type):
        """Generate intelligent responses when no documents match"""
        doc_count = len(self.documents_text)
        
        if doc_count == 0:
            return """Jeg har ingen dokumenter å svare basert på ennå. 
            
Legg til dokumenter via document manager, så kan jeg hjelpe deg med jernbanerelaterte spørsmål!"""
        
        question_lower = question.lower()
        
        # Try to be helpful based on question content
        if any(word in question_lower for word in ['etcs', 'ertms']):
            return f"Jeg ser du spør om ETCS/ERTMS, men fant ikke spesifikk informasjon i de {doc_count} dokumentene. Legg gjerne til mer teknisk dokumentasjon om signalsystemer."
        
        elif any(word in question_lower for word in ['kostnad', 'pris', 'kost']):
            return f"Du spør om kostnader, men jeg fant ikke prisopplysninger i dokumentene. Har du budsjett- eller kostnadsdokumenter du kan legge til?"
        
        elif any(word in question_lower for word in ['rams', 'sikkerhet']):
            return f"RAMS og sikkerhet er viktige tema. Jeg har {doc_count} dokumenter, men fant ikke svar på ditt spesifikke spørsmål. Prøv å være mer spesifikk eller legg til flere tekniske dokumenter."
        
        else:
            return f"Jeg forstår spørsmålet ditt, men fant ikke svar i de {doc_count} dokumentene. Prøv å omformulere spørsmålet eller legg til mer relevant dokumentasjon."

    def load_knowledge_base(self):
        """Load all documents from document manager"""
        if not self._doc_manager:
            print("⚠️ Document manager not available")
            return
        
        try:
            all_docs = self._doc_manager.load_all_documents()
            
            if not all_docs:
                print("⚠️ No documents found")
                return
            
            print(f"📄 Loading {len(all_docs)} documents...")
            
            # Clear existing documents
            self.documents_text = []
            self.documents_metadata = []
            
            for doc in all_docs:
                try:
                    content = doc.get("content")
                    if not content:
                        continue

                    metadata = {
                        "type": doc.get("type", "unknown"),
                        "category": doc.get("category", "general"),
                        "title": doc.get("title", "Untitled"),
                        "tags": doc.get("tags", []),
                        "source": "manual",
                        "doc_id": doc.get("id", "unknown"),
                        "added_date": doc.get("created_at", datetime.now().isoformat())
                    }

                    self.add_document_to_ai(text=content, metadata=metadata)
                    
                except Exception as e:
                    print(f"⚠️ Error loading document {doc.get('title', 'Unknown')}: {e}")
                    continue
            
            print(f"✅ Loaded {len(self.documents_text)} documents into AI")
            
        except Exception as e:
            print(f"❌ Failed to load knowledge base: {e}")

    def reload_documents(self):
        """Reload all documents"""
        if not self.ensure_initialized():
            return
        
        try:
            # Clear collection
            self.client.delete_collection("railadvice")
            self.collection = self.client.create_collection("railadvice")
            
            # Clear local storage
            self.documents_text = []
            self.documents_metadata = []
            
            # Reload documents
            self.load_knowledge_base()
            
            print("🔄 Documents reloaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to reload documents: {e}")

    def add_document_to_ai(self, text, metadata):
        """Add document to AI (internal method)"""
        try:
            if not isinstance(text, str):
                text = str(text)
            
            if not text.strip():
                return
            
            # Only add to ChromaDB if initialized
            if self.ensure_initialized() and self.collection:
                embedding = self.embedder.encode([text])[0].tolist()
                
                # Add to local storage
                self.documents_text.append(text)
                self.documents_metadata.append(metadata)
                
                # Prepare metadata for ChromaDB
                chroma_metadata = metadata.copy()
                chroma_metadata['ai_added_date'] = datetime.now().isoformat()
                chroma_metadata['text_length'] = len(text)
                chroma_metadata['doc_index'] = len(self.documents_text) - 1
                
                doc_id = f"doc_{len(self.collection.get()['ids']) + 1}"
                
                fixed_metadata = fix_metadata(chroma_metadata)
                
                self.collection.add(
                    documents=[text],
                    metadatas=[fixed_metadata],
                    ids=[doc_id],
                    embeddings=[embedding]
                )
                
                # Update TF-IDF if available
                if self.tfidf and len(self.documents_text) > 1:
                    try:
                        self.tfidf.fit(self.documents_text)
                    except Exception as e:
                        print(f"⚠️ TF-IDF update failed: {e}")
            else:
                # Just add to local storage if ChromaDB not ready
                self.documents_text.append(text)
                self.documents_metadata.append(metadata)
                
        except Exception as e:
            print(f"⚠️ Failed to add document to AI: {e}")

    def extract_keywords_and_intent(self, text):
        """Enhanced keyword extraction and intent recognition"""
        text_lower = text.lower()
        
        # Extract entities if NLP is available
        entities = []
        if self.ensure_initialized() and self.nlp:
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
        
        # Extract specific terms from document metadata
        specific_terms = []
        for doc_meta in self.documents_metadata:
            title_words = doc_meta.get('title', '').lower().split()
            for word in title_words:
                if len(word) > 3 and word in text_lower:
                    specific_terms.append(word)
            
            tags = doc_meta.get('tags', [])
            if isinstance(tags, str):
                tags = tags.split(', ')
            for tag in tags:
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
        """Find best response using semantic search"""
        if not self.documents_text:
            return [], "No Documents", intent_analysis
        
        if not self.ensure_initialized():
            return [], "Not Initialized", intent_analysis

        try:
            query_embedding = self.embedder.encode([question])[0].tolist()
            
            # Perform semantic search
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                include=["documents", "metadatas", "distances"]
            )
            
            ranked_results = []
            if semantic_results['documents'] and semantic_results['documents'][0]:
                for i in range(len(semantic_results['documents'][0])):
                    doc_text = semantic_results['documents'][0][i]
                    metadata = semantic_results['metadatas'][0][i]
                    distance = semantic_results['distances'][0][i]
                    
                    score = 1 - distance
                    
                    # Bonus for title matches
                    title_lower = metadata.get('title', '').lower()
                    question_lower = question.lower()
                    
                    if any(word in title_lower for word in question_lower.split()):
                        score += 0.4
                    
                    # Bonus for category matches
                    question_categories = intent_analysis.get('categories', [])
                    doc_category = metadata.get('category', '')
                    if doc_category in question_categories:
                        score += 0.2
                    
                    ranked_results.append({'doc': doc_text, 'score': score})
            
            # Sort by combined score
            ranked_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Get top documents
            best_docs = [item['doc'] for item in ranked_results[:2]]
            
            # Determine confidence
            confidence = "Low"
            if ranked_results:
                top_score = ranked_results[0]['score']
                if top_score > 1.0:
                    confidence = "High"
                elif top_score > 0.7:
                    confidence = "Medium"
                else:
                    confidence = "Low"
            
            return best_docs, confidence, intent_analysis
            
        except Exception as e:
            print(f"⚠️ Error in find_best_response: {e}")
            return [], "Error", intent_analysis

    def query(self, question):
        """Main query function with enhanced response generation"""
        print(f"❓ Processing: {question}")
        
        # Classify input type
        input_type = self.classify_input_type(question)
        print(f"🎯 Input type: {input_type}")
        
        # Handle special cases that don't need heavy ML components
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
        
        # For other queries, try to initialize heavy components if needed
        if not self._initialized:
            if self.lazy_init:
                return {
                    "answer": "AI engine is still loading. Please try again in a moment.",
                    "sources": 0,
                    "confidence": "Loading",
                    "input_type": input_type,
                    "intent_categories": [],
                    "specific_terms": [],
                    "analysis": {},
                    "loading": True
                }
            else:
                try:
                    self.initialize_heavy_components()
                except Exception as e:
                    return {
                        "answer": f"AI engine initialization failed: {str(e)}. Please try again later.",
                        "sources": 0,
                        "confidence": "Error",
                        "input_type": input_type,
                        "intent_categories": [],
                        "specific_terms": [],
                        "analysis": {}
                    }
        
        # Check if we have documents
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
    def __init__(self, memory_file="conversation_memory.json", lazy_init=True):
        super().__init__(lazy_init=lazy_init)
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
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save memory: {e}")

    def classify_input_type(self, text):
        text_lower = text.lower().strip()
        for pattern in self.farewell_patterns:
            if re.search(pattern, text_lower):
                return "farewell"
        return super().classify_input_type(text)

    def generate_smart_response(self, question, docs, confidence, input_type):
        if input_type == "farewell":
            return "Takk for praten! Ta kontakt igjen når du trenger hjelp med jernbaneprosjekter."
        return super().generate_smart_response(question, docs, confidence, input_type)

    def query(self, question):
        result = super().query(question)
        
        # Save conversation history
        self.conversation_history.append({"user": question, "ai": result["answer"]})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        self.save_memory()
        
        return result


# Factory function for creating AI instances
def create_ai_engine(lazy=True, contextual=False):
    """Factory function to create AI engine instances"""
    if contextual:
        return ContextualRailAdviceAI(lazy_init=lazy)
    else:
        return RailAdviceAI(lazy_init=lazy)


# Test function
if __name__ == "__main__":
    print("Testing Optimized RailAdvice AI")
    
    # Test with lazy loading
    ai = RailAdviceAI(lazy_init=True)
    
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