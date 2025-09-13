import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

class DataProcessor:
    def __init__(self, data_dir="./data"):
        self.data_dir = Path(data_dir)
        self.projects_dir = self.data_dir / "projects"
        self.regulations_dir = self.data_dir / "regulations"
        self.company_dir = self.data_dir / "company"
        
        # Create directories
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.regulations_dir, exist_ok=True)
        os.makedirs(self.company_dir, exist_ok=True)
    
    def process_complete_railadvice_profile(self):
        """Complete RailAdvice company profile and knowledge"""
        
        company_profile = {
            "basic_info": {
                "name": "RailAdvice AS",
                "founded": "2018",
                "location": "Oslo, Norge",
                "website": "www.railadvice.no",
                "industry": "Jernbanekonsulenter",
                "employees": "10-20 ansatte",
                "languages": ["Norsk", "Engelsk", "Svensk", "Dansk"]
            },
            
            "core_competencies": [
                "RAMS (Reliability, Availability, Maintainability, Safety) analyse",
                "ETCS (European Train Control System) implementering",
                "TSI (Technical Specifications for Interoperability) samsvar",
                "Jernbaneinfrastruktur design og optimalisering",
                "Sikkerhetsanalyse (HAZOP, FMEA, HAZID)",
                "Prosjektledelse for jernbaneprosjekter",
                "Due diligence og teknisk rådgivning",
                "Regelverk og godkjenningsprosesser",
                "Rolling stock evaluering og optimalisering",
                "Depot design og drift"
            ],
            
            "certifications": [
                "CENELEC sertifiseringer",
                "EU TSI ekspertise",
                "ETCS Level 1 og 2 kompetanse",
                "RAMS analysemetodikk",
                "Norsk jernbaneregelverk",
                "Internasjonal jernbanestandard"
            ],
            
            "key_personnel": {
                "Lars Mortvedt": {
                    "role": "Senior konsulent / Prosjektleder",
                    "expertise": ["RAMS", "LCC", "Rolling stock", "Prosjektledelse"],
                    "experience": "15+ år jernbaneerfaring",
                    "active_since": "Mai 2019",
                    "current_projects": ["Flytoget Type 78 RAM/LCC ansvar", "Bane NOR RAMS signalprosjekter"]
                }
            },
            
            "service_areas": {
                "RAMS_services": {
                    "description": "Komplett RAMS analyse og dokumentasjon",
                    "deliverables": ["RAMS plan", "Sikkerhetsdokumentasjon", "Risikoanalyse"],
                    "standards": ["EN 50126", "EN 50128", "EN 50129"],
                    "typical_cost": "500,000 - 2,000,000 NOK per prosjekt"
                },
                "ETCS_services": {
                    "description": "ETCS implementering og optimalisering",
                    "levels": ["ETCS Level 1", "ETCS Level 2", "ETCS Level 3"],
                    "deliverables": ["ETCS design", "Kostnad-nytte analyse", "Implementeringsplan"],
                    "typical_cost": "15-25 millioner NOK per 100km implementering"
                },
                "project_management": {
                    "description": "Prosjektledelse for jernbaneprosjekter",
                    "project_types": ["Infrastruktur", "Rolling stock", "Signaling", "Depot"],
                    "methodologies": ["PRINCE2", "PMI", "Jernbanespesifikk"],
                    "typical_duration": "6-36 måneder"
                }
            }
        }
        
        # Save company profile
        company_file = self.company_dir / "railadvice_profile.json"
        with open(company_file, 'w', encoding='utf-8') as f:
            json.dump(company_profile, f, indent=2, ensure_ascii=False)
        
        return company_profile
    
    def process_detailed_projects(self):
        """Detailed project information with costs, timelines, and outcomes"""
        
        projects = [
            {
                "title": "Fornebu Base Depot - Fullservice depotutvikling",
                "client": "Prosjekteringsgruppen Fornebubanen",
                "project_code": "FB-DEPOT-2023",
                "type": "depot_development",
                "status": "Pågående",
                "start_date": "2023-01-15",
                "estimated_completion": "2024-12-31",
                "description": "Komplett utvikling av depot med verksted, renhold og hensetting for Fornebubanen. Inkluderer teknisk design, RAMS analyse og prosjektledelse.",
                "scope": [
                    "Depotlayout og optimalisering",
                    "Verkstedutforming for vedlikehold",
                    "Renholdsanlegg design",
                    "Hensettingskapasitet beregning",
                    "RAMS dokumentasjon for depot"
                ],
                "technologies": ["depot", "workshop", "maintenance", "cleaning_systems"],
                "deliverables": ["Tekniske tegninger", "RAMS rapport", "Kostnadsanalyse"],
                "budget": "Konfidensielt - kontakt for estimat",
                "year": 2023,
                "outcome": "Pågående - foreløpige resultater positive"
            },
            
            {
                "title": "Flytoget Type 78 - RAMS og LCC optimalisering",
                "client": "Flytoget AS",
                "project_code": "FLY-T78-2019",
                "type": "rolling_stock",
                "status": "Pågående (langtidskontrakt)",
                "start_date": "2019-05-01",
                "description": "Teknisk bistand for nye flytogsett Type 78. Lars Mortvedt har RAMS/LCC ansvar og deltar i designoptimalisering.",
                "scope": [
                    "RAMS analyse for Type 78",
                    "Life Cycle Cost (LCC) beregninger",
                    "Vedlikeholdsstrategi utvikling",
                    "Pålitelighetsvurderinger",
                    "Teknisk support til leverandør"
                ],
                "technologies": ["RAM", "LCC", "rolling_stock", "reliability_analysis"],
                "consultant": "Lars Mortvedt",
                "key_metrics": {
                    "target_availability": "98.5%",
                    "mtbf_target": "50,000 km",
                    "lifecycle_years": "30 år"
                },
                "estimated_value": "450 millioner NOK (totalt Type 78 program)",
                "railadvice_fee": "Konfidensielt - flerårig rammeavtale",
                "year": 2019,
                "outcome": "Suksess - forbedret pålitelighet og reduserte LCC-kostnader"
            },
            
            {
                "title": "SJ Norge Materiellavdeling - Kontraktsansvar Trafikkpakke 2",
                "client": "SJ Norge AS",
                "project_code": "SJ-TP2-2020",
                "type": "contract_management",
                "status": "Avsluttet",
                "start_date": "2020-03-01",
                "end_date": "2021-08-31",
                "description": "Kontraktsansvarlig for trafikkpakke 2 omfattende Dovrebanen og dieselstrekninger nord. Teknisk ledelse av materiell og drift.",
                "scope": [
                    "Materiellstrategi for Dovrebanen",
                    "Dieseltog optimalisering",
                    "Vedlikeholdsplanlegging",
                    "Kontraktsoppfølging",
                    "Teknisk rådgivning til drift"
                ],
                "routes": ["Dovrebanen", "Nordlandsbanen", "Meråkerbanen"],
                "technologies": ["contract", "diesel", "operations", "maintenance_planning"],
                "key_results": [
                    "15% forbedring i punktlighet",
                    "12% reduksjon i vedlikeholdskostnader",
                    "Forbedret materiellytelse"
                ],
                "contract_value": "Konfidensielt",
                "year": 2020,
                "outcome": "Suksess - kontrakt levert i henhold til plan"
            },
            
            {
                "title": "Bybanen Utvikling - Sikkerhetssjef (Rammeavtale)",
                "client": "Bybanen Utvikling AS",
                "project_code": "BY-SIKK-2023",
                "type": "safety_management",
                "status": "Aktiv rammeavtale",
                "start_date": "2023-06-01",
                "description": "Rammeavtale som sikkerhetssjef for Bybanen Utvikling. Ansvar for sikkerhetsstyring og RAMS i bybaneutvikling.",
                "scope": [
                    "Sikkerhetsledelse og -styring",
                    "HAZOP og HAZID gjennomføring",
                    "Risikovurdering bybaneprosjekter",
                    "Safety case utarbeidelse",
                    "Koordinering med myndigheter"
                ],
                "technologies": ["safety", "light_rail", "management", "hazop", "risk_assessment"],
                "deliverables": ["Sikkerhetspolitikk", "RAMS dokumentasjon", "Safety cases"],
                "framework_value": "Rammeavtale - timepris basis",
                "year": 2023,
                "outcome": "Pågående - god fremdrift i sikkerhetsstyring"
            },
            
            {
                "title": "Bane NOR RAMS Signal - Multippel signalprosjekter",
                "client": "Bane NOR SF",
                "project_code": "BN-RAMS-SIG-2024",
                "type": "RAMS_analysis",
                "status": "Pågående",
                "start_date": "2024-01-01",
                "description": "RAMS-rådgiving i flere signalprosjekter for Bane NOR. Omfatter både nye installasjoner og oppgraderinger.",
                "scope": [
                    "RAMS analyse signalsystemer",
                    "FMEA for kritiske komponenter",
                    "Sikkerhetsdokumentasjon",
                    "CSM-RA samsvarsvurdering",
                    "Teknisk support under installasjon"
                ],
                "signal_types": ["ETCS Level 2", "ATC", "Conventional signaling"],
                "technologies": ["RAMS", "signaling", "safety", "ETCS", "FMEA"],
                "geographical_scope": ["Østlandet", "Sørlandet", "Vestlandet"],
                "estimated_value": "2-5 millioner NOK (total portefølje)",
                "year": 2024,
                "outcome": "Pågående - flere milepæler levert i tide"
            }
        ]
        
        # Save detailed projects
        projects_file = self.projects_dir / "detailed_projects.json"
        with open(projects_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processed {len(projects)} detailed projects")
        return projects
    
    def process_technical_knowledge(self):
        """Detailed technical knowledge and regulations"""
        
        technical_knowledge = [
            {
                "title": "ETCS Level 2 - Implementeringskrav og kostnader",
                "category": "signaling",
                "code": "ETCS-L2-IMPL",
                "content": """ETCS Level 2 krever Radio Block Centre (RBC), GSM-R kommunikasjon, 
                onboard-enheter med SIL-4 sertifisering, og baliser minimum hver 1000m. 
                
                Typiske implementeringskostnader:
                - RBC: 25-40 millioner NOK per senter
                - Onboard-enheter: 2-4 millioner NOK per tog
                - Baliser: 50,000-100,000 NOK per balise
                - GSM-R infrastruktur: 10-20 millioner NOK per 100km
                
                Total kostnad: 15-25 millioner NOK per 100km strekning.
                
                Implementeringstid: 24-36 måneder for kompleks strekning.""",
                "applications": ["Hovedbaner", "Høyhastighet", "Tung godstrafikk"],
                "benefits": ["Økt kapasitet", "Forbedret sikkerhet", "Reduserte driftskostnader"],
                "challenges": ["Høye investeringskostnader", "Kompleks integrasjon", "GSM-R avhengighet"]
            },
            
            {
                "title": "RAMS metodikk - EN 50126 implementering",
                "category": "safety",
                "code": "RAMS-EN50126",
                "content": """EN 50126 definerer RAMS-krav for jernbanesystemer:
                
                Reliability: MTBF > 50,000 timer for kritiske systemer
                Availability: 99.9% for persontransport, 99.5% for godstransport  
                Maintainability: MTTR < 4 timer for kritiske feil
                Safety: SIL-4 for kritiske sikkerhetsfunksjoner
                
                RAMS-prosess:
                1. RAMS-krav definisjon (3-6 måneder)
                2. HAZOP/HAZID analyse (2-4 måneder) 
                3. FMEA gjennomføring (4-6 måneder)
                4. Safety case utarbeidelse (6-12 måneder)
                5. Verifikasjon og validering (6-18 måneder)
                
                Typisk kostnad: 500,000 - 2,000,000 NOK per prosjekt.""",
                "methodologies": ["HAZOP", "HAZID", "FMEA", "FTA", "SSHA"],
                "deliverables": ["RAMS plan", "Safety case", "Hazard log", "FMEA rapport"],
                "certification": "Uavhengig Safety Assessor (ISA) påkrevd"
            },
            
            {
                "title": "TSI Infrastructure - Tekniske krav infrastruktur",
                "category": "infrastructure", 
                "code": "TSI-INF-2023",
                "content": """TSI Infrastructure definerer tekniske krav for jernbaneinfrastruktur:
                
                Sporvidde: 1435mm (normalspor) ±2mm toleranse
                Lastefri profil: Minimum GA struktur, GC for høyhastighetsbaner
                Minimum kurveradius: 150m for nye baner (300m anbefalt)
                Maksimal gradient: 35‰ (3.5%) for persontog, 25‰ for godstog
                
                Konstruksjonskrav:
                - Ballast: Minimum 30cm under sviller
                - Fundamentering: Frostfritt under -20°C
                - Drenering: Kapasitet for 100-års regn
                - Bæreevne: 250 kN aksellast (godstog)
                
                Byggetoleranse: ±10mm horisontal, ±5mm vertikal
                Vedlikeholdsintervall: 5-8 år sporstabilisering
                
                Kostnad ny bane: 150-300 millioner NOK per km (avhenger av terreng)""",
                "standards": ["EN 13848", "prEN 16432", "UIC 719"],
                "testing": ["Geometrimåling", "Ballast-tetthet", "Dreneringskapasitet"],
                "compliance": "EU-kommisjon godkjenning påkrevd"
            },
            
            {
                "title": "Rolling Stock LCC - Life Cycle Cost analyse", 
                "category": "rolling_stock",
                "code": "RS-LCC-METHOD",
                "content": """Life Cycle Cost analyse for rullende materiell:
                
                CAPEX (Anskaffelse): 40-60% av total LCC
                - Nye tog: 25-45 millioner NOK per enhet
                - Elektrisk motorvogn: 30-50 millioner NOK
                - Diesellokomotiv: 35-55 millioner NOK
                
                OPEX (Drift): 40-60% av total LCC over 30 år
                - Energi: 1,5-3,0 NOK per km
                - Vedlikehold: 2-4 NOK per km  
                - Personalkostnader: 150-250 NOK per driftstime
                - Forsikring: 0.5-1% av CAPEX årlig
                
                Optimalisering:
                - Energieffektivitet: 20-30% besparelse mulig
                - Prediktivt vedlikehold: 15-25% kostnadreduksjon
                - Komponentstandardisering: 10-20% lavere reservedelskostnad
                
                ROI-periode: 8-15 år for effektivitetstiltak""",
                "analysis_tools": ["LCC-kalkulatorer", "Risikosimulering", "Sensitivitetsanalyse"],
                "key_factors": ["Tilgjengelighet", "Pålitelighet", "Energiforbruk", "Vedlikeholdskostnad"]
            }
        ]
        
        # Save technical knowledge
        tech_file = self.regulations_dir / "technical_knowledge.json"
        with open(tech_file, 'w', encoding='utf-8') as f:
            json.dump(technical_knowledge, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processed {len(technical_knowledge)} technical knowledge articles")
        return technical_knowledge
    
    def process_market_insights(self):
        """Market insights and industry knowledge"""
        
        market_data = [
            {
                "title": "Norsk jernbanemarked - Status og trender 2024",
                "category": "market_analysis",
                "content": """Norsk jernbanemarked verdi: 25-30 milliarder NOK årlig
                
                Vekstområder:
                - ETCS modernisering: 8-12 milliarder NOK (2024-2030)
                - Bybaner: 15-20 milliarder NOK (2024-2035)
                - Elektrifisering: 5-8 milliarder NOK (2024-2030)
                - Høyhastighetsbane: 200-300 milliarder NOK (planlagt)
                
                Hovedaktører:
                - Bane NOR: Infrastrukturforvalter
                - Vygruppen: Største operatør
                - Go-Ahead: Sørlandsbanen
                - SJ Norge: Regionale ruter
                
                Konsulentmarked: 2-3 milliarder NOK årlig
                RailAdvice markedsandel: Estimert 1-2% (spesialisert nisje)""",
                "trends": ["Digitalisering", "Bærekraft", "Automatisering", "ETCS Level 3"],
                "opportunities": ["Smart vedlikehold", "Energioptimalisering", "Kapasitetsøkning"]
            },
            
            {
                "title": "ETCS markedet i Norden - Muligheter og utfordringer",
                "category": "technology_market",
                "content": """ETCS implementering Norden 2024-2035:
                
                Norge: 4,000 km hovedbaner (60% implementert)
                Sverige: 15,000 km (25% implementert) 
                Danmark: 2,800 km (80% implementert)
                Finland: 5,900 km (15% implementert)
                
                Markedsverdi ETCS Norden: 40-60 milliarder NOK
                
                RailAdvice posisjon:
                - ETCS Level 2 ekspertise
                - RAMS spesialisering
                - Nordisk språkkompetanse  
                - Kostnadseffektive løsninger
                
                Konkurranse: Større internasjonale konsulenter
                Fordeler: Lokal tilstedeværelse og særnorske forhold""",
                "competitors": ["Atkins", "COWI", "Ramboll", "WSP"],
                "differentiators": ["RAMS-ekspertise", "Kostnadseffektivitet", "Lokalkunnskap"]
            }
        ]
        
        # Save market insights
        market_file = self.company_dir / "market_insights.json" 
        with open(market_file, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processed {len(market_data)} market insight articles")
        return market_data
    
    def load_all_data(self):
        """Load all processed data for AI training"""
        all_data = {}
        
        # Load company profile
        all_data['company_profile'] = self.process_complete_railadvice_profile()
        
        # Load projects
        all_data['projects'] = self.process_detailed_projects()
        
        # Load technical knowledge
        all_data['technical_knowledge'] = self.process_technical_knowledge()
        
        # Load market insights
        all_data['market_insights'] = self.process_market_insights()
        
        print("📊 Complete RailAdvice knowledge base loaded!")
        print(f"   - Company profile: {len(all_data['company_profile'])} sections")
        print(f"   - Projects: {len(all_data['projects'])} detailed projects")
        print(f"   - Technical knowledge: {len(all_data['technical_knowledge'])} articles")
        print(f"   - Market insights: {len(all_data['market_insights'])} reports")
        
        return all_data

if __name__ == "__main__":
    processor = DataProcessor()
    all_data = processor.load_all_data()
    print("\n🎯  data processing complete!")