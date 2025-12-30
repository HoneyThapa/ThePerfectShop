import streamlit as st
import pandas as pd
from sqlalchemy import text, inspect
from app.db.session import SessionLocal
from app.db.models import StoreMaster, SKUMaster, SalesDaily, InventoryBatch, Purchase
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="ThePerfectShop - Database Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_data
def get_table_data(table_name, limit=1000):
    """Get data from a specific table"""
    db = SessionLocal()
    try:
        table_models = {
            "stores": StoreMaster,
            "products": SKUMaster,
            "sales": SalesDaily,
            "inventory": InventoryBatch,
            "purchases": Purchase
        }
        
        model = table_models.get(table_name)
        if not model:
            return pd.DataFrame()
        
        records = db.query(model).limit(limit).all()
        
        if not records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for record in records:
            row = {}
            for column in model.__table__.columns:
                row[column.name] = getattr(record, column.name)
            data.append(row)
        
        return pd.DataFrame(data)
    finally:
        db.close()

@st.cache_data
def run_query(query):
    """Run a custom SQL query"""
    db = SessionLocal()
    try:
        result = db.execute(text(query))
        if query.strip().upper().startswith('SELECT'):
            rows = result.fetchall()
            if rows:
                columns = result.keys()
                return pd.DataFrame(rows, columns=columns)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
    finally:
        db.close()

def get_table_stats():
    """Get statistics for all tables"""
    db = SessionLocal()
    try:
        stats = {}
        tables = [
            ("Stores", StoreMaster),
            ("Products", SKUMaster),
            ("Sales Records", SalesDaily),
            ("Inventory Batches", InventoryBatch),
            ("Purchase Records", Purchase)
        ]
        
        for name, model in tables:
            count = db.query(model).count()
            stats[name] = count
        
        return stats
    finally:
        db.close()

# Main app
def main():
    st.title("🗄️ ThePerfectShop Database Viewer")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Choose a view:",
            ["📊 Overview", "📋 Table Data", "🔍 Custom Query", "📈 Analytics"]
        )
    
    if page == "📊 Overview":
        show_overview()
    elif page == "📋 Table Data":
        show_table_data()
    elif page == "🔍 Custom Query":
        show_custom_query()
    elif page == "📈 Analytics":
        show_analytics()

def show_overview():
    """Show database overview"""
    st.header("📊 Database Overview")
    
    # Get table statistics
    stats = get_table_stats()
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏪 Stores", stats.get("Stores", 0))
    with col2:
        st.metric("🛒 Products", stats.get("Products", 0))
    with col3:
        st.metric("📈 Sales Records", f"{stats.get('Sales Records', 0):,}")
    with col4:
        st.metric("📦 Inventory Batches", stats.get("Inventory Batches", 0))
    with col5:
        st.metric("💰 Purchase Records", stats.get("Purchase Records", 0))
    
    st.markdown("---")
    
    # Show sample data from each table
    st.subheader("🔍 Sample Data Preview")
    
    tables = ["stores", "products", "sales", "inventory", "purchases"]
    
    for table in tables:
        with st.expander(f"📋 {table.title()} Table"):
            df = get_table_data(table, limit=5)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available")

def show_table_data():
    """Show detailed table data"""
    st.header("📋 Table Data Viewer")
    
    # Table selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        table = st.selectbox(
            "Select table:",
            ["stores", "products", "sales", "inventory", "purchases"],
            format_func=lambda x: {
                "stores": "🏪 Stores (store_master)",
                "products": "🛒 Products (sku_master)",
                "sales": "📈 Sales (sales_daily)",
                "inventory": "📦 Inventory (inventory_batch)",
                "purchases": "💰 Purchases (purchase)"
            }[x]
        )
    
    with col2:
        limit = st.number_input("Records to show:", min_value=10, max_value=10000, value=100)
    
    # Get and display data
    df = get_table_data(table, limit)
    
    if not df.empty:
        st.subheader(f"📊 {table.title()} Data ({len(df)} records)")
        
        # Show filters for some tables
        if table == "sales":
            col1, col2 = st.columns(2)
            with col1:
                if 'store_id' in df.columns:
                    stores = ['All'] + list(df['store_id'].unique())
                    selected_store = st.selectbox("Filter by Store:", stores)
                    if selected_store != 'All':
                        df = df[df['store_id'] == selected_store]
            
            with col2:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    date_range = st.date_input(
                        "Date range:",
                        value=(df['date'].min(), df['date'].max()),
                        min_value=df['date'].min(),
                        max_value=df['date'].max()
                    )
                    if len(date_range) == 2:
                        df = df[(df['date'] >= pd.Timestamp(date_range[0])) & 
                               (df['date'] <= pd.Timestamp(date_range[1]))]
        
        # Display data
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            f"📥 Download {table}.csv",
            csv,
            file_name=f"{table}_data.csv",
            mime="text/csv"
        )
        
        # Show basic statistics
        if st.checkbox("Show Statistics"):
            st.subheader("📊 Basic Statistics")
            st.write(df.describe())
    else:
        st.warning("No data found in this table")

