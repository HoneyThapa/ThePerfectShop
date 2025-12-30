#!/usr/bin/env python3
"""
Interactive Database Viewer for ThePerfectShop
View all tables, data, and run custom queries
"""

import pandas as pd
from sqlalchemy import text, inspect
from app.db.session import SessionLocal
from app.db.models import StoreMaster, SKUMaster, SalesDaily, InventoryBatch, Purchase
import sys

def show_table_info():
    """Show information about all tables"""
    print("📊 Database Tables Overview")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get table counts
        tables_info = [
            ("store_master", StoreMaster, "🏪 Store information"),
            ("sku_master", SKUMaster, "🛒 Product catalog"),
            ("sales_daily", SalesDaily, "📈 Daily sales records"),
            ("inventory_batch", InventoryBatch, "📦 Inventory batches"),
            ("purchase", Purchase, "💰 Purchase records")
        ]
        
        for table_name, model, description in tables_info:
            count = db.query(model).count()
            print(f"{description}")
            print(f"   Table: {table_name}")
            print(f"   Records: {count:,}")
            print()
        
    finally:
        db.close()

def view_table(table_name, limit=10):
    """View data from a specific table"""
    db = SessionLocal()
    try:
        print(f"📋 Viewing {table_name} (showing first {limit} records)")
        print("=" * 80)
        
        # Map table names to models
        table_models = {
            "stores": StoreMaster,
            "store_master": StoreMaster,
            "products": SKUMaster,
            "sku_master": SKUMaster,
            "sales": SalesDaily,
            "sales_daily": SalesDaily,
            "inventory": InventoryBatch,
            "inventory_batch": InventoryBatch,
            "purchases": Purchase,
            "purchase": Purchase
        }
        
        model = table_models.get(table_name.lower())
        if not model:
            print(f"❌ Unknown table: {table_name}")
            print(f"Available tables: {', '.join(table_models.keys())}")
            return
        
        # Get data
        records = db.query(model).limit(limit).all()
        
        if not records:
            print("📭 No records found")
            return
        
        # Convert to DataFrame for nice display
        data = []
        for record in records:
            row = {}
            for column in model.__table__.columns:
                row[column.name] = getattr(record, column.name)
            data.append(row)
        
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
        
        print(f"\n📊 Total records in {table_name}: {db.query(model).count():,}")
        
    finally:
        db.close()

def run_custom_query(query):
    """Run a custom SQL query"""
    db = SessionLocal()
    try:
        print(f"🔍 Running Query:")
        print(f"   {query}")
        print("=" * 80)
        
        result = db.execute(text(query))
        
        # Handle different types of queries
        if query.strip().upper().startswith('SELECT'):
            # For SELECT queries, show results
            rows = result.fetchall()
            if rows:
                # Get column names
                columns = result.keys()
                df = pd.DataFrame(rows, columns=columns)
                print(df.to_string(index=False))
                print(f"\n📊 Returned {len(rows)} rows")
            else:
                print("📭 No results returned")
        else:
            # For other queries, show affected rows
            print(f"✅ Query executed successfully")
            if hasattr(result, 'rowcount'):
                print(f"📊 Affected rows: {result.rowcount}")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
    finally:
        db.close()

def show_sample_queries():
    """Show some useful sample queries"""
    print("💡 Sample Queries You Can Try:")
    print("=" * 60)
    
    queries = [
        ("Show all stores", "SELECT * FROM store_master;"),
        ("Show products by category", "SELECT category, COUNT(*) as count FROM sku_master GROUP BY category;"),
        ("Recent sales", "SELECT * FROM sales_daily ORDER BY date DESC LIMIT 10;"),
        ("Expiring inventory", "SELECT * FROM inventory_batch WHERE expiry_date <= CURRENT_DATE + INTERVAL '7 days' ORDER BY expiry_date;"),
        ("Sales by store", "SELECT store_id, SUM(units_sold) as total_units, SUM(revenue) as total_revenue FROM sales_daily GROUP BY store_id;"),
        ("Top selling products", "SELECT sku_id, SUM(units_sold) as total_sold FROM sales_daily GROUP BY sku_id ORDER BY total_sold DESC LIMIT 10;"),
        ("Inventory value by store", "SELECT store_id, SUM(on_hand_qty * cost_per_unit) as inventory_value FROM inventory_batch GROUP BY store_id;")
    ]
    
    for i, (description, query) in enumerate(queries, 1):
        print(f"{i}. {description}")
        print(f"   {query}")
        print()

def interactive_mode():
    """Interactive database exploration"""
    print("🛒 ThePerfectShop Database Viewer")
    print("=" * 60)
    
    while True:
        print("\n🔧 What would you like to do?")
        print("1. Show table overview")
        print("2. View table data")
        print("3. Run custom query")
        print("4. Show sample queries")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            show_table_info()
            
        elif choice == '2':
            print("\nAvailable tables:")
            print("- stores (store_master)")
            print("- products (sku_master)")
            print("- sales (sales_daily)")
            print("- inventory (inventory_batch)")
            print("- purchases (purchase)")
            
            table = input("\nEnter table name: ").strip()
            limit = input("How many records to show? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            
            view_table(table, limit)
            
        elif choice == '3':
            query = input("\nEnter SQL query: ").strip()
            if query:
                run_custom_query(query)
            
        elif choice == '4':
            show_sample_queries()
            
        elif choice == '5':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'info':
            show_table_info()
        elif command == 'queries':
            show_sample_queries()
        elif command in ['stores', 'products', 'sales', 'inventory', 'purchases']:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            view_table(command, limit)
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python view_database.py [info|queries|stores|products|sales|inventory|purchases] [limit]")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()