# 🗄️ Database Access Guide

## Multiple Ways to View Your PostgreSQL Database

### 1. **Python Command Line Viewer** (Easiest)

```bash
cd backend

# Show table overview
python view_database.py info

# View specific tables
python view_database.py stores
python view_database.py products
python view_database.py sales 20
python view_database.py inventory
python view_database.py purchases

# Interactive mode
python view_database.py
```

### 2. **Web-Based Database Viewer** (Most Visual)

```bash
cd backend
streamlit run database_viewer_ui.py
```

Then open: http://localhost:8501

Features:
- 📊 Database overview with statistics
- 📋 Browse all tables with filtering
- 🔍 Run custom SQL queries
- 📈 Analytics with charts and graphs
- 📥 Download data as CSV

### 3. **Through the Main UI** (Integrated)

```bash
cd backend
python start_system.py
```

The main UI shows live database data in the dashboard and analytics sections.

### 4. **Direct SQL Access** (Advanced)

If you have PostgreSQL command line tools installed:

```bash
# Connect to database
psql -h localhost -U postgres -d theperfectshop

# Or if using different credentials
psql -h localhost -U your_username -d theperfectshop
```

### 5. **Python Script for Custom Queries**

Create a simple script:

```python
from backend.app.db.session import SessionLocal
from sqlalchemy import text
import pandas as pd

db = SessionLocal()

# Run any SQL query
query = "SELECT * FROM store_master;"
result = db.execute(text(query))
df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(df)

db.close()
```

## 📊 Your Database Contains

- **🏪 3 Stores**: Downtown, Suburbs, Mall
- **🛒 15 Products**: Across dairy, bakery, produce, meat, frozen categories
- **📈 2,697 Sales Records**: 60 days of transaction history
- **📦 82 Inventory Batches**: Current stock with expiry dates
- **💰 82 Purchase Records**: Supply chain data

## 🔍 Useful Sample Queries

### View All Stores
```sql
SELECT * FROM store_master;
```

### Products by Category
```sql
SELECT category, COUNT(*) as count 
FROM sku_master 
GROUP BY category 
ORDER BY count DESC;
```

### Recent Sales
```sql
SELECT * FROM sales_daily 
ORDER BY date DESC 
LIMIT 20;
```

### Expiring Inventory (Next 7 Days)
```sql
SELECT * FROM inventory_batch 
WHERE expiry_date <= CURRENT_DATE + INTERVAL '7 days' 
ORDER BY expiry_date;
```

### Sales by Store
```sql
SELECT store_id, 
       SUM(units_sold) as total_units, 
       SUM(revenue) as total_revenue 
FROM sales_daily 
GROUP BY store_id;
```

### Top Selling Products
```sql
SELECT sku_id, SUM(units_sold) as total_sold 
FROM sales_daily 
GROUP BY sku_id 
ORDER BY total_sold DESC 
LIMIT 10;
```

### Inventory Value by Store
```sql
SELECT store_id, 
       SUM(on_hand_qty * cost_per_unit) as inventory_value 
FROM inventory_batch 
GROUP BY store_id;
```

## 🛠️ Database Schema

### Tables Structure:

1. **store_master**
   - store_id (Primary Key)
   - city
   - zone

2. **sku_master**
   - sku_id (Primary Key)
   - category
   - mrp (Maximum Retail Price)

3. **sales_daily**
   - store_id
   - sku_id
   - date
   - units_sold
   - revenue

4. **inventory_batch**
   - store_id
   - sku_id
   - batch_id
   - expiry_date
   - on_hand_qty
   - cost_per_unit

5. **purchase**
   - store_id
   - sku_id
   - batch_id
   - purchase_date
   - quantity
   - cost_per_unit

## 🚀 Quick Commands

```bash
# See database overview
python view_database.py info

# Browse stores
python view_database.py stores

# See recent sales
python view_database.py sales 50

# Interactive database browser
python view_database.py

# Web-based viewer with charts
streamlit run database_viewer_ui.py

# Full system with UI
python start_system.py
```

## 💡 Tips

- Use the web viewer for visual exploration
- Use command line for quick data checks
- Download data as CSV for external analysis
- Run custom queries to get specific insights
- Check expiring inventory regularly
- Monitor sales trends by store and product

Your database is fully populated and ready to explore! 🎉