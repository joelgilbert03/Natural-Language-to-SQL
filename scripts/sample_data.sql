-- ===================================================================
-- Sample E-Commerce Database Schema and Data
-- Perfect for testing the NL2SQL system!
-- ===================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- ===================================================================
-- 1. REGIONS TABLE
-- ===================================================================
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

INSERT INTO regions (region_name, country) VALUES
('North America', 'USA'),
('Europe', 'UK'),
('Asia Pacific', 'Singapore'),
('South America', 'Brazil'),
('Middle East', 'UAE');

-- ===================================================================
-- 2. CUSTOMERS TABLE
-- ===================================================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    region_id INTEGER REFERENCES regions(region_id),
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    loyalty_points INTEGER DEFAULT 0
);

INSERT INTO customers (first_name, last_name, email, region_id, signup_date, is_active, loyalty_points) VALUES
('John', 'Smith', 'john.smith@email.com', 1, '2023-01-15', true, 1250),
('Emma', 'Johnson', 'emma.j@email.com', 1, '2023-02-20', true, 2100),
('Michael', 'Williams', 'mike.w@email.com', 2, '2023-03-10', true, 850),
('Sophia', 'Brown', 'sophia.b@email.com', 2, '2023-04-05', true, 3200),
('James', 'Davis', 'james.d@email.com', 3, '2023-05-12', true, 1500),
('Olivia', 'Miller', 'olivia.m@email.com', 3, '2023-06-18', true, 950),
('Robert', 'Wilson', 'robert.w@email.com', 1, '2023-07-22', false, 200),
('Ava', 'Moore', 'ava.m@email.com', 4, '2023-08-14', true, 1750),
('William', 'Taylor', 'william.t@email.com', 4, '2023-09-09', true, 4100),
('Isabella', 'Anderson', 'isabella.a@email.com', 5, '2023-10-03', true, 2800),
('David', 'Thomas', 'david.t@email.com', 5, '2023-11-11', true, 650),
('Mia', 'Jackson', 'mia.j@email.com', 2, '2023-12-05', true, 1900),
('Joseph', 'White', 'joseph.w@email.com', 1, '2024-01-08', true, 3500),
('Charlotte', 'Harris', 'charlotte.h@email.com', 3, '2024-02-14', true, 1100),
('Daniel', 'Martin', 'daniel.m@email.com', 2, '2024-03-19', false, 50);

-- ===================================================================
-- 3. CATEGORIES TABLE
-- ===================================================================
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT
);

INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Home & Garden', 'Home improvement and garden supplies'),
('Books', 'Physical and digital books'),
('Sports', 'Sports equipment and gear'),
('Toys', 'Toys and games for all ages');

-- ===================================================================
-- 4. PRODUCTS TABLE
-- ===================================================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category_id INTEGER REFERENCES categories(category_id),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL,
    is_featured BOOLEAN DEFAULT false,
    created_date DATE NOT NULL
);

INSERT INTO products (product_name, category_id, price, stock_quantity, is_featured, created_date) VALUES
-- Electronics
('Wireless Headphones Pro', 1, 199.99, 45, true, '2023-01-10'),
('Smart Watch Series 5', 1, 299.99, 32, true, '2023-02-15'),
('Laptop Stand Aluminum', 1, 49.99, 120, false, '2023-03-20'),
('USB-C Hub 7-in-1', 1, 39.99, 85, false, '2023-04-12'),
('Mechanical Keyboard RGB', 1, 129.99, 28, true, '2023-05-08'),

-- Clothing
('Cotton T-Shirt Pack (3)', 2, 29.99, 200, false, '2023-01-25'),
('Denim Jeans Classic', 2, 59.99, 150, false, '2023-02-18'),
('Running Shoes Premium', 2, 89.99, 75, true, '2023-03-22'),
('Winter Jacket Insulated', 2, 149.99, 45, true, '2023-09-01'),
('Baseball Cap Adjustable', 2, 19.99, 180, false, '2023-04-10'),

