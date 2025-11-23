# Sample Database Setup Guide

## 📊 What's Included

I've created a realistic **e-commerce database** with:

- **6 Tables**: regions, customers, categories, products, orders, order_items
- **200+ rows** of sample data
- **Relationships**: Foreign keys connecting all tables
- **2 Views**: Pre-built analytics views
- **Indexes**: For optimal query performance

## 🚀 Quick Setup (3 minutes)

### Option 1: Using psql (Recommended)

```bash
# Connect to your Neon database
psql "your_neon_connection_string_here"

# Run the setup script
\i scripts/sample_data.sql

# Exit
\q
```

### Option 2: Using Neon Web Console

1. Go to [console.neon.tech](https://console.neon.tech)
2. Select your project
3. Click on "SQL Editor"
4. Copy the contents of `scripts/sample_data.sql`
5. Paste and click "Run"

### Option 3: Using DBeaver/pgAdmin

1. Open your database tool
2. Connect to Neon using your connection string
3. Open `scripts/sample_data.sql`
4. Execute the script

## 📋 Database Schema

```
┌─────────────┐
│   regions   │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
┌──────┴────────┐    │
│   customers   │    │
└──────┬────────┘    │
       │             │
       │   ┌─────────┴────────┐
       │   │    categories    │
       │   └─────────┬────────┘
       │             │
       │   ┌─────────┴────────┐
       │   │     products     │
       │   └─────────┬────────┘
       │             │
┌──────┴────────┐    │
│    orders     │    │
└──────┬────────┘    │
       │             │
┌──────┴────────┐────┘
│  order_items  │
└───────────────┘
```

## 🎯 Sample Natural Language Queries to Test

Once your database is set up, try these questions in the NL2SQL app:

### **Easy Queries**
- "How many customers do we have?"
- "Show me all active customers"
- "List all products in the Electronics category"
- "What regions do we serve?"

### **Medium Queries**
- "Show me total sales by category"
- "Who are our top 5 customers by total spending?"
- "How many orders were placed last month?"
- "What's the average order value?"

### **Advanced Queries**
- "Show me monthly revenue for the last 3 months"
- "Which products are low in stock (less than 50 units)?"
- "List customers who haven't ordered anything"
- "What's the total revenue by region?"

### **Time-Based Queries**
- "Show me orders from last week"
- "How many sales did we have today?"
- "What's our revenue for November 2024?"

### **Analytical Queries**
- "Which category generates the most revenue?"
- "Show me the top 3 best-selling products"
- "How many orders are currently being shipped?"
- "What's the average customer loyalty points?"

## 📊 Database Statistics

After running the script, you'll have:

| Table | Rows | Description |
|-------|------|-------------|
| **regions** | 5 | Geographic regions (NA, Europe, Asia, etc.) |
| **customers** | 15 | Customer profiles with loyalty points |
| **categories** | 6 | Product categories |
| **products** | 25 | Products with prices and stock |
| **orders** | 20 | Order history (last 3 months) |
| **order_items** | 35+ | Individual items in each order |
| **Views** | 2 | Pre-built analytics queries |

## 🔍 Verify Installation

Check if everything loaded correctly:

```sql
-- Count rows in each table
SELECT 'regions' as table_name, COUNT(*) as rows FROM regions
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;

-- Test a query
SELECT * FROM sales_summary;
```

Expected output:
- regions: 5 rows
- customers: 15 rows  
- products: 25 rows
- orders: 20 rows

## 🎨 Sample Data Highlights

### Customers
- 15 customers across 5 regions
- Mix of active (13) and inactive (2) customers
- Loyalty points ranging from 50 to 4,100

### Products
- 25 products across 6 categories
- Prices from $14.99 to $299.99
- Stock quantities from 28 to 250 units
- 8 featured products

### Orders
- 20 orders spanning 3 months
- Status types: delivered, shipped, processing, cancelled
- Order values from $44.99 to $559.96
- Most recent orders from last week

## 🔐 Setting Up Read-Only User (Important!)

After loading the data, create a read-only user for the NL2SQL app:

```sql
-- Create readonly user
CREATE USER nl2sql_readonly WITH PASSWORD 'your_secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE your_database TO nl2sql_readonly;
GRANT USAGE ON SCHEMA public TO nl2sql_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nl2sql_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO nl2sql_readonly;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO nl2sql_readonly;
```

Then update your `.env` file:
```env
NEON_READONLY_CONNECTION_STRING=postgresql://nl2sql_readonly:your_secure_password@host/db?sslmode=require
```

## 🚦 Next Steps

1. ✅ **Load the sample data** (using one of the methods above)
2. ✅ **Verify the data** (run verification queries)
3. ✅ **Create read-only user** (for security)
4. ✅ **Update .env file** (with readonly connection string)
5. ✅ **Initialize vector store** (`python scripts/init_vector_store.py`)
6. ✅ **Test the app** (`streamlit run app.py`)

## 💡 Pro Tips

- **Keep the DBA connection** for your main admin account
- **Use readonly connection** for the NL2SQL app in production
- **The sample data is realistic** - it mimics a real e-commerce business
- **Try complex queries** - the system handles joins, aggregations, and time-based filters
- **Check audit logs** - See what SQL was generated for each question

## 🔄 Reset Database

To start fresh:

```sql
-- Drop all tables
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- Then re-run the sample_data.sql script
```

## ❓ Troubleshooting

### "Permission denied" error
- Make sure you're connected as the database owner
- Check that your user has CREATE TABLE permissions

### "Database doesn't exist"
- Create a database first in Neon console
- Use the connection string for that specific database

### Tables already exist
- Either drop them first (see Reset Database above)
- Or use a different database name

---

**Your database is now ready for testing! 🎉**

Try asking questions in natural language and watch the AI translate them to SQL!
