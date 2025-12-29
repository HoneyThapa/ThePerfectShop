"""
Check database connectivity and table status
"""
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
from app.db.session import DATABASE_URL, engine
from app.db.models import Base

def check_database_status():
    """Check if database is accessible and tables exist"""
    
    print("=== Database Status Check ===\n")
    
    # 1. Check database connectivity
    print("1. Testing database connection...")
    try:
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   ✅ Database connected successfully")
            print(f"   PostgreSQL version: {version}")
    except OperationalError as e:
        print(f"   ❌ Database connection failed: {str(e)}")
        print(f"   Expected database: {DATABASE_URL}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False
    
    # 2. Check if database exists
    print("\n2. Checking database existence...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"   ✅ Connected to database: {db_name}")
    except Exception as e:
        print(f"   ❌ Could not verify database: {str(e)}")
        return False
    
    # 3. Check table existence
    print("\n3. Checking table existence...")
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            'raw_uploads',
            'sales_daily', 
            'inventory_batches',
            'purchases',
            'features_store_sku',
            'batch_risk',
            'store_master',
            'sku_master'
        ]
        
        print(f"   Existing tables: {existing_tables}")
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print(f"   ✅ {table}: EXISTS")
            else:
                print(f"   ❌ {table}: MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n   Missing tables: {missing_tables}")
            return False
        else:
            print(f"\n   ✅ All {len(expected_tables)} tables exist")
            
    except Exception as e:
        print(f"   ❌ Could not check tables: {str(e)}")
        return False
    
    # 4. Test table structure
    print("\n4. Checking table structures...")
    try:
        sample_checks = [
            ("sales_daily", ["date", "store_id", "sku_id", "units_sold"]),
            ("features_store_sku", ["date", "store_id", "sku_id", "v7", "v14", "v30", "volatility"]),
            ("inventory_batches", ["snapshot_date", "store_id", "sku_id", "batch_id", "expiry_date"])
        ]
        
        for table_name, expected_columns in sample_checks:
            columns = inspector.get_columns(table_name)
            column_names = [col['name'] for col in columns]
            
            missing_cols = [col for col in expected_columns if col not in column_names]
            if missing_cols:
                print(f"   ❌ {table_name}: Missing columns {missing_cols}")
                return False
            else:
                print(f"   ✅ {table_name}: All required columns present")
                
    except Exception as e:
        print(f"   ❌ Could not check table structures: {str(e)}")
        return False
    
    # 5. Test basic operations
    print("\n5. Testing basic database operations...")
    try:
        with engine.connect() as conn:
            # Test SELECT
            result = conn.execute(text("SELECT COUNT(*) FROM raw_uploads"))
            upload_count = result.fetchone()[0]
            print(f"   ✅ SELECT operation: {upload_count} records in raw_uploads")
            
            # Test INSERT (and rollback)
            trans = conn.begin()
            try:
                conn.execute(text("""
                    INSERT INTO raw_uploads (file_name, file_type, status) 
                    VALUES ('test.csv', 'CSV', 'TEST')
                """))
                trans.rollback()  # Don't actually save the test record
                print(f"   ✅ INSERT operation: Test successful (rolled back)")
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"   ❌ Database operations failed: {str(e)}")
        return False
    
    print("\n=== Summary ===")
    print("✅ Database is READY and FULLY CONFIGURED")
    print("   - PostgreSQL connection: Working")
    print("   - All required tables: Present") 
    print("   - Table structures: Correct")
    print("   - Basic operations: Functional")
    
    return True

def create_tables_if_missing():
    """Create tables if they don't exist"""
    print("\n=== Creating Missing Tables ===")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        db_ready = check_database_status()
        
        if not db_ready:
            print("\n🔧 Attempting to create missing tables...")
            if create_tables_if_missing():
                print("\n🔄 Re-checking database status...")
                db_ready = check_database_status()
        
        if db_ready:
            print("\n🎉 DATABASE IS READY FOR USE!")
            sys.exit(0)
        else:
            print("\n❌ DATABASE IS NOT READY")
            print("\nTo fix this, you need to:")
            print("1. Install and start PostgreSQL")
            print("2. Create database 'ThePerfectShop'")
            print("3. Ensure user 'postgres' has access")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nCheck cancelled by user")
        sys.exit(1)