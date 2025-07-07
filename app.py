from flask import Flask, render_template, jsonify
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

load_dotenv()

app = Flask(__name__)
CORS(app)

# Globális változók a hírek tárolására
newsletter_data = {
    'articles': [],
    'executive_briefing': '',
    'last_update': None,
    'update_count': 0,
    'processing_status': 'idle'
}

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
                
                # Fordítás
                translated_title = translate_text(title)
                translated_description = translate_text(description)
                
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
        
        # Formázott cikkek előkészítése
        formatted_articles = [
            ai_analyzer.format_article_for_display(article)
            for article in processed_articles[:20]  # Top 20 cikk
        ]
        
        # Globális változók frissítése
        newsletter_data['articles'] = formatted_articles
        newsletter_data['executive_briefing'] = executive_briefing or "⚠️ Vezetői összefoglaló nem elérhető - ellenőrizze az OpenAI API kulcsot."
    else:
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

# Ütemezett feladatok beállítása
schedule.every(6).hours.do(fetch_and_process_news)

# Első futtatás háttérszálban 2 másodperc múlva
def delayed_first_run():
    """Késleltetett első futtatás"""
    time.sleep(2)
    print("\n🚀 Első hírek betöltése indul...")
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
    return jsonify(newsletter_data)

@app.route('/api/refresh', methods=['POST'])
def refresh_articles():
    """Manuális frissítés"""
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)