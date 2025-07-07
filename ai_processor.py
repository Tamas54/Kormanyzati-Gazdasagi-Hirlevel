import os
import re
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime
import hashlib

# Robust AI imports with fallbacks
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Gemini import error: {e}")
    genai = None
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ OpenAI import error: {e}")
    OpenAI = None
    OPENAI_AVAILABLE = False

load_dotenv()

class GovernmentEconomicAnalyzer:
    """
    Kormányzati szintű gazdasági elemző rendszer
    - Részletes makrogazdasági elemzések
    - Geopolitikai hatásvizsgálatok
    - Szektorális következmények
    - Döntéshozatali javaslatok
    """
    
    def __init__(self):
        # Gemini 2.5 Flash inicializálása
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ Gemini 2.5 Flash inicializálva")
            else:
                self.gemini_model = None
                print("⚠️ GEMINI_API_KEY hiányzik!")
        else:
            self.gemini_model = None
            print("⚠️ google-generativeai package nem elérhető!")
        
        # OpenAI GPT-4o mini inicializálása
        if OPENAI_AVAILABLE:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.openai_client = OpenAI(api_key=openai_api_key)
                print("✅ OpenAI GPT-4o mini inicializálva")
            else:
                self.openai_client = None
                print("⚠️ OPENAI_API_KEY hiányzik!")
        else:
            self.openai_client = None
            print("⚠️ openai package nem elérhető!")
    
    def _get_full_article_content(self, article: Dict) -> str:
        """Teljes cikk tartalom összeállítása"""
        content = f"""
        CÍM: {article.get('title', 'N/A')}
        EREDETI CÍM: {article.get('original_title', 'N/A')}
        FORRÁS: {article.get('source', 'N/A')}
        KATEGÓRIA: {article.get('category', 'N/A')}
        PUBLIKÁLÁS: {article.get('pub_date', 'N/A')}
        
        LEÍRÁS:
        {article.get('description', 'N/A')}
        
        EREDETI LEÍRÁS:
        {article.get('original_description', 'N/A')}
        
        LINK: {article.get('link', 'N/A')}
        """
        return content.strip()
    
    def analyze_for_government(self, article: Dict) -> Optional[Dict]:
        """
        Kormányzati szintű részletes elemzés egy cikkről
        """
        if not self.gemini_model:
            return None
        
        full_content = self._get_full_article_content(article)
        
        prompt = f"""
        Készíts RÉSZLETES KORMÁNYZATI ELEMZÉST a következő gazdasági hírről.
        Te egy vezető közgazdasági elemző vagy, aki a magyar kormány számára készít jelentéseket.
        
        {full_content}
        
        KÖTELEZŐ ELEMZÉSI SZEMPONTOK:
        
        0. MAGYAR CÍM
           - Adj egy rövid, tömör magyar címet a hírnek (max 80 karakter)
           - A cím legyen informatív és szakszerű
        
        1. VEZETŐI ÖSSZEFOGLALÓ (3-5 mondat)
           - A hír lényege és azonnali relevanciája
           - Miért fontos ezt MOST tudni a döntéshozóknak
        
        2. MAKROGAZDASÁGI HATÁSOK
           - Közvetlen és közvetett hatások a magyar gazdaságra
           - Lehetséges költségvetési következmények
           - Inflációs és GDP hatások becslése
           - Devizapiaci kockázatok és lehetőségek
           - Időhorizont: rövid, közép és hosszú távú hatások
        
        3. SZEKTORÁLIS ELEMZÉS
           - Mely magyar gazdasági szektorokat érinti
           - Konkrét vállalati példák (ha releváns)
           - Munkaerőpiaci hatások
        
        4. GEOPOLITIKAI KONTEXTUS
           - EU-s vonatkozások
           - Regionális (V4, CEE) következmények
           - Globális gazdasági trendekbe illeszkedés
        
        5. KOCKÁZATOK ÉS LEHETŐSÉGEK
           - Főbb kockázati tényezők
           - Kihasználható lehetőségek
           - Időhorizont (rövid/közép/hosszú táv)
        
        6. SZAKPOLITIKAI MEGFONTOLÁSOK
           - Lehetséges válaszopciók elemzése
           - Szabályozási kihívások és lehetőségek
           - Stakeholder érintettség
           - Nemzetközi koordináció szükségessége
        
        7. MONITORING PONTOK
           - Mit kell figyelni a következő időszakban
           - Kulcs indikátorok és küszöbértékek
        
        8. FONTOSSÁGI BESOROLÁS
           - Skála: 1-10 (10 = kritikus, azonnali intézkedést igényel)
           - Sürgősség: azonnali / 24 órán belül / 1 héten belül / monitoring
        
        Válaszolj JSON formátumban:
        {{
            "hungarian_title": "magyar cím",
            "executive_summary": "vezetői összefoglaló",
            "importance_score": <1-10>,
            "urgency": "azonnali/24h/1hét/monitoring",
            "macro_impacts": {{
                "gdp_effect": "hatás leírása",
                "inflation_effect": "hatás leírása",
                "budget_effect": "hatás leírása",
                "currency_effect": "HUF árfolyamra gyakorolt hatás"
            }},
            "sectoral_analysis": {{
                "affected_sectors": ["szektor1", "szektor2"],
                "company_examples": ["cég1", "cég2"],
                "employment_impact": "munkaerőpiaci hatás"
            }},
            "geopolitical_context": {{
                "eu_relevance": "EU vonatkozások",
                "regional_impact": "regionális hatások",
                "global_trends": "globális trendek"
            }},
            "risks_opportunities": {{
                "main_risks": ["kockázat1", "kockázat2"],
                "opportunities": ["lehetőség1", "lehetőség2"],
                "time_horizon": "rövid/közép/hosszú táv"
            }},
            "policy_considerations": [
                "megfontolás1",
                "megfontolás2"
            ],
            "monitoring_points": [
                "figyelendő1",
                "figyelendő2"
            ],
            "keywords_hu": ["kulcsszó1", "kulcsszó2", "kulcsszó3"]
        }}
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            # Improved JSON extraction - remove THOUGHT sections and find only clean JSON
            response_text = response.text
            
            # Remove THOUGHT sections that break JSON
            if "THOUGHT:" in response_text:
                response_text = re.sub(r'THOUGHT:.*?(?=\{)', '', response_text, flags=re.DOTALL)
            
            # Find COMPLETE JSON block - not just first level!
            json_start = response_text.find('{')
            if json_start != -1:
                # Count braces to find complete JSON
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_text[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                json_text = response_text[json_start:json_end]
                
                # Clean up common JSON issues
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
                json_text = re.sub(r'[\n\r\t]', ' ', json_text)  # Remove newlines
                
                try:
                    analysis = json.loads(json_text)
                    print(f"✅ TELJES JSON elemzés sikeresen feldolgozva ({len(analysis)} mező)")
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing hiba: {e}")
                    print(f"JSON részlet: {json_text[:200]}...")
                    return None
            else:
                print(f"❌ Nem található JSON válasz a Gemini kimenetében")
                return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing hiba: {e}")
            print(f"Részlet: {response.text[:500]}...")
            
            # ULTIMATE FALLBACK: Extract just the executive summary
            try:
                exec_match = re.search(r'"executive_summary":\s*"([^"]*)', response_text)
                if exec_match:
                    summary = exec_match.group(1)
                    print(f"✅ Fallback: Extracted executive summary")
                    return {
                        "hungarian_title": "Gazdasági hír",
                        "executive_summary": summary,
                        "importance_score": 5,
                        "urgency": "monitoring",
                        "macro_impacts": {"gdp_effect": "N/A", "inflation_effect": "N/A", "budget_effect": "N/A", "currency_effect": "N/A"},
                        "sectoral_analysis": {"affected_sectors": [], "company_examples": [], "employment_impact": "N/A"},
                        "risks_opportunities": {"main_risks": [], "opportunities": [], "time_horizon": "N/A"},
                        "policy_considerations": [],
                        "monitoring_points": [],
                        "keywords_hu": []
                    }
            except:
                pass
            return None
        except Exception as e:
            print(f"❌ Kormányzati elemzési hiba: {e}")
            return None
    
    def generate_executive_briefing(self, articles: List[Dict]) -> Optional[str]:
        """
        Vezetői sajtószemle készítése GPT-4o mini-vel
        """
        if not self.openai_client or not articles:
            return None
        
        # Top 10 legfontosabb hír
        top_articles = sorted(
            [a for a in articles if a.get('ai_analysis')],
            key=lambda x: x.get('ai_analysis', {}).get('importance_score', 0),
            reverse=True
        )[:10]
        
        # Részletesebb cikk információk összegyűjtése
        detailed_articles = []
        for i, a in enumerate(top_articles):
            analysis = a.get('ai_analysis', {})
            original_desc = a.get('original_description', '')[:300] + '...' if a.get('original_description') else ''
            
            article_info = f"""
            [{i+1}] <strong>{a.get('title')}</strong> (Fontosság: {analysis.get('importance_score', 'N/A')}/10, Sürgősség: {analysis.get('urgency', 'N/A')})
            Forrás: {a.get('source', 'N/A')} | Kategória: {a.get('category', 'N/A')}
            Eredeti tartalom: {original_desc}
            Magyar összefoglaló: {analysis.get('executive_summary', 'N/A')}
            
            Makrogazdasági hatások:
            - GDP: {analysis.get('macro_impacts', {}).get('gdp_effect', 'N/A')}
            - Infláció: {analysis.get('macro_impacts', {}).get('inflation_effect', 'N/A')}
            - HUF árfolyam: {analysis.get('macro_impacts', {}).get('currency_effect', 'N/A')}
            
            Szektorális hatások: {', '.join(analysis.get('sectoral_analysis', {}).get('affected_sectors', []))}
            Kockázatok: {', '.join(analysis.get('risks_opportunities', {}).get('main_risks', []))}
            """
            detailed_articles.append(article_info)
        
        articles_summary = "\n".join(detailed_articles)
        
        prompt = f"""
        Te egy vezető közgazdasági tanácsadó vagy, aki NAPI NEMZETKÖZI GAZDASÁGI SAJTÓSZEMLÉT készít a MAGYAR KORMÁNY számára.
        
        SZEREPED: Elemezd a nemzetközi gazdasági híreket és készíts kormányzati szintű jelentést, amely konkrét döntéstámogatást nyújt.
        
        Dátum: {datetime.now().strftime('%Y. %m. %d.')}
        
        NEMZETKÖZI GAZDASÁGI HÍREK (részletes elemzéssel):
        {articles_summary}
        
        KÉSZÍTS RÉSZLETES VEZETŐI SAJTÓSZEMLÉT HTML FORMÁTUMBAN:
        
        <h3>🏛️ KORMÁNYZATI GAZDASÁGI SAJTÓSZEMLE</h3>
        <p><strong>Dátum:</strong> {datetime.now().strftime('%Y. %m. %d.')}</p>
        
        <h4>🚨 AZONNALI FIGYELMET IGÉNYLŐ ÜGYEK</h4>
        <ul>
        [Itt sorold fel a kritikus ügyeket konkrét adatokkal, számokkal]
        </ul>
        
        <h4>📈 GLOBÁLIS GAZDASÁGI MOZGÁSOK ÉS TRENDEK</h4>
        <ul>
        [Részletesen elemezd a főbb trendeket, számadatokkal]
        </ul>
        
        <h4>🇭🇺 MAGYAR GAZDASÁGRA GYAKOROLT HATÁSOK</h4>
        <ul>
        [Konkrét szektorok, vállalatok, munkahelyek, költségvetési hatások]
        </ul>
        
        <h4>🌍 NEMZETKÖZI GAZDASÁGI KÖRNYEZET</h4>
        <ul>
        [EU, USA, Kína, energiapiacok, devizaárfolyamok stb.]
        </ul>
        
        <h4>🔍 MEGFONTOLÁSRA JAVASOLT TERÜLETEK</h4>
        <ol>
        [Elemzési szempontok, figyelendő területek, lehetséges irányok]
        </ol>
        
        <h4>📊 FIGYELENDŐ INDIKÁTOROK</h4>
        <ul>
        [Piaci mutatók, gazdasági adatok, tőzsdei mozgások - a hírekből]
        </ul>
        
        KÖVETELMÉNYEK:
        - CSAK A FENTI HÍREKBŐL DOLGOZZ! Ne találj ki új információkat!
        - Ha nincs konkrét adat egy hírben, ne találj ki számokat
        - Használd a hírekből származó információkat és elemzéseket
        - NE találj ki határidőket, minisztériumokat vagy konkrét intézkedéseket
        - Ehelyett: javasolj irányokat, megfontolásokat, figyelendő területeket
        - HTML formázást használj (h3, h4, ul, ol, strong, em)
        - Legalább 800-1000 szó legyen
        - Elemzői, NEM döntéshozói szemlélet
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Te egy vezető közgazdasági elemző vagy, aki a magyar kormány számára készít napi gazdasági jelentéseket."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Vezetői briefing generálási hiba: {e}")
            if "invalid_api_key" in str(e) or "401" in str(e):
                return "⚠️ HIBA: Érvénytelen OpenAI API kulcs. A vezetői összefoglaló generálásához frissíteni kell az OPENAI_API_KEY környezeti változót."
            return f"⚠️ HIBA a vezetői összefoglaló generálásában: {str(e)}"
    
    def process_articles_for_government(self, articles: List[Dict]) -> Tuple[List[Dict], str]:
        """
        Teljes kormányzati feldolgozás - DATABASE VERZIÓ
        """
        print(f"\n🏛️ Kormányzati elemzés indítása {len(articles)} cikkre...")
        
        processed_articles = []
        
        # Import database manager
        from database_manager import db_manager
        
        # Start processing status
        db_manager.start_processing()
        
        # Import test mode safely
        try:
            from app import TEST_MODE
            # MINDEN új cikket elemzünk, nem limit!
            max_articles_to_analyze = 3 if TEST_MODE else len(articles)
        except ImportError:
            max_articles_to_analyze = len(articles)
        
        # EGYSZER betöltjük az összes meglévő cikket (GYORSABB!)
        existing_articles = db_manager.get_latest_articles(1000)
        existing_analyses = {article.get('id'): article.get('full_analysis') for article in existing_articles if article.get('full_analysis')}
        print(f"📊 {len(existing_analyses)} meglévő elemzés az adatbázisban")
        
        # Minden cikk részletes elemzése - CSAK HA NINCS MÉG ELEMZÉS
        for i, article in enumerate(articles[:max_articles_to_analyze]):
            article_id = article.get('id')
            existing_analysis = existing_analyses.get(article_id)
            
            if existing_analysis:
                print(f"Meglévő elemzés: {i+1}/{min(max_articles_to_analyze, len(articles))} - {article.get('source', 'N/A')} (KIHAGYVA)")
                # Használjuk a meglévő elemzést
                article['ai_analysis'] = existing_analysis
                article['importance_score'] = existing_analysis.get('importance_score', 5)
                article['urgency'] = existing_analysis.get('urgency', 'monitoring')
            else:
                print(f"Új elemzés: {i+1}/{min(max_articles_to_analyze, len(articles))} - {article.get('source', 'N/A')}")
                
                analysis = self.analyze_for_government(article)
                if analysis:
                    article['ai_analysis'] = analysis
                    article['importance_score'] = analysis.get('importance_score', 5)
                    article['urgency'] = analysis.get('urgency', 'monitoring')
                else:
                    article['importance_score'] = 5
                    article['urgency'] = 'monitoring'
                
                # DATABASE SAVE - Csak új elemzéseket mentjük
                db_manager.save_article(article, analysis)
            
            processed_articles.append(article)
            
            try:
                from app import TEST_MODE
                update_frequency = 1 if TEST_MODE else 3
            except ImportError:
                update_frequency = 3
            if i % update_frequency == 0:
                print(f"💾 {i+1} cikk mentve az adatbázisba")
                
                # STREAMING: MINDIG frissítjük a newsletter_data-t
                from app import newsletter_data
                newsletter_data['articles'] = [
                    self.format_article_for_display(a) 
                    for a in sorted(processed_articles, 
                                  key=lambda x: x.get('importance_score', 5), 
                                  reverse=True)[:10]
                ]
        
        # Rendezés fontosság szerint
        processed_articles.sort(
            key=lambda x: (
                x.get('importance_score', 5),
                1 if x.get('urgency') == 'azonnali' else 2 if x.get('urgency') == '24h' else 3
            ),
            reverse=True
        )
        
        # Vezetői összefoglaló generálása CSAK A FELDOLGOZOTT CIKKEKBŐL
        executive_briefing = self.generate_executive_briefing(processed_articles)
        
        # Save executive briefing to database
        if executive_briefing:
            db_manager.save_executive_briefing(executive_briefing, len(processed_articles))
        
        # Mark processing as completed
        db_manager.complete_processing(len(processed_articles))
        
        # VÉGSŐ FRISSÍTÉS: newsletter_data betöltése az adatbázisból (TOP 30)
        from app import newsletter_data
        if db_manager.available:
            db_articles = db_manager.get_latest_articles(30)
            db_briefing = db_manager.get_latest_executive_briefing()
            newsletter_data['articles'] = db_articles
            newsletter_data['executive_briefing'] = db_briefing['content'] if db_briefing else "Nincs vezetői összefoglaló"
        
        print(f"✅ Kormányzati elemzés kész! ({len(processed_articles)} cikk feldolgozva)")
        return processed_articles, executive_briefing
    
    def format_article_for_display(self, article: Dict) -> Dict:
        """
        Cikk formázása megjelenítéshez
        """
        analysis = article.get('ai_analysis', {})
        
        # Magyar cím használata ha van AI elemzés
        hungarian_title = analysis.get('hungarian_title') or article.get('title')
        
        return {
            'id': article.get('id'),
            'title': hungarian_title,  # Magyar cím
            'original_title': article.get('original_title'),  # Angol cím
            'source': article.get('source'),
            'category': article.get('category'),
            'pub_date': article.get('pub_date'),
            'link': article.get('link'),
            'importance_score': analysis.get('importance_score', 5),
            'urgency': analysis.get('urgency', 'monitoring'),
            'executive_summary': analysis.get('executive_summary', ''),
            'full_analysis': analysis,
            'description': article.get('description'),
            'original_description': article.get('original_description')
        }