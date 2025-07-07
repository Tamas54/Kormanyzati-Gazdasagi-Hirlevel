# Kormányzati Gazdasági Sajtószemle - Gazdhirlevel

Professzionális gazdasági elemző rendszer kormányzati döntéshozók számára. Az alkalmazás angol nyelvű gazdasági forrásokból készít részletes magyar nyelvű elemzéseket és döntéstámogatási anyagokat.

## 🏛️ Főbb jellemzők

### Intelligens AI elemzés
- **Gemini 2.5 Flash** és **GPT-4o mini** alapú elemzések
- Kormányzati szintű makrogazdasági hatásvizsgálatok
- Szektorális elemzések és munkaerőpiaci következmények
- Geopolitikai kontextus és EU-s vonatkozások
- Kockázatelemzés és lehetőségek feltárása
- Konkrét szakpolitikai javaslatok

### Átfogó forráskezelés
- 20+ vezető nemzetközi gazdasági forrás
- Bloomberg, Financial Times, Reuters, WSJ, The Economist
- Gazdasági think tank-ek és elemző központok
- Automatikus angol→magyar fordítás
- 48 órás időablak a releváns hírekhez

### Vezetői funkcionalitás
- Napi vezetői összefoglaló (executive briefing)
- Fontossági és sürgősségi besorolás
- Részletes elemzések lenyitható formában
- Monitoring pontok és figyelendő indikátorok
- Eredeti cikkek teljes tartalma

## 📋 Telepítés

1. **Függőségek telepítése:**
```bash
cd /home/tamas/hirmagnet/Gazdhirlevel
pip install -r requirements.txt
```

2. **Környezeti változók beállítása (.env fájl):**
```
PORT=5000
FLASK_ENV=production
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

3. **Alkalmazás indítása:**
```bash
python app.py
```

## 🚀 Railway deployment

Az alkalmazás Railway-re optimalizált. A `railway.json` konfiguráció automatikusan kezeli a build és deploy folyamatot.

## 🔧 API végpontok

- `GET /` - Főoldal a kormányzati elemzésekkel
- `GET /api/articles` - JSON formátumú teljes adatkészlet
- `POST /api/refresh` - Manuális frissítés és AI elemzés indítása

## 📊 Elemzési struktúra

Minden cikkhez tartozik:
- **Vezetői összefoglaló**: 3-5 mondatos lényegkiemelés
- **Makrogazdasági hatások**: GDP, infláció, költségvetés, HUF árfolyam
- **Szektorális elemzés**: Érintett iparágak és vállalatok
- **Geopolitikai kontextus**: EU és regionális következmények
- **Kockázatok és lehetőségek**: Főbb tényezők időhorizonttal
- **Szakpolitikai javaslatok**: Konkrét kormányzati lépések
- **Monitoring pontok**: Követendő indikátorok

## ⏰ Ütemezés

- Automatikus frissítés 6 óránként
- Manuális frissítés bármikor indítható
- Feldolgozási idő: 3-5 perc (AI elemzésekkel)

## 🔒 Biztonsági megjegyzések

- Az API kulcsokat mindig környezeti változókban tárold
- Ne commitold a `.env` fájlt
- Railway-n használj encrypted secrets-et

## 📈 Teljesítmény

- Max 60 cikk feldolgozása egyszerre (3 cikk/forrás)
- Top 20 cikk részletes megjelenítése
- Optimalizált AI promptok a költséghatékonyság érdekében