def show_custom_query():
    """Show custom query interface"""
    st.header("🔍 Custom SQL Query")
    
    # Sample queries
    with st.expander("💡 Sample Queries"):
        sample_queries = {
            "All Stores": "SELECT * FROM store_master;",
            "Products by Category": "SELECT category, COUNT(*) as count FROM sku_master GROUP BY category ORDER BY count DESC;",
            "Recent Sales": "SELECT * FROM sales_daily ORDER BY date DESC LIMIT 20;",
            "Expiring Inventory": "SELECT * FROM inventory_batch WHERE expiry_date <= CURRENT_DATE + INTERVAL '7 days' ORDER BY expiry_date;",
            "Sales by Store": "SELECT store_id, SUM(units_sold) as total_units, SUM(revenue) as total_revenue FROM sales_daily GROUP BY store_id;",
            "Top Products": "SELECT sku_id, SUM(units_sold) as total_sold FROM sales_daily GROUP BY sku_id ORDER BY total_sold DESC LIMIT 10;",
            "Inventory Value": "SELECT store_id, SUM(on_hand_qty * cost_per_unit) as inventory_value FROM inventory_batch GROUP BY store_id;"
        }
        
        for name, query in sample_queries.items():
            if st.button(f"📋 {name}"):
                st.session_state.query = query
    
    # Query input
    query = st.text_area(
        "Enter SQL Query:",
        value=st.session_state.get('query', ''),
        height=100,
        help="Enter a SELECT query to view data"
    )
    
    if st.button("🚀 Run Query"):
        if query.strip():
            with st.spinner("Running query..."):
                df = run_query(query)
                
                if not df.empty:
                    st.success(f"✅ Query returned {len(df)} rows")
                    st.dataframe(df, use_container_width=True)
                    
                    # Download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results",
                        csv,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Query executed but returned no results")
        else:
            st.warning("Please enter a query")

def show_analytics():
    """Show analytics and visualizations"""
    st.header("📈 Database Analytics")
    
    # Sales analytics
    st.subheader("📊 Sales Analytics")
    
    sales_df = get_table_data("sales", limit=5000)
    
    if not sales_df.empty:
        # Convert date column
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sales over time
            daily_sales = sales_df.groupby('date')['revenue'].sum().reset_index()
            fig = px.line(daily_sales, x='date', y='revenue', 
                         title='Daily Revenue Trend')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sales by store
            store_sales = sales_df.groupby('store_id')['revenue'].sum().reset_index()
            fig = px.bar(store_sales, x='store_id', y='revenue',
                        title='Revenue by Store')
            st.plotly_chart(fig, use_container_width=True)
        
        # Product analytics
        st.subheader("🛒 Product Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top products by units sold
            top_products = sales_df.groupby('sku_id')['units_sold'].sum().reset_index()
            top_products = top_products.nlargest(10, 'units_sold')
            fig = px.bar(top_products, x='sku_id', y='units_sold',
                        title='Top 10 Products by Units Sold')
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Revenue distribution
            fig = px.histogram(sales_df, x='revenue', nbins=30,
                             title='Revenue Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    # Inventory analytics
    st.subheader("📦 Inventory Analytics")
    
    inventory_df = get_table_data("inventory", limit=1000)
    
    if not inventory_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Inventory by store
            store_inventory = inventory_df.groupby('store_id')['on_hand_qty'].sum().reset_index()
            fig = px.pie(store_inventory, values='on_hand_qty', names='store_id',
                        title='Inventory Distribution by Store')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Expiry analysis
            inventory_df['expiry_date'] = pd.to_datetime(inventory_df['expiry_date'])
            inventory_df['days_to_expiry'] = (inventory_df['expiry_date'] - pd.Timestamp.now()).dt.days
            
            fig = px.histogram(inventory_df, x='days_to_expiry', nbins=30,
                             title='Days to Expiry Distribution')
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()