import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    article_hash = Column(String(32), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    original_title = Column(Text, nullable=False)
    description = Column(Text)
    original_description = Column(Text)
    source = Column(String(100), nullable=False)
    category = Column(String(100))
    link = Column(Text, nullable=False)
    pub_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI elemzés mezők
    importance_score = Column(Integer, default=5)
    urgency = Column(String(20), default='monitoring')
    executive_summary = Column(Text)
    ai_analysis = Column(JSON)  # Teljes AI elemzés JSON-ben
    hungarian_title = Column(Text)  # AI által generált magyar cím
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.article_hash,
            'title': self.hungarian_title or self.title,
            'original_title': self.original_title,
            'source': self.source,
            'category': self.category,
            'pub_date': self.pub_date.isoformat() if self.pub_date else None,
            'link': self.link,
            'importance_score': self.importance_score,
            'urgency': self.urgency,
            'executive_summary': self.executive_summary,
            'full_analysis': self.ai_analysis,
            'description': self.description,
            'original_description': self.original_description
        }

class ExecutiveBriefing(Base):
    __tablename__ = 'executive_briefings'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    article_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessingStatus(Base):
    __tablename__ = 'processing_status'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False)  # 'processing', 'completed', 'failed'
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    articles_processed = Column(Integer, default=0)
    error_message = Column(Text)

# Database setup
def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Railway/Heroku style DATABASE_URL fix
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    else:
        # No database URL - run in memory mode
        return None

# Create engine
database_url = get_database_url()
if database_url:
    try:
        engine = create_engine(database_url, echo=False)
        SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        print("✅ PostgreSQL kapcsolat létrehozva")
    except Exception as e:
        print(f"❌ PostgreSQL kapcsolat hiba: {e}")
        engine = None
        SessionLocal = None
else:
    print("⚡ Memória módban fut - nincs adatbázis kapcsolat")
    engine = None
    SessionLocal = None

def get_session():
    """Get database session"""
    if SessionLocal:
        return SessionLocal()
    return None

def init_database():
    """Initialize database tables"""
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database táblák létrehozva")
            return True
        except Exception as e:
            print(f"❌ Database inicializálási hiba: {e}")
            return False
    return False

def is_database_available():
    """Check if database is available"""
    return engine is not None and SessionLocal is not None