#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Setup database tables"""
    try:
        from database import init_database, is_database_available
        from database_manager import db_manager
        
        print("🗄️  PostgreSQL Database Setup")
        print("=" * 40)
        
        # Check if database URL is provided
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("❌ DATABASE_URL not found in .env file")
            print("💡 Example: DATABASE_URL=postgresql://user:pass@localhost:5432/gazdhirlevel")
            return False
        
        print(f"📡 Connecting to: {db_url.split('@')[1] if '@' in db_url else 'database'}")
        
        # Initialize database
        if init_database():
            print("✅ Database tables created successfully!")
            
            # Test database connection
            if db_manager.available:
                print("✅ Database manager is working")
                
                # Show current statistics
                articles = db_manager.get_latest_articles(1000)
                briefing = db_manager.get_latest_executive_briefing()
                
                print(f"📊 Current articles in database: {len(articles)}")
                print(f"📋 Latest briefing: {'Available' if briefing else 'None'}")
                
                return True
            else:
                print("❌ Database manager not available")
                return False
        else:
            print("❌ Failed to initialize database")
            return False
            
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Kormányzati Külgazdasági Szemle - Database Setup")
    print()
    
    if setup_database():
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Run: python app.py")
        print("  2. Visit: http://localhost:5000")
        print("  3. Test: curl -X POST http://localhost:5000/api/test-refresh")
    else:
        print("\n💔 Database setup failed!")
        print("\n🔧 Troubleshooting:")
        print("  1. Check DATABASE_URL in .env file")
        print("  2. Ensure PostgreSQL is running")
        print("  3. Verify database exists and user has permissions")
        print("  4. App will fall back to memory mode if database is unavailable")
        sys.exit(1)

if __name__ == "__main__":
    main()