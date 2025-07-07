# 🏛️ Kormányzati Külgazdasági Szemle

Automatizált gazdasági hírlevél és elemző rendszer a magyar kormány számára. AI-alapú elemzésekkel támogatja a gazdasági döntéshozatalt nemzetközi hírek feldolgozásával.

## 🎯 Főbb funkciók

- **Valós idejű hírek**: 21 nemzetközi gazdasági forrásból
- **AI elemzés**: Minden cikkhez részletes kormányzati szintű elemzés
- **Magyar nyelvű**: AI által generált magyar címek és összefoglalók
- **Vezetői összefoglaló**: Napi sajtószemle a legfontosabb hírekből
- **PDF export**: Nyomtatható jelentés generálása
- **Szektorális elemzés**: Ágazati hatásvizsgálatok
- **Gördülő hírek**: Top 30 legfontosabb cikk folyamatosan frissítve
- **Keresés**: Archívumban keresés kulcsszavakra
- **PostgreSQL adatbázis**: Perzisztens tárolás, hibrid működés

## 🚀 Gyors indítás

### 1. Környezet beállítása

```bash
# Virtuális környezet
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy
venv\Scripts\activate     # Windows

# Függőségek telepítése
pip install -r requirements.txt
```

### 2. API kulcsok beállítása

Hozz létre egy `.env` fájlt:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/gazdhirlevel  # Opcionális
TEST_MODE=false
```

### 3. Indítás

```bash
# Smart launcher (ajánlott) - automatikusan detektálja az adatbázist
python run.py

# Vagy közvetlenül
python app.py
```

Nyisd meg: http://localhost:5000

## 🏗️ Architektúra

### Backend komponensek
- **app.py** - Flask alkalmazás, API endpoints, ütemezés
- **ai_processor.py** - AI elemzések (Gemini 2.5 Flash + GPT-4o mini)
- **database.py** - PostgreSQL modellek (SQLAlchemy)
- **database_manager.py** - Adatbázis műveletek
- **run.py** - Smart launcher (DB auto-detect)

### Adatbázis séma
- **articles** - Cikkek teljes AI elemzésekkel
- **executive_briefings** - Vezetői összefoglalók
- **processing_status** - Feldolgozási állapot

### Frissítési ciklusok
- **RSS hírek**: 30 percenként
- **AI elemzések**: 2 óránként
- **Frontend**: Top 30 cikk fontosság szerint

## 📊 API végpontok

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/articles` | GET | Top 30 cikk lekérése |
| `/api/refresh` | POST | Teljes frissítés (minden forrás) |
| `/api/test-refresh` | POST | Teszt frissítés (3 forrás) |
| `/api/search?q=keyword` | GET | Keresés az összes cikkben |
| `/api/export-pdf` | GET | PDF jelentés letöltése |
| `/api/db-status` | GET | Adatbázis állapot |
| `/api/cleanup` | POST | Régi cikkek törlése |

## 🧪 Fejlesztés és tesztelés

### Teszt mód
```bash
# Gyors tesztelés - csak 3 forrás, 3 cikk
TEST_MODE=true python run.py

# API teszt
curl -X POST http://localhost:5000/api/test-refresh
```

### Docker használat
```bash
# PostgreSQL indítása
docker-compose up -d

# Teljes alkalmazás
docker build -t gazdhirlevel .
docker run -p 5000:5000 gazdhirlevel
```

## 🌐 Deployment

### Railway.app
1. Kapcsold össze GitHubbal
2. Állítsd be az environment változókat
3. Deploy automatikus minden push-ra

### Heroku
```bash
heroku create your-app-name
heroku config:set GEMINI_API_KEY=your_key
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

## 📰 RSS források

21 nemzetközi gazdasági forrás, többek között:
- Bloomberg (Markets, Politics, Technology)
- Financial Times
- The Economist
- Reuters Business
- Wall Street Journal
- MarketWatch
- CNBC
- És még sok más...

## 🤖 AI elemzési struktúra

Minden cikkhez:
- 🏷️ **Magyar cím**
- 📋 **Vezetői összefoglaló**
- 🌍 **Globális makrogazdasági hatások**
- 🇭🇺 **Magyarországi makrogazdasági hatások**
- 🏭 **Szektorális elemzés**
- ⚠️ **Kockázatok és lehetőségek**
- 📊 **Szakpolitikai megfontolások**
- 🔍 **Monitoring pontok**

## 🐛 Hibaelhárítás

### AI API hibák
- Ellenőrizd a `GEMINI_API_KEY` és `OPENAI_API_KEY` értékeket
- Figyelj a rate limit-ekre
- Fallback: ha egy API nem működik, a másik átveszi

### Adatbázis problémák
- Az app automatikusan memória módba vált, ha nincs DB
- `DATABASE_URL` formátum: `postgresql://user:pass@host:port/db`
- Docker: `docker-compose ps` státusz ellenőrzés

### PDF export
```bash
# Ha nem működik a PDF export, telepítsd:
sudo apt-get install wkhtmltopdf  # Linux
brew install wkhtmltopdf          # macOS
```

## 📝 Környezeti változók

| Változó | Leírás | Kötelező |
|---------|--------|----------|
| `GEMINI_API_KEY` | Google AI API kulcs | ✅ |
| `OPENAI_API_KEY` | OpenAI API kulcs | ✅ |
| `DATABASE_URL` | PostgreSQL kapcsolat | ❌ |
| `TEST_MODE` | Teszt mód (true/false) | ❌ |
| `PORT` | Alkalmazás port | ❌ |

## 🔒 Biztonsági megjegyzések

- Soha ne commitold a `.env` fájlt!
- Használj erős jelszavakat az adatbázishoz
- Korlátozd az API kulcsok jogosultságait
- HTTPS használata production környezetben

## 📄 Licensz

MIT License - lásd [LICENSE](LICENSE) fájl

## 🤝 Közreműködés

1. Fork-old a repót
2. Hozz létre egy feature branch-et
3. Commitold a változásokat
4. Push és pull request

## 👥 Készítők

- Fejlesztés: Tamas Csizmadia
- AI asszisztens: Claude (Anthropic)

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>