-- Home & Garden
('LED Desk Lamp', 3, 34.99, 95, false, '2023-01-30'),
('Plant Pot Set (5)', 3, 24.99, 160, false, '2023-03-15'),
('Kitchen Knife Set', 3, 79.99, 55, true, '2023-02-20'),
('Bath Towel Set Premium', 3, 44.99, 110, false, '2023-04-05'),
('Garden Tool Kit', 3, 69.99, 40, false, '2023-05-12'),

-- Books
('Python Programming Guide', 4, 39.99, 88, true, '2023-02-01'),
('Mystery Novel Bestseller', 4, 14.99, 250, false, '2023-03-10'),
('Cook Book International', 4, 29.99, 120, false, '2023-04-15'),
('Self-Help Success Book', 4, 19.99, 175, false, '2023-05-20'),

-- Sports
('Yoga Mat Premium', 5, 34.99, 95, false, '2023-02-25'),
('Dumbbells Set 20lb', 5, 89.99, 60, true, '2023-03-18'),
('Tennis Racket Pro', 5, 129.99, 35, true, '2023-04-22'),
('Basketball Official Size', 5, 24.99, 140, false, '2023-05-15'),

-- Toys
('Building Blocks Set 500pc', 6, 49.99, 85, true, '2023-03-01'),
('Remote Control Car', 6, 69.99, 42, false, '2023-04-08'),
('Board Game Family Pack', 6, 34.99, 110, false, '2023-05-05');

-- ===================================================================
-- 5. ORDERS TABLE
-- ===================================================================
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address TEXT
);

INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address) VALUES
-- Recent orders (last 30 days)
(1, '2024-11-20 10:30:00', 'delivered', 249.98, '123 Main St, New York, NY'),
(2, '2024-11-19 14:15:00', 'delivered', 129.99, '456 Oak Ave, Los Angeles, CA'),
(3, '2024-11-18 09:45:00', 'shipped', 89.99, '789 Pine Rd, London, UK'),
(4, '2024-11-17 16:20:00', 'delivered', 199.99, '321 Elm St, Manchester, UK'),
(5, '2024-11-16 11:00:00', 'processing', 349.97, '654 Maple Dr, Singapore'),

-- Last week
(6, '2024-11-15 13:30:00', 'delivered', 79.99, '987 Cedar Ln, Tokyo, Japan'),
(7, '2024-11-14 08:15:00', 'cancelled', 44.99, '147 Birch Ave, New York, NY'),
(8, '2024-11-13 15:45:00', 'delivered', 229.97, '258 Spruce St, São Paulo, Brazil'),
(9, '2024-11-12 10:00:00', 'delivered', 559.96, '369 Willow Rd, Rio de Janeiro, Brazil'),
(10, '2024-11-11 12:30:00', 'shipped', 149.99, '741 Ash Ct, Dubai, UAE'),

-- Last month
(11, '2024-10-28 14:20:00', 'delivered', 89.99, '852 Poplar Dr, Abu Dhabi, UAE'),
(1, '2024-10-25 16:45:00', 'delivered', 299.98, '123 Main St, New York, NY'),
(2, '2024-10-22 09:30:00', 'delivered', 159.98, '456 Oak Ave, Los Angeles, CA'),
(13, '2024-10-20 11:15:00', 'delivered', 449.97, '963 Beach Rd, Miami, FL'),
(3, '2024-10-18 13:00:00', 'delivered', 249.99, '789 Pine Rd, London, UK'),

-- Older orders
(4, '2024-09-15 10:00:00', 'delivered', 319.98, '321 Elm St, Manchester, UK'),
(5, '2024-09-10 14:30:00', 'delivered', 199.99, '654 Maple Dr, Singapore'),
(12, '2024-09-05 16:15:00', 'delivered', 129.99, '159 Lake St, Paris, France'),
(14, '2024-08-28 11:45:00', 'delivered', 279.97, '357 River Ave, Berlin, Germany'),
(6, '2024-08-20 09:20:00', 'delivered', 89.99, '987 Cedar Ln, Tokyo, Japan');

-- ===================================================================
-- 6. ORDER_ITEMS TABLE
-- ===================================================================
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- Order 1 items
(1, 1, 1, 199.99, 199.99),
(1, 4, 1, 49.99, 49.99),

-- Order 2 items
(2, 5, 1, 129.99, 129.99),

-- Order 3 items
(3, 8, 1, 89.99, 89.99),

-- Order 4 items
(4, 1, 1, 199.99, 199.99),

-- Order 5 items
(5, 2, 1, 299.99, 299.99),
(5, 4, 1, 49.99, 49.99),

-- Order 6 items
(6, 13, 1, 79.99, 79.99),

-- Order 7 items (cancelled)
(7, 14, 1, 44.99, 44.99),

-- Order 8 items
(8, 16, 1, 39.99, 39.99),
(8, 17, 2, 14.99, 29.98),
(8, 20, 5, 34.99, 174.95),

-- Order 9 items
(9, 2, 1, 299.99, 299.99),
(9, 21, 1, 89.99, 89.99),
(9, 22, 2, 129.99, 259.98),

-- Order 10 items
(10, 9, 1, 149.99, 149.99),

-- Order 11 items
(11, 8, 1, 89.99, 89.99),

-- Order 12 items
(12, 1, 1, 199.99, 199.99),
(12, 5, 1, 129.99, 129.99),

-- Order 13 items
(13, 6, 2, 29.99, 59.98),
(13, 7, 1, 59.99, 59.99),
(13, 10, 1, 19.99, 19.99),

-- Order 14 items
(14, 2, 1, 299.99, 299.99),
(14, 3, 1, 49.99, 49.99),
(14, 24, 2, 24.99, 49.98),

-- Order 15 items
(15, 13, 1, 79.99, 79.99),
(15, 15, 1, 69.99, 69.99),

-- Order 16 items
(16, 21, 2, 89.99, 179.98),
(16, 8, 1, 89.99, 89.99),
(16, 10, 1, 19.99, 19.99),

-- Order 17 items
(17, 1, 1, 199.99, 199.99),

-- Order 18 items
(18, 5, 1, 129.99, 129.99),

-- Order 19 items
(19, 22, 1, 129.99, 129.99),
(19, 8, 1, 89.99, 89.99),
(19, 16, 1, 39.99, 39.99),

-- Order 20 items
(20, 8, 1, 89.99, 89.99);

-- ===================================================================
-- CREATE INDEXES FOR BETTER QUERY PERFORMANCE
-- ===================================================================
CREATE INDEX idx_customers_region ON customers(region_id);
CREATE INDEX idx_customers_active ON customers(is_active);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- ===================================================================
-- CREATE VIEWS FOR COMMON QUERIES
-- ===================================================================

-- Sales summary view
CREATE OR REPLACE VIEW sales_summary AS
SELECT 
    c.category_name,
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(oi.quantity) as units_sold,
    SUM(oi.subtotal) as total_revenue
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status != 'cancelled'
GROUP BY c.category_name;

-- Customer lifetime value view
CREATE OR REPLACE VIEW customer_lifetime_value AS
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name as customer_name,
    c.email,
    r.region_name,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status != 'cancelled'
LEFT JOIN regions r ON c.region_id = r.region_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, r.region_name;

-- ===================================================================
-- GRANT PERMISSIONS (for read-only user)
-- ===================================================================
-- Run these commands separately after creating your readonly user:
-- 
-- GRANT CONNECT ON DATABASE your_database TO readonly_user;
-- GRANT USAGE ON SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;

-- ===================================================================
-- VERIFICATION QUERIES
-- ===================================================================

-- Check row counts
SELECT 'regions' as table_name, COUNT(*) as row_count FROM regions
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;

-- Show sample data
SELECT 'Sample Customers:' as info;
SELECT customer_id, first_name, last_name, email FROM customers LIMIT 5;

SELECT 'Sample Products:' as info;
SELECT product_id, product_name, price FROM products LIMIT 5;

SELECT 'Sample Orders:' as info;
SELECT order_id, customer_id, order_date, status, total_amount FROM orders LIMIT 5;

SELECT 'Sample Views:' as info;
SELECT * FROM sales_summary;

-- ===================================================================
-- DONE! Your database is ready for NL2SQL testing!
-- ===================================================================
