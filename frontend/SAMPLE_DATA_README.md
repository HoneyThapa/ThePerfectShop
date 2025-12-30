# Sample Inventory Data

This directory contains sample CSV files for testing the AI Operations Copilot system.

## Files Available

### 1. `sample_inventory.csv` (30 items)
- **Purpose**: Basic testing with moderate risk scenarios
- **Stores**: 3 stores (STORE001, STORE002, STORE003)
- **Categories**: Fruits, Dairy, Bakery, Meat, Seafood, Vegetables, Beverages, Frozen, Pantry, Snacks
- **Risk Levels**: Mixed - some items expiring soon (1-3 days), others with longer shelf life
- **Use Case**: Quick testing and demonstration

### 2. `comprehensive_inventory.csv` (40 items)
- **Purpose**: Comprehensive testing with varied risk scenarios
- **Stores**: 4 stores (STORE001-STORE004)
- **Categories**: Premium and regular items across all categories
- **Risk Levels**: 
  - **High Risk**: Premium perishables expiring in 1-3 days
  - **Medium Risk**: Regular items expiring in 4-10 days
  - **Low Risk**: Pantry items with long shelf life
- **Use Case**: Full system testing and realistic scenarios

## Data Structure

Each CSV file contains the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `store_id` | Unique store identifier | STORE001 |
| `sku_id` | Stock Keeping Unit ID | SKU001 |
| `batch_id` | Batch/lot identifier | BATCH001 |
| `product_name` | Human-readable product name | Fresh Apples |
| `category` | Product category | Fruits |
| `on_hand_qty` | Current inventory quantity | 45 |
| `expiry_date` | Product expiration date | 2025-01-15 |
| `cost_per_unit` | Cost price per unit | 2.50 |
| `selling_price` | Retail price per unit | 4.99 |

## Risk Scenarios Included

### High Risk Items (Expiring 1-3 days)
- Premium Strawberries (25 units, expires 2025-01-02)
- Fresh Raspberries (12 units, expires 2025-01-02)
- Gourmet Croissants (8 units, expires 2025-01-02)
- Fresh Lobster Tails (4 units, expires 2025-01-03)

### Medium Risk Items (Expiring 4-10 days)
- Whole Milk (28-60 units, expires 2025-01-08-10)
- Ground Beef (12 units, expires 2025-01-10)
- Fresh Spinach (30-35 units, expires 2025-01-09)

### Low Risk Items (Long shelf life)
- Canned Tomatoes (100 units, expires 2025-12-31)
- Pasta (45-80 units, expires 2025-06-20)
- Rice (60 units, expires 2025-09-30)

## Expected AI Insights

When you upload these files, the AI should identify:

1. **Immediate Actions Needed**:
   - Markdown recommendations for items expiring in 1-3 days
   - Transfer suggestions for overstocked items
   - Disposal recommendations for expired items

2. **Key Metrics**:
   - Total at-risk value: $500-2000 (depending on file)
   - High-risk batches: 5-10 items
   - Average days to expiry: 15-45 days

3. **Business Insights**:
   - Category-wise risk analysis
   - Store-wise performance comparison
   - Profit margin optimization opportunities

## How to Use

1. **Upload CSV**: Use the file uploader in the left navigation panel
2. **Confirm Data**: Review the preview and click "Confirm & Continue"
3. **Get AI Insights**: Navigate to AI Insights tab and click "Get AI Insights"
4. **Review Recommendations**: Examine the action recommendations and provide feedback
5. **Chat with AI**: Ask specific questions about your inventory in the AI Chatbot tab

## Customization

You can modify these files or create your own by:
- Adjusting expiry dates for different risk scenarios
- Changing quantities to test different stock levels
- Adding new products or categories
- Modifying prices to test profit margin calculations

The system will automatically calculate risk scores based on:
- Days to expiry (closer = higher risk)
- Quantity levels (more units = higher potential loss)
- Value at risk (cost × quantity)