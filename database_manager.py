from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import Article, ExecutiveBriefing, ProcessingStatus, get_session, is_database_available
import hashlib

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.available = is_database_available()
        
    def save_article(self, article_data: Dict, analysis: Optional[Dict] = None) -> bool:
        """Save article to database"""
        if not self.available:
            return False
            
        session = get_session()
        if not session:
            return False
            
        try:
            # Check if article already exists
            existing = session.query(Article).filter_by(
                article_hash=article_data['id']
            ).first()
            
            if existing:
                # Update existing article with new analysis
                if analysis:
                    existing.ai_analysis = analysis
                    existing.importance_score = analysis.get('importance_score', 5)
                    existing.urgency = analysis.get('urgency', 'monitoring')
                    existing.executive_summary = analysis.get('executive_summary', '')
                    existing.hungarian_title = analysis.get('hungarian_title', '')
                session.commit()
                return True
            
            # Create new article
            article = Article(
                article_hash=article_data['id'],
                title=article_data.get('title', ''),
                original_title=article_data.get('original_title', ''),
                description=article_data.get('description', ''),
                original_description=article_data.get('original_description', ''),
                source=article_data.get('source', ''),
                category=article_data.get('category', ''),
                link=article_data.get('link', ''),
                pub_date=datetime.fromisoformat(article_data['pub_date'].replace('Z', '+00:00')) if article_data.get('pub_date') else datetime.utcnow()
            )
            
            # Add AI analysis if available
            if analysis:
                article.ai_analysis = analysis
                article.importance_score = analysis.get('importance_score', 5)
                article.urgency = analysis.get('urgency', 'monitoring')
                article.executive_summary = analysis.get('executive_summary', '')
                article.hungarian_title = analysis.get('hungarian_title', '')
            
            session.add(article)
            session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Article save error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_latest_articles(self, limit: int = 20) -> List[Dict]:
        """Get latest articles ordered by importance and date"""
        if not self.available:
            return []
            
        session = get_session()
        if not session:
            return []
            
        try:
            articles = session.query(Article)\
                .order_by(Article.importance_score.desc(), Article.pub_date.desc())\
                .limit(limit)\
                .all()
            
            return [article.to_dict() for article in articles]
            
        except Exception as e:
            print(f"❌ Get articles error: {e}")
            return []
        finally:
            session.close()
    
    def save_executive_briefing(self, content: str, article_count: int) -> bool:
        """Save executive briefing"""
        if not self.available:
            return False
            
        session = get_session()
        if not session:
            return False
            
        try:
            briefing = ExecutiveBriefing(
                content=content,
                article_count=article_count
            )
            session.add(briefing)
            session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Executive briefing save error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_latest_executive_briefing(self) -> Optional[Dict]:
        """Get latest executive briefing"""
        if not self.available:
            return None
            
        session = get_session()
        if not session:
            return None
            
        try:
            briefing = session.query(ExecutiveBriefing)\
                .order_by(ExecutiveBriefing.created_at.desc())\
                .first()
            
            if briefing:
                return {
                    'content': briefing.content,
                    'article_count': briefing.article_count,
                    'created_at': briefing.created_at.isoformat()
                }
            return None
            
        except Exception as e:
            print(f"❌ Get executive briefing error: {e}")
            return None
        finally:
            session.close()
    
    def start_processing(self) -> bool:
        """Mark processing as started"""
        if not self.available:
            return False
            
        session = get_session()
        if not session:
            return False
            
        try:
            status = ProcessingStatus(
                status='processing',
                started_at=datetime.utcnow()
            )
            session.add(status)
            session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Start processing error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def complete_processing(self, articles_processed: int) -> bool:
        """Mark processing as completed"""
        if not self.available:
            return False
            
        session = get_session()
        if not session:
            return False
            
        try:
            # Get latest processing status
            status = session.query(ProcessingStatus)\
                .filter_by(status='processing')\
                .order_by(ProcessingStatus.started_at.desc())\
                .first()
            
            if status:
                status.status = 'completed'
                status.completed_at = datetime.utcnow()
                status.articles_processed = articles_processed
                session.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Complete processing error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def cleanup_old_articles(self, days: int = 30) -> int:
        """Clean up old articles"""
        if not self.available:
            return 0
            
        session = get_session()
        if not session:
            return 0
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(Article)\
                .filter(Article.created_at < cutoff_date)\
                .delete()
            session.commit()
            
            print(f"✅ Törölve {deleted} régi cikk ({days} napnál régebbi)")
            return deleted
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            session.rollback()
            return 0
        finally:
            session.close()

# Global instance
db_manager = DatabaseManager()