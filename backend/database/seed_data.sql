-- Seed data for e-commerce dataset
-- Inserts sample data into all tables

-- Clear existing data (for re-seeding)
TRUNCATE TABLE order_items CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE customers CASCADE;

-- Insert customers
INSERT INTO customers (name, email, city, country, phone) VALUES
('John Smith', 'john.smith@email.com', 'New York', 'USA', '555-0101'),
('Emily Johnson', 'emily.j@email.com', 'Los Angeles', 'USA', '555-0102'),
('Michael Brown', 'm.brown@email.com', 'Chicago', 'USA', '555-0103'),
('Sarah Davis', 'sarah.davis@email.com', 'Houston', 'USA', '555-0104'),
('David Wilson', 'd.wilson@email.com', 'Phoenix', 'USA', '555-0105'),
('Jessica Martinez', 'j.martinez@email.com', 'Philadelphia', 'USA', '555-0106'),
('Christopher Anderson', 'c.anderson@email.com', 'San Antonio', 'USA', '555-0107'),
('Amanda Taylor', 'a.taylor@email.com', 'San Diego', 'USA', '555-0108'),
('Matthew Thomas', 'm.thomas@email.com', 'Dallas', 'USA', '555-0109'),
('Ashley Jackson', 'ashley.j@email.com', 'San Jose', 'USA', '555-0110'),
('James White', 'james.white@email.com', 'Austin', 'USA', '555-0111'),
('Lauren Harris', 'lauren.h@email.com', 'Jacksonville', 'USA', '555-0112'),
('Robert Martin', 'r.martin@email.com', 'Fort Worth', 'USA', '555-0113'),
('Megan Thompson', 'megan.t@email.com', 'Columbus', 'USA', '555-0114'),
('Daniel Garcia', 'daniel.g@email.com', 'Charlotte', 'USA', '555-0115'),
('Nicole Rodriguez', 'nicole.r@email.com', 'San Francisco', 'USA', '555-0116'),
('William Lee', 'william.lee@email.com', 'Indianapolis', 'USA', '555-0117'),
('Stephanie Walker', 'stephanie.w@email.com', 'Seattle', 'USA', '555-0118'),
('Joseph Hall', 'joseph.hall@email.com', 'Denver', 'USA', '555-0119'),
('Rachel Young', 'rachel.y@email.com', 'Washington', 'USA', '555-0120');

-- Insert products
INSERT INTO products (name, category, price, stock_quantity, description) VALUES
('Laptop Pro 15"', 'Electronics', 1299.99, 50, 'High-performance laptop with 16GB RAM'),
('Wireless Mouse', 'Electronics', 29.99, 200, 'Ergonomic wireless mouse'),
('Mechanical Keyboard', 'Electronics', 149.99, 75, 'RGB mechanical keyboard'),
('USB-C Cable', 'Electronics', 19.99, 500, 'Fast charging USB-C cable'),
('Monitor 27" 4K', 'Electronics', 399.99, 30, 'Ultra HD 4K monitor'),
('Blue Jeans', 'Clothing', 59.99, 150, 'Classic fit blue jeans'),
('Cotton T-Shirt', 'Clothing', 24.99, 300, '100% cotton t-shirt'),
('Running Shoes', 'Clothing', 89.99, 100, 'Comfortable running shoes'),
('Winter Jacket', 'Clothing', 129.99, 80, 'Warm winter jacket'),
('Baseball Cap', 'Clothing', 19.99, 250, 'Adjustable baseball cap'),
('Coffee Maker', 'Home & Kitchen', 79.99, 60, 'Programmable coffee maker'),
('Blender', 'Home & Kitchen', 49.99, 90, 'High-speed blender'),
('Toaster', 'Home & Kitchen', 39.99, 120, '4-slice toaster'),
('Dinner Set', 'Home & Kitchen', 89.99, 40, '16-piece dinner set'),
('Bed Sheets', 'Home & Kitchen', 34.99, 200, 'Queen size bed sheets'),
('Mystery Novel', 'Books', 14.99, 500, 'Bestselling mystery novel'),
('Cookbook', 'Books', 24.99, 300, 'Professional cookbook'),
('Sci-Fi Novel', 'Books', 16.99, 400, 'Award-winning sci-fi novel'),
('History Book', 'Books', 19.99, 250, 'Comprehensive history book'),
('Children Book', 'Books', 12.99, 600, 'Illustrated children book');

-- Insert orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, '2024-01-15 10:30:00', 1329.98, 'completed', '123 Main St, New York, NY 10001'),
(2, '2024-01-16 14:20:00', 89.98, 'completed', '456 Oak Ave, Los Angeles, CA 90001'),
(3, '2024-01-17 09:15:00', 199.98, 'completed', '789 Pine Rd, Chicago, IL 60601'),
(1, '2024-01-18 11:45:00', 49.99, 'completed', '123 Main St, New York, NY 10001'),
(4, '2024-01-19 16:30:00', 179.97, 'completed', '321 Elm St, Houston, TX 77001'),
(5, '2024-01-20 08:00:00', 399.99, 'completed', '654 Maple Dr, Phoenix, AZ 85001'),
(6, '2024-01-21 13:20:00', 84.98, 'completed', '987 Cedar Ln, Philadelphia, PA 19101'),
(7, '2024-01-22 10:10:00', 149.99, 'completed', '147 Birch Way, San Antonio, TX 78201'),
(8, '2024-01-23 15:45:00', 129.99, 'completed', '258 Spruce St, San Diego, CA 92101'),
(9, '2024-01-24 09:30:00', 79.99, 'completed', '369 Willow Ave, Dallas, TX 75201'),
(10, '2024-01-25 12:00:00', 49.99, 'completed', '741 Ash Blvd, San Jose, CA 95101'),
(11, '2024-01-26 14:15:00', 199.98, 'completed', '852 Poplar Rd, Austin, TX 78701'),
(12, '2024-01-27 11:30:00', 34.99, 'completed', '963 Fir St, Jacksonville, FL 32201'),
(13, '2024-01-28 16:00:00', 89.99, 'completed', '159 Sycamore Dr, Fort Worth, TX 76101'),
(14, '2024-01-29 10:45:00', 149.99, 'completed', '357 Magnolia Ln, Columbus, OH 43201'),
(15, '2024-01-30 13:00:00', 24.99, 'completed', '468 Dogwood Way, Charlotte, NC 28201'),
(16, '2024-02-01 09:15:00', 1299.99, 'completed', '579 Redwood Ave, San Francisco, CA 94101'),
(17, '2024-02-02 15:30:00', 59.99, 'completed', '680 Sequoia Blvd, Indianapolis, IN 46201'),
(18, '2024-02-03 11:00:00', 89.99, 'completed', '791 Cypress Rd, Seattle, WA 98101'),
(19, '2024-02-04 14:45:00', 79.99, 'completed', '802 Hemlock St, Denver, CO 80201'),
(20, '2024-02-05 10:20:00', 49.99, 'completed', '913 Juniper Dr, Washington, DC 20001'),
(1, '2024-02-06 12:30:00', 149.99, 'pending', '123 Main St, New York, NY 10001'),
(3, '2024-02-07 08:45:00', 29.99, 'pending', '789 Pine Rd, Chicago, IL 60601'),
(5, '2024-02-08 16:20:00', 399.99, 'shipped', '654 Maple Dr, Phoenix, AZ 85001'),
(7, '2024-02-09 11:15:00', 19.99, 'shipped', '147 Birch Way, San Antonio, TX 78201'),
(9, '2024-02-10 13:50:00', 89.99, 'pending', '369 Willow Ave, Dallas, TX 75201');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, line_total) VALUES
-- Order 1 (customer 1)
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
-- Order 2 (customer 2)
(2, 8, 1, 89.99),
-- Order 3 (customer 3)
(3, 3, 1, 149.99),
(3, 4, 1, 19.99),
(3, 2, 1, 29.99),
-- Order 4 (customer 1)
(4, 12, 1, 49.99),
-- Order 5 (customer 4)
(5, 3, 1, 149.99),
(5, 2, 1, 29.99),
-- Order 6 (customer 5)
(6, 5, 1, 399.99),
-- Order 7 (customer 6)
(7, 7, 2, 49.98),
(7, 10, 1, 19.99),
(7, 16, 1, 14.99),
-- Order 8 (customer 7)
(8, 3, 1, 149.99),
-- Order 9 (customer 8)
(9, 9, 1, 129.99),
-- Order 10 (customer 9)
(10, 11, 1, 79.99),
-- Order 11 (customer 10)
(11, 12, 1, 49.99),
-- Order 12 (customer 11)
(12, 3, 1, 149.99),
(12, 2, 1, 29.99),
(12, 4, 1, 19.99),
-- Order 13 (customer 12)
(13, 15, 1, 34.99),
-- Order 14 (customer 13)
(14, 8, 1, 89.99),
-- Order 15 (customer 14)
(15, 3, 1, 149.99),
-- Order 16 (customer 15)
(16, 7, 1, 24.99),
-- Order 17 (customer 16)
(17, 1, 1, 1299.99),
-- Order 18 (customer 17)
(18, 6, 1, 59.99),
-- Order 19 (customer 18)
(19, 8, 1, 89.99),
-- Order 20 (customer 19)
(20, 11, 1, 79.99),
-- Order 21 (customer 20)
(21, 12, 1, 49.99),
-- Order 22 (customer 1)
(22, 3, 1, 149.99),
-- Order 23 (customer 3)
(23, 2, 1, 29.99),
-- Order 24 (customer 5)
(24, 5, 1, 399.99),
-- Order 25 (customer 7)
(25, 4, 1, 19.99),
-- Order 26 (customer 9)
(26, 11, 1, 79.99),
(26, 13, 1, 9.99);

-- Update order totals to match order_items (for accuracy)
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(oi.line_total), 0)
    FROM order_items oi
    WHERE oi.order_id = o.id
);

