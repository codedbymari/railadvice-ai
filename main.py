from src.ai_engine import RailAdviceAI
from src.data_processor import DataProcessor
from src.document_manager import EnhancedFileDocumentManager
import json
import os

def setup_railadvice_ai():
    """Setup AI with complete RailAdvice knowledge using document_manager"""
    print("🚀 Setting up RailAdvice AI with complete knowledge base...")
    
    # Initialize document manager and data processor
    doc_manager = EnhancedFileDocumentManager()
    processor = DataProcessor()
    
    # Load all data
    all_data = processor.load_all_data()
    
    # Clear existing documents first
    existing_docs = doc_manager.list_documents()
    print(f"🗑️ Clearing {len(existing_docs)} existing documents...")
    for doc in existing_docs:
        doc_manager.remove_document(doc['id'])
    
    # Add company profile to document manager
    company_profile = all_data['company_profile']
    for section_name, section_data in company_profile.items():
        if isinstance(section_data, dict):
            text_content = f"RailAdvice {section_name}:\n"
            text_content += json.dumps(section_data, indent=2, ensure_ascii=False)
        else:
            text_content = f"RailAdvice {section_name}: {section_data}"
        
        doc_id = doc_manager.add_document(
            title=f"RailAdvice - {section_name}",
            content=text_content,
            doc_type="company_profile",
            category="company",
            tags=["railadvice", "company", section_name],
            metadata={"section": section_name, "source": "company_profile"}
        )
        print(f"✅ Added company section: {section_name} (ID: {doc_id})")
    
    # Add content documents from data/documents/content/
    content_dir = "data/documents/content"
    if os.path.exists(content_dir):
        print(f"📂 Loading content documents from {content_dir}...")
        for filename in os.listdir(content_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(content_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                    
                    # Extract title and content more flexibly
                    title = filename.replace('.json', '')
                    content = ""
                    
                    # Handle different JSON structures
                    if isinstance(content_data, dict):
                        # Try various keys for title
                        title = (content_data.get('title') or 
                                content_data.get('name') or 
                                content_data.get('document_title') or 
                                title)
                        
                        # Try various keys for content, or use entire JSON as string
                        content = (content_data.get('content') or 
                                  content_data.get('text') or
                                  content_data.get('body') or
                                  json.dumps(content_data, indent=2, ensure_ascii=False))
                                  
                    elif isinstance(content_data, list):
                        # If it's a list, process each item
                        for i, item in enumerate(content_data):
                            if isinstance(item, dict):
                                item_title = (item.get('title') or 
                                            item.get('name') or 
                                            f"{title} - Del {i+1}")
                                item_content = (item.get('content') or 
                                              item.get('text') or
                                              json.dumps(item, indent=2, ensure_ascii=False))
                                
                                doc_id = doc_manager.add_document(
                                    title=item_title,
                                    content=item_content,
                                    doc_type="content_guide",
                                    category="railadvice_guides",
                                    tags=["railadvice", "guide", "content"],
                                    metadata={"source_file": filename, "part": i+1}
                                )
                        continue  # Skip the main document creation below
                    else:
                        # If it's neither dict nor list, convert to string
                        content = str(content_data)
                    
                    # Add the main document
                    doc_id = doc_manager.add_document(
                        title=title,
                        content=content,
                        doc_type="content_guide",
                        category="railadvice_guides",
                        tags=["railadvice", "guide", "content"],
                        metadata={"source_file": filename}
                    )
                    
                    print(f"✅ Added content document: {title} (ID: {doc_id})")
                except Exception as e:
                    print(f"⚠️ Could not load {filename}: {e}")
                    continue
    else:
        print(f"⚠️ Content directory {content_dir} not found. Skipping content documents.")

    # Add detailed projects
    print("📋 Adding project documents...")
    for project in all_data['projects']:
        project_text = f"""PROSJEKT: {project['title']}
Kunde: {project['client']}
Type: {project['type']}
Status: {project['status']}
År: {project.get('year', 'N/A')}

Beskrivelse: {project['description']}

Omfang: {' | '.join(project.get('scope', []))}
Teknologier: {' | '.join(project['technologies'])}

Budsjett/Verdi: {project.get('estimated_value', project.get('budget', 'Konfidensielt'))}

Resultater: {project.get('outcome', 'Pågående')}

Nøkkeldata: {json.dumps(project.get('key_metrics', {}), ensure_ascii=False)}"""
        
        # Clean up tags - ensure all are strings
        project_tags = ["projekt", project['client'], project['type']]
        if project.get('year'):
            project_tags.append(str(project['year']))
        
        doc_id = doc_manager.add_document(
            title=project['title'],
            content=project_text,
            doc_type="project",
            category="projects",
            tags=project_tags,
            metadata={
                "client": project['client'],
                "year": project.get('year'),
                "project_type": project['type'],
                "status": project['status']
            }
        )
        print(f"✅ Added project: {project['title']} (ID: {doc_id})")
    
    # Add technical knowledge
    print("🔧 Adding technical knowledge documents...")
    for tech_item in all_data['technical_knowledge']:
        tech_text = f"""TEKNISK KUNNSKAP: {tech_item['title']}
Kategori: {tech_item['category']}
Kode: {tech_item['code']}

INNHOLD:
{tech_item['content']}

Anvendelser: {' | '.join(tech_item.get('applications', []))}
Fordeler: {' | '.join(tech_item.get('benefits', []))}
Utfordringer: {' | '.join(tech_item.get('challenges', []))}"""
        
        doc_id = doc_manager.add_document(
            title=tech_item['title'],
            content=tech_text,
            doc_type="technical_knowledge",
            category=tech_item['category'],
            tags=["teknisk", tech_item['category'], tech_item['code']],
            metadata={
                "category": tech_item['category'],
                "code": tech_item['code']
            }
        )
        print(f"✅ Added technical knowledge: {tech_item['title']} (ID: {doc_id})")
    
    # Add market insights
    print("📈 Adding market insight documents...")
    for market_item in all_data['market_insights']:
        market_text = f"""MARKEDSANALYSE: {market_item['title']}
Kategori: {market_item['category']}

ANALYSE:
{market_item['content']}

Trender: {' | '.join(market_item.get('trends', []))}
Muligheter: {' | '.join(market_item.get('opportunities', []))}"""
        
        doc_id = doc_manager.add_document(
            title=market_item['title'],
            content=market_text,
            doc_type="market_insight",
            category=market_item['category'],
            tags=["marked", "analyse", market_item['category']],
            metadata={
                "category": market_item['category']
            }
        )
        print(f"✅ Added market insight: {market_item['title']} (ID: {doc_id})")
    
    # Get final stats
    stats = doc_manager.get_stats()
    print(f"\n📊 Complete RailAdvice knowledge base loaded!")
    print(f"   - Total documents: {stats['total_documents']}")
    print(f"   - Document types: {list(stats['document_types'].keys())}")
    print(f"   - Categories: {list(stats['categories'].keys())}")
    
    # Now initialize AI with the loaded documents
    print("\n🤖 Initializing AI engine with loaded documents...")

    ai = RailAdviceAI()
    print("✅ RailAdvice AI ready with complete knowledge base!")
    
    return ai

def test_ai_with_loaded_data(ai):
    """Test the AI with some sample queries"""
    print("\n🧪 Testing AI with loaded knowledge...")
    print("=" * 60)
    
    test_queries = [
        "Hei",
        "Hva er ETCS?",
        "Fortell om Lars Mortvedt",
        "Hvilke prosjekter har RailAdvice gjort?",
        "Hva koster ETCS implementering?",
        "Flytoget Type 78"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Spørsmål: '{query}'")
        print("-" * 50)
        
        try:
            result = ai.query(query)
            answer = result['answer']
            
            # Truncate long answers for display
            if len(answer) > 200:
                display_answer = answer[:197] + "..."
            else:
                display_answer = answer
                
            print(f"🤖 Svar: {display_answer}")
            print(f"📊 Kilder: {result['sources']} | Confidence: {result['confidence']}")
            
            if result.get('intent_categories'):
                print(f"🔍 Intent: {', '.join(result['intent_categories'])}")
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")

def interactive_mode(ai):
    """Interactive chat mode"""
    print("\n💬 Interactive mode started! (type 'exit' to quit)")
    print("=" * 60)
    
    while True:
        try:
            question = input("\n🧑 Du: ").strip()
            
            if question.lower() in ['exit', 'quit', 'bye', 'avslutt']:
                print("👋 Ha det! Takk for at du brukte RailAdvice AI.")
                break
            
            if not question:
                continue
                
            result = ai.query(question)
            print(f"🤖 RailAdvice AI: {result['answer']}")
            
            # Show debug info if low confidence
            if result['confidence'] in ['Low', 'Error']:
                print(f"   (Confidence: {result['confidence']}, Sources: {result['sources']})")
                
        except KeyboardInterrupt:
            print("\n👋 Ha det! Takk for at du brukte RailAdvice AI.")
            break
        except Exception as e:
            print(f"❌ En feil oppstod: {e}")

def main():
    """Main function with menu options"""
    print("🚆 RAILADVICE AI SETUP")
    print("=" * 50)
    
    try:
        # Setup AI and load all data into document_manager
        ai = setup_railadvice_ai()
        
        # Ask user what they want to do
        print(f"\n" + "=" * 60)
        print("✅ Setup komplett!")
        print("\nHva vil du gjøre?")
        print("1. Teste AI med forhåndsdefinerte spørsmål")
        print("2. Starte interaktiv chat-modus")
        print("3. Avslutte (og starte API-serveren manuelt)")
        
        while True:
            choice = input("\nVelg (1/2/3): ").strip()
            
            if choice == '1':
                test_ai_with_loaded_data(ai)
                break
            elif choice == '2':
                interactive_mode(ai)
                break
            elif choice == '3':
                print("\nFor å starte API-serveren:")
                print("python -m src.api")
                print("\nDeretter gå til: http://localhost:8000")
                break
            else:
                print("Ugyldig valg. Velg 1, 2 eller 3.")
                
    except Exception as e:
        print(f"❌ En feil oppstod under oppsettet: {e}")
        print("\nSjekk at alle avhengigheter er installert og at datafilene eksisterer.")

if __name__ == "__main__":
    main()