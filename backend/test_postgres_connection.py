#!/usr/bin/env python3
"""
Test PostgreSQL connection before setting up the database
"""

import psycopg2
import sys

def test_postgres_connection():
    """Test if PostgreSQL is running and accessible"""
    print("🔍 Testing PostgreSQL Connection")
    print("=" * 40)
    
    try:
        # Try to connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            port=5432,
            database="postgres"  # Connect to default postgres database
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print("✅ PostgreSQL Connection: SUCCESS")
        print(f"📋 Version: {version}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 PostgreSQL is ready!")
        print("💡 Next step: Run 'python setup_local_db.py' to create the database")
        return True
        
    except psycopg2.OperationalError as e:
        print("❌ PostgreSQL Connection: FAILED")
        print(f"📋 Error: {e}")
        
        print("\n💡 Troubleshooting:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Check if the service is started:")
        print("   - Postgres.app: Open the app and start the server")
        print("   - Official installer: Check 'Services' in System Preferences")
        print("3. Verify credentials: username='postgres', password='postgres'")
        print("4. Check if port 5432 is available: lsof -i :5432")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)