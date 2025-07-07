#!/usr/bin/env python3
"""
Kormányzati Külgazdasági Szemle - Egyszerű indító
Detektálja mi van és azzal indul
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

def check_docker_postgres():
    """Ellenőrzi van-e Docker PostgreSQL"""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        result = subprocess.run(['docker', 'ps', '--filter', 'name=postgres'], capture_output=True, text=True)
        return 'postgres' in result.stdout
    except:
        return False

def start_docker_postgres():
    """Elindítja PostgreSQL-t Docker-rel"""
    print("🐳 Starting PostgreSQL with Docker...")
    try:
        subprocess.run([
            'docker', 'run', '-d',
            '--name', 'gazdhir_postgres',
            '-e', 'POSTGRES_DB=gazdhirlevel',
            '-e', 'POSTGRES_USER=gazdhir_user', 
            '-e', 'POSTGRES_PASSWORD=gazdhir_pass',
            '-p', '5432:5432',
            'postgres:15'
        ], check=True)
        
        print("⏳ Waiting for PostgreSQL to start...")
        time.sleep(8)
        return True
    except subprocess.CalledProcessError:
        # Már fut
        print("✅ PostgreSQL container already running")
        return True
    except Exception as e:
        print(f"❌ Failed to start Docker PostgreSQL: {e}")
        return False

def check_local_postgres():
    """Ellenőrzi fut-e lokális PostgreSQL"""
    try:
        result = subprocess.run(['pg_isready', '-h', 'localhost'], capture_output=True)
        return result.returncode == 0
    except:
        return False

def test_database_connection():
    """Teszteli az adatbázis kapcsolatot"""
    try:
        from database import init_database, is_database_available
        
        if is_database_available():
            init_database()
            print("✅ Database connection successful!")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Database test failed: {e}")
        return False

def main():
    """Smart launcher"""
    print("🏛️ Kormányzati Külgazdasági Szemle")
    print("=" * 50)
    
    # Load existing .env
    load_dotenv()
    
    database_ready = False
    db_url = "postgresql://gazdhir_user:gazdhir_pass@localhost:5432/gazdhirlevel"
    
    # 1. Van-e már DATABASE_URL?
    env_db_url = os.getenv('DATABASE_URL')
    if env_db_url:
        print("📄 Found DATABASE_URL in .env")
        os.environ['DATABASE_URL'] = env_db_url
        if test_database_connection():
            print("✅ Existing database works!")
            database_ready = True
    
    # 2. Lokális PostgreSQL check (prioritás!)
    if not database_ready and check_local_postgres():
        print("🐘 Local PostgreSQL detected")
        os.environ['DATABASE_URL'] = db_url
        if test_database_connection():
            database_ready = True
    
    # 3. Docker PostgreSQL check
    if not database_ready:
        if check_docker_postgres():
            print("🐳 Docker PostgreSQL detected")
            os.environ['DATABASE_URL'] = db_url
            if test_database_connection():
                database_ready = True
        else:
            # Próbáljunk Docker-t indítani CSAK ha nincs lokális
            if not check_local_postgres():
                try:
                    subprocess.run(['docker', '--version'], capture_output=True, check=True)
                    if start_docker_postgres():
                        os.environ['DATABASE_URL'] = db_url
                        if test_database_connection():
                            database_ready = True
                except:
                    pass
    
    # 4. Eredmény
    if database_ready:
        print("💾 Database mode: PostgreSQL")
        # .env update ha kell
        if not env_db_url:
            with open('.env', 'a') as f:
                f.write(f"\nDATABASE_URL={db_url}\n")
            print("📝 DATABASE_URL added to .env")
    else:
        print("💾 Memory mode: No database (this is fine!)")
    
    # 5. Flask indítás
    print("\n🚀 Starting application...")
    try:
        import app
        print("\n🎉 Ready!")
        print("📱 Visit: http://localhost:5000")
        print("🧪 Test: curl -X POST http://localhost:5000/api/test-refresh")
        print("🛑 Stop: Ctrl+C\n")
        
        # Run the app
        port = int(os.environ.get('PORT', 5000))
        app.app.run(host='0.0.0.0', port=port, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: python app.py")

if __name__ == "__main__":
    main()