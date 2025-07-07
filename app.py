from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import feedparser
import requests
from datetime import datetime, timedelta
# from googletrans import Translator  # Kikommentálva - AI-val fordítunk
import hashlib
import os
from dotenv import load_dotenv
import schedule
import threading
import time
from ai_processor import GovernmentEconomicAnalyzer
from database import init_database, is_database_available
from database_manager import db_manager
from flask import send_file
import tempfile
try:
    import pdfkit
    PDF_GENERATOR = 'pdfkit'
except ImportError:
    pdfkit = None
    PDF_GENERATOR = None
    
# WeasyPrint-et kikapcsoljuk production-ben
HTML = None
    
if not pdfkit:
    print("⚠️ PDF export nem elérhető production környezetben")

load_dotenv()

app = Flask(__name__)
CORS(app)

# Teszt mód a gyorsabb fejlesztéshez
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

# Globális változók a hírek tárolására
newsletter_data = {
    'articles': [],
    'executive_briefing': '',
    'last_update': None,
    'update_count': 0,
    'processing_status': 'idle'
}

# Database inicializálása
if init_database():
    print("✅ PostgreSQL adatbázis kész")
else:
    print("⚠️ PostgreSQL nem elérhető - memória módban fut")

# AI elemző inicializálása
ai_analyzer = GovernmentEconomicAnalyzer()

# Gazdasági RSS források (angol nyelvű)
ECONOMIC_SOURCES = [
    # PRÉMIUM FORRÁSOK
    {
        'name': 'Bloomberg Markets',
        'url': 'https://feeds.bloomberg.com/markets/news.rss',
        'category': 'Piacok'
    },
    {
        'name': 'Bloomberg Politics',
        'url': 'https://feeds.bloomberg.com/politics/news.rss',
        'category': 'Gazdaságpolitika'
    },
    {
        'name': 'Bloomberg Technology',
        'url': 'https://feeds.bloomberg.com/technology/news.rss',
        'category': 'Tech & Gazdaság'
    },
    {
        'name': 'Financial Times',
        'url': 'https://www.ft.com/rss/home',
        'category': 'Általános gazdaság'
    },
    {
        'name': 'The Economist - Finance',
        'url': 'https://www.economist.com/finance-and-economics/rss.xml',
        'category': 'Elemzések'
    },
    {
        'name': 'The Economist - Business',
        'url': 'https://www.economist.com/business/rss.xml',
        'category': 'Üzleti elemzések'
    },
    {
        'name': 'Reuters Business',
        'url': 'https://feeds.reuters.com/reuters/businessNews',
        'category': 'Üzleti hírek'
    },
    {
        'name': 'Wall Street Journal',
        'url': 'https://feeds.wsj.com/rss/RSSWorldNews.xml',
        'category': 'Pénzügyek'
    },
    {
        'name': 'MarketWatch',
        'url': 'https://feeds.content.dowjones.io/public/rss/mw_topstories',
        'category': 'Tőzsde'
    },
    {
        'name': 'CNBC',
        'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'category': 'Tőzsde'
    },
    {
        'name': 'Business Insider',
        'url': 'https://markets.businessinsider.com/rss/news',
        'category': 'Piacok & Üzlet'
    },
    {
        'name': 'BBC Business',
        'url': 'http://feeds.bbci.co.uk/news/business/rss.xml',
        'category': 'Globális gazdaság'
    },
    # ELEMZÉSEK & THINK TANK
    {
        'name': 'Investopedia - Vállalati',
        'url': 'https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline&categoryName=company-news',
        'category': 'Vállalati hírek'
    },
    {
        'name': 'Investopedia - Piacok',
        'url': 'https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline&categoryName=markets-news',
        'category': 'Piaci hírek'
    },
    {
        'name': 'Economic Policy Institute',
        'url': 'http://feeds.feedburner.com/epi',
        'category': 'Gazdaságpolitika'
    },
    {
        'name': 'Federal Reserve FRED',
        'url': 'https://fredblog.stlouisfed.org/feed/',
        'category': 'Fed elemzések'
    },
    {
        'name': 'Congressional Budget Office',
        'url': 'https://www.cbo.gov/publications/all/rss.xml',
        'category': 'Költségvetés'
    },
    # BEFOLYÁSOS BLOGOK
    {
        'name': 'Calculated Risk',
        'url': 'http://feeds.feedburner.com/calculatedrisk',
        'category': 'Makrogazdaság'
    },
    {
        'name': 'Marginal Revolution',
        'url': 'http://feeds.feedburner.com/marginalrevolution',
        'category': 'Közgazdaságtan'
    },
    {
        'name': 'Financial Samurai',
        'url': 'https://financialsamurai.com/feed/',
        'category': 'Pénzügyi tanácsok'
    },
    {
        'name': 'Zero Hedge',
        'url': 'http://feeds.feedburner.com/zerohedge/feed',
        'category': 'Alternatív elemzés'
    }
]

# translator = Translator()  # Kikommentálva - AI-val fordítunk

def generate_article_id(title, source):
    """Egyedi azonosító generálása"""
    content = f"{title}-{source}".encode('utf-8')
    return hashlib.md5(content).hexdigest()[:12]

def translate_text(text, max_retries=3):
    """Szöveg fordítása angol->magyar AI-val"""
    if not text:
        return text
    
    # Használjuk a Gemini API-t a fordításhoz
    try:
        if ai_analyzer.gemini_model:
            prompt = f"Translate to Hungarian (output ONLY the Hungarian translation, no explanations): {text}"
            response = ai_analyzer.gemini_model.generate_content(prompt)
            # Clean up response - remove any THOUGHT sections or extra text
            result = response.text.strip()
            if "THOUGHT:" in result:
                # Extract only the translation part
                lines = result.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('THOUGHT:') and not line.startswith('*'):
                        return line.strip()
            return result
        else:
            # Ha nincs Gemini API, adjuk vissza az angol szöveget
            return text
    except Exception as e:
        print(f"Fordítási hiba: {e}")
        return text

def fetch_and_process_news():
    """Hírek lekérése és feldolgozása kormányzati elemzéssel"""
    # Ellenorizzük, hogy nem fut-e már
    if newsletter_data.get('processing_status') == 'processing':
        print("⚠️ Feldolgozás már folyamatban...")
        return
    
    newsletter_data['processing_status'] = 'processing'
    print(f"\n{'='*60}")
    print(f"🏛️ KORMÁNYZATI GAZDASÁGI HÍRLEVÉL FRISSÍTÉSE")
    print(f"Időpont: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_articles = []
    
    # RSS források feldolgozása
    for source in ECONOMIC_SOURCES:
        try:
            print(f"📡 Lekérés: {source['name']}")
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries[:3]:  # Max 3 cikk forrásonként a minőség miatt
                # Alapadatok kinyerése
                title = entry.get('title', 'Nincs cím')
                description = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')
                
                # Publikálási idő
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()
                
                # Csak az elmúlt 48 óra hírei (kormányzati elemzéshez bővebb időablak)
                if datetime.now() - pub_date > timedelta(days=2):
                    continue
                
                # Egyelőre nem fordítunk - túl lassú a betöltéshez
                translated_title = title  # translate_text(title)
                translated_description = description  # translate_text(description)
                
                article = {
                    'id': generate_article_id(title, source['name']),
                    'original_title': title,
                    'title': translated_title,
                    'original_description': description,
                    'description': translated_description,
                    'source': source['name'],
                    'category': source['category'],
                    'link': link,
                    'pub_date': pub_date.isoformat(),
                    'timestamp': datetime.now().isoformat()
                }
                
                all_articles.append(article)
                
        except Exception as e:
            print(f"❌ Hiba {source['name']} feldolgozásakor: {e}")
            continue
    
    print(f"\n📊 Összesen {len(all_articles)} cikk összegyűjtve")
    
    # AI elemzés csak ha vannak cikkek
    if all_articles:
        print(f"\n🤖 Kormányzati AI elemzés indítása...")
        processed_articles, executive_briefing = ai_analyzer.process_articles_for_government(all_articles)
        
        if not is_database_available():
            # Fallback: memória mód
            formatted_articles = [
                ai_analyzer.format_article_for_display(article)
                for article in processed_articles[:20]
            ]
            newsletter_data['articles'] = formatted_articles
            newsletter_data['executive_briefing'] = executive_briefing or "⚠️ Vezetői összefoglaló nem elérhető"
    else:
        if not is_database_available():
            newsletter_data['articles'] = []
            newsletter_data['executive_briefing'] = "Nincs feldolgozható cikk."
    
    newsletter_data['last_update'] = datetime.now().isoformat()
    newsletter_data['update_count'] += 1
    newsletter_data['processing_status'] = 'completed'
    
    print(f"\n✅ Frissítés kész! Feldolgozott cikkek: {len(newsletter_data['articles'])}")
    print(f"{'='*60}\n")

def run_scheduler():
    """Ütemező futtatása háttérszálon"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Ütemezett feladatok beállítása - KÉT KÜLÖN CIKLUS
def fetch_rss_only():
    """Csak RSS hírek lekérése elemzés nélkül (30 percenként)"""
    print(f"\n📰 RSS hírek frissítése: {datetime.now().strftime('%H:%M:%S')}")
    # Itt lehetne RSS cache frissítés, de most még nincs külön implementálva

def fetch_and_analyze():
    """Teljes elemzés új cikkekkel (2 óránként)"""
    fetch_and_process_news()

# RSS frissítés: 30 percenként
schedule.every(30).minutes.do(fetch_rss_only)

# AI elemzés: 2 óránként  
schedule.every(2).hours.do(fetch_and_analyze)

# Első futtatás háttérszálban 2 másodperc múlva
def delayed_first_run():
    """Késleltetett első futtatás - csak ha nincs friss adat"""
    time.sleep(2)
    try:
        test_mode_text = '(TESZT MÓD)' if TEST_MODE else ''
    except NameError:
        test_mode_text = ''
    
    # Ellenőrizzük van-e már friss adat az adatbázisban
    if is_database_available():
        try:
            articles = db_manager.get_latest_articles(5)
            if articles:
                print(f"\n💾 {len(articles)} cikk található az adatbázisban - első feldolgozás kihagyása")
                return
        except Exception as e:
            print(f"\n⚠️ Adatbázis ellenőrzési hiba: {e}")
    
    print(f"\n🚀 Első hírek betöltése indul... {test_mode_text}")
    fetch_and_process_news()

# Első futtatás háttérszálban
first_run_thread = threading.Thread(target=delayed_first_run, daemon=True)
first_run_thread.start()

# Ütemező indítása háttérszálon
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    """Főoldal"""
    return render_template('index.html', data=newsletter_data)

@app.route('/api/articles')
def get_articles():
    """API végpont a cikkek lekéréséhez"""
    if is_database_available():
        # ADATBÁZISBÓL TOP 30-AT BETÖLTÜNK (fontosság szerint)
        articles = db_manager.get_latest_articles(30)
        briefing = db_manager.get_latest_executive_briefing()
        
        # FRISSÍTJÜK A NEWSLETTER_DATA-T IS
        newsletter_data['articles'] = articles
        newsletter_data['executive_briefing'] = briefing['content'] if briefing else "Nincs vezetői összefoglaló"
        newsletter_data['last_update'] = briefing['created_at'] if briefing else None
        
        return jsonify({
            'articles': articles,
            'executive_briefing': briefing['content'] if briefing else "Nincs vezetői összefoglaló",
            'last_update': briefing['created_at'] if briefing else None,
            'processing_status': newsletter_data.get('processing_status', 'idle')
        })
    else:
        # Fallback: memória mód
        return jsonify(newsletter_data)

@app.route('/api/refresh', methods=['POST'])
def refresh_articles():
    """Manuális frissítés"""
    if newsletter_data.get('processing_status') == 'processing':
        return jsonify({'success': False, 'message': 'Feldolgozás már folyamatban...'})
    
    # Úresetünk mindent a duplikáció elkerülésére
    newsletter_data['articles'] = []
    newsletter_data['executive_briefing'] = ''
    
    fetch_and_process_news()
    return jsonify({'success': True, 'message': 'Hírek frissítve'})

@app.route('/api/rss-sources')
def get_rss_sources():
    """RSS források és cikkeik VALÓS IDEJŰ lekérése"""
    sources_with_articles = []
    
    for source in ECONOMIC_SOURCES:
        try:
            # Valós időben lekérjük az RSS feed-et
            feed = feedparser.parse(source['url'])
            recent_articles = []
            
            for entry in feed.entries[:3]:  # Max 3 legfrissebb cikk
                title = entry.get('title', 'Nincs cím')
                link = entry.get('link', '')
                description = entry.get('summary', entry.get('description', ''))
                
                # Publikálási idő
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()
                
                recent_articles.append({
                    'title': title,
                    'link': link,
                    'pub_date': pub_date.isoformat(),
                    'description': description[:150] + '...' if description else ''
                })
            
            source_info = {
                'name': source['name'],
                'url': source['url'],
                'category': source['category'],
                'articles': recent_articles
            }
            sources_with_articles.append(source_info)
            
        except Exception as e:
            print(f"❌ RSS lekérési hiba {source['name']}: {e}")
            # Fallback üres cikkekkel
            source_info = {
                'name': source['name'],
                'url': source['url'], 
                'category': source['category'],
                'articles': []
            }
            sources_with_articles.append(source_info)
    
    return jsonify({'sources': sources_with_articles})

@app.route('/api/test-refresh', methods=['POST'])
def test_refresh():
    """Gyors teszt frissítés"""
    global TEST_MODE
    TEST_MODE = True
    
    if newsletter_data.get('processing_status') == 'processing':
        return jsonify({'success': False, 'message': 'Feldolgozás már folyamatban...'})
    
    # Úresetünk mindent
    newsletter_data['articles'] = []
    newsletter_data['executive_briefing'] = ''
    
    fetch_and_process_news()
    return jsonify({'success': True, 'message': 'Teszt frissítés elindítva (3 forrás, 3 cikk)'})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_database():
    """Régi cikkek takarítása"""
    if not is_database_available():
        return jsonify({'success': False, 'message': 'Adatbázis nem elérhető'})
    
    data = request.get_json() or {}
    days = int(data.get('days', 30))
    deleted = db_manager.cleanup_old_articles(days)
    return jsonify({'success': True, 'message': f'{deleted} régi cikk törölve'})

@app.route('/api/search')
def search_articles():
    """Keresés a cikkekben"""
    if not is_database_available():
        return jsonify({'success': False, 'message': 'Adatbázis nem elérhető'})
    
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'success': False, 'message': 'Minimum 2 karakter szükséges'})
    
    # Keresés az összes cikkben (nem csak a top 30-ban!)
    all_articles = db_manager.get_latest_articles(1000)
    results = []
    
    query_lower = query.lower()
    for article in all_articles:
        # Keresés címben, összefoglalóban, forrásban
        title = (article.get('title', '') or '').lower()
        summary = (article.get('executive_summary', '') or '').lower()
        source = (article.get('source', '') or '').lower()
        
        if (query_lower in title or 
            query_lower in summary or 
            query_lower in source):
            results.append(article)
    
    return jsonify({
        'success': True,
        'query': query,
        'results': results[:50],  # Max 50 találat
        'total': len(results)
    })

@app.route('/api/db-status')
def database_status():
    """Adatbázis állapot"""
    if is_database_available():
        article_count = len(db_manager.get_latest_articles(1000))
        briefing = db_manager.get_latest_executive_briefing()
        return jsonify({
            'database_available': True,
            'article_count': article_count,
            'last_briefing': briefing['created_at'] if briefing else None
        })
    else:
        return jsonify({'database_available': False})

@app.route('/api/export-pdf')
def export_pdf():
    """PDF export - Kormányzati jelentés"""
    if not is_database_available():
        return jsonify({'success': False, 'message': 'Adatbázis nem elérhető'})
    
    try:
        # Adatok lekérése
        articles = db_manager.get_latest_articles(30)
        briefing = db_manager.get_latest_executive_briefing()
        
        # HTML template generálása
        html_content = f"""
        <!DOCTYPE html>
        <html lang="hu">
        <head>
            <meta charset="UTF-8">
            <title>Kormányzati Külgazdasági Szemle</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; line-height: 1.4; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1a237e; padding-bottom: 20px; }}
                .header h1 {{ color: #1a237e; font-size: 28px; margin: 0; }}
                .header .date {{ color: #666; font-size: 14px; margin-top: 10px; }}
                .executive-summary {{ background: #f8f9fa; padding: 20px; margin-bottom: 30px; border-left: 4px solid #1a237e; }}
                .executive-summary h2 {{ color: #1a237e; font-size: 20px; margin-top: 0; }}
                .articles-section h2 {{ color: #1a237e; font-size: 18px; margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                .article {{ margin-bottom: 25px; padding: 15px; border: 1px solid #e0e0e0; page-break-inside: avoid; }}
                .article-title {{ font-size: 16px; font-weight: bold; color: #1a237e; margin-bottom: 8px; }}
                .article-meta {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
                .article-summary {{ font-size: 14px; margin-bottom: 10px; }}
                .analysis-section {{ margin-top: 15px; }}
                .analysis-section h4 {{ color: #444; font-size: 14px; margin-bottom: 8px; }}
                .analysis-list {{ font-size: 12px; margin-left: 15px; }}
                .importance-badge {{ background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
                .urgency-badge {{ background: #fff3e0; color: #e65100; padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏛️ Kormányzati Külgazdasági Szemle</h1>
                <div class="date">Generálva: {datetime.now().strftime('%Y. %m. %d. %H:%M')}</div>
            </div>
        """
        
        # Vezetői összefoglaló
        if briefing:
            html_content += f"""
            <div class="executive-summary">
                <h2>📋 Vezetői Összefoglaló</h2>
                {briefing['content']}
            </div>
            """
        
        # Részletes elemzések
        html_content += """
            <div class="articles-section">
                <h2>📊 Részletes Elemzések</h2>
        """
        
        for i, article in enumerate(articles, 1):
            analysis = article.get('full_analysis', {})
            html_content += f"""
                <div class="article">
                    <div class="article-title">{i}. {article.get('title', 'Nincs cím')}</div>
                    <div class="article-meta">
                        <span class="importance-badge">Fontosság: {article.get('importance_score', 'N/A')}/10</span>
                        <span class="urgency-badge">{article.get('urgency', 'N/A')}</span>
                        | Forrás: {article.get('source', 'N/A')} | {article.get('pub_date', 'N/A')[:10]}
                    </div>
                    <div class="article-summary">{article.get('executive_summary', 'Nincs összefoglaló')}</div>
            """
            
            # Makrogazdasági hatások
            if analysis.get('macro_impacts'):
                macro = analysis['macro_impacts']
                html_content += """
                    <div class="analysis-section">
                        <h4>🇭🇺 Magyarországi Makrogazdasági Hatások</h4>
                        <div class="analysis-list">
                """
                for key, value in macro.items():
                    if value and value != 'N/A':
                        # TELJES SZÖVEG, nem levágva!
                        html_content += f"<div style='margin-bottom: 8px;'><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>"
                html_content += "</div></div>"
            
            # Szektorális elemzés
            if analysis.get('sectoral_analysis'):
                sectoral = analysis['sectoral_analysis']
                html_content += """
                    <div class="analysis-section">
                        <h4>🏭 Szektorális Elemzés</h4>
                        <div class="analysis-list">
                """
                if sectoral.get('affected_sectors'):
                    html_content += f"<div><strong>Érintett szektorok:</strong> {', '.join(sectoral['affected_sectors'])}</div>"
                if sectoral.get('employment_impact'):
                    # TELJES SZÖVEG, nem levágva!
                    html_content += f"<div style='margin-bottom: 8px;'><strong>Munkaerőpiaci hatás:</strong> {sectoral['employment_impact']}</div>"
                html_content += "</div></div>"
            
            html_content += "</div>"
        
        html_content += """
            </div>
            <div class="footer">
                <p>Kormányzati Külgazdasági Szemle - Automatikusan generált jelentés</p>
                <p>🤖 Generated with Claude Code | Co-Authored-By: Claude</p>
            </div>
        </body>
        </html>
        """
        
        # PDF generálás
        filename = f"Kormanyzati_Szemle_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        # Temp fájl létrehozása
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Production-ben nincs PDF
            return jsonify({'success': False, 'message': 'PDF export nem elérhető production környezetben. Használd lokálisan!'})
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
    except Exception as e:
        print(f"❌ PDF export hiba: {{e}}")
        return jsonify({{'success': False, 'message': f'PDF generálási hiba: {{str(e)}}'}})

if __name__ == '__main__':
    print(f"\n🔧 Teszt mód: {'BE' if TEST_MODE else 'KI'}")
    print(f"💾 Adatbázis: {'PostgreSQL' if is_database_available() else 'Memória mód'}")
    print("\n🔄 API Endpoints:")
    print("  POST /api/refresh - Teljes frissítés")
    print("  POST /api/test-refresh - Gyors teszt frissítés (3 forrás, 3 cikk)")
    print("  POST /api/cleanup - Régi cikkek takarítása")
    print("  GET /api/search?q=keyword - Keresés cikkekben")
    print("  GET /api/export-pdf - PDF letöltés")
    print("  GET /api/db-status - Adatbázis állapot")
    print("\n🌍 Environment variables:")
    print("  TEST_MODE=true - Gyors teszt mód")
    print("  DATABASE_URL=postgresql://... - PostgreSQL kapcsolat\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)