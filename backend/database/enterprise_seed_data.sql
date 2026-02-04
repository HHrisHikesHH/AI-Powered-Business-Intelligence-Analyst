-- ============================================================================
-- ENTERPRISE DATABASE SEED DATA
-- Comprehensive realistic data for all 40+ tables
-- ============================================================================

-- Clear existing data (in reverse dependency order)
TRUNCATE TABLE event_attendees CASCADE;
TRUNCATE TABLE campaign_leads CASCADE;
TRUNCATE TABLE events CASCADE;
TRUNCATE TABLE marketing_campaigns CASCADE;
TRUNCATE TABLE knowledge_base_articles CASCADE;
TRUNCATE TABLE ticket_comments CASCADE;
TRUNCATE TABLE support_tickets CASCADE;
TRUNCATE TABLE time_entries CASCADE;
TRUNCATE TABLE project_tasks CASCADE;
TRUNCATE TABLE projects CASCADE;
TRUNCATE TABLE inventory_movements CASCADE;
TRUNCATE TABLE purchase_order_items CASCADE;
TRUNCATE TABLE purchase_orders CASCADE;
TRUNCATE TABLE inventory CASCADE;
TRUNCATE TABLE warehouses CASCADE;
TRUNCATE TABLE suppliers CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE product_categories CASCADE;
TRUNCATE TABLE quote_line_items CASCADE;
TRUNCATE TABLE quotes CASCADE;
TRUNCATE TABLE sales_order_items CASCADE;
TRUNCATE TABLE sales_orders CASCADE;
TRUNCATE TABLE opportunities CASCADE;
TRUNCATE TABLE leads CASCADE;
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE budgets CASCADE;
TRUNCATE TABLE payments CASCADE;
TRUNCATE TABLE invoice_line_items CASCADE;
TRUNCATE TABLE invoices CASCADE;
TRUNCATE TABLE general_ledger CASCADE;
TRUNCATE TABLE financial_periods CASCADE;
TRUNCATE TABLE chart_of_accounts CASCADE;
TRUNCATE TABLE performance_reviews CASCADE;
TRUNCATE TABLE leave_requests CASCADE;
TRUNCATE TABLE attendance CASCADE;
TRUNCATE TABLE employee_skills CASCADE;
TRUNCATE TABLE employees CASCADE;
TRUNCATE TABLE job_positions CASCADE;
TRUNCATE TABLE departments CASCADE;

-- ============================================================================
-- DEPARTMENTS
-- ============================================================================
INSERT INTO departments (code, name, description, location) VALUES
('EXEC', 'Executive', 'C-Suite and executive management', 'HQ Floor 10'),
('HR', 'Human Resources', 'HR operations, recruitment, and employee relations', 'HQ Floor 5'),
('IT', 'Information Technology', 'IT infrastructure, development, and support', 'HQ Floor 7'),
('FIN', 'Finance', 'Accounting, budgeting, and financial planning', 'HQ Floor 6'),
('SALES', 'Sales', 'Sales operations and account management', 'HQ Floor 4'),
('MKTG', 'Marketing', 'Marketing campaigns and brand management', 'HQ Floor 3'),
('OPS', 'Operations', 'Operations and supply chain management', 'HQ Floor 2'),
('SUPP', 'Customer Support', 'Customer service and technical support', 'HQ Floor 1'),
('RND', 'Research & Development', 'Product development and innovation', 'HQ Floor 8'),
('LEGAL', 'Legal', 'Legal affairs and compliance', 'HQ Floor 9');

-- ============================================================================
-- JOB POSITIONS
-- ============================================================================
INSERT INTO job_positions (title, code, department_id, min_salary, max_salary, employment_type) VALUES
('CEO', 'CEO', 1, 200000, 500000, 'full-time'),
('CFO', 'CFO', 1, 180000, 400000, 'full-time'),
('CTO', 'CTO', 1, 180000, 400000, 'full-time'),
('HR Director', 'HR-DIR', 2, 120000, 200000, 'full-time'),
('HR Manager', 'HR-MGR', 2, 80000, 120000, 'full-time'),
('HR Specialist', 'HR-SPEC', 2, 50000, 75000, 'full-time'),
('IT Director', 'IT-DIR', 3, 140000, 220000, 'full-time'),
('Software Engineer', 'IT-ENG', 3, 90000, 150000, 'full-time'),
('DevOps Engineer', 'IT-DEVOPS', 3, 95000, 160000, 'full-time'),
('IT Support Specialist', 'IT-SUPP', 3, 45000, 70000, 'full-time'),
('Finance Director', 'FIN-DIR', 4, 130000, 210000, 'full-time'),
('Accountant', 'FIN-ACC', 4, 55000, 85000, 'full-time'),
('Financial Analyst', 'FIN-ANAL', 4, 65000, 95000, 'full-time'),
('Sales Director', 'SALES-DIR', 5, 120000, 250000, 'full-time'),
('Sales Manager', 'SALES-MGR', 5, 80000, 150000, 'full-time'),
('Sales Representative', 'SALES-REP', 5, 50000, 120000, 'full-time'),
('Marketing Director', 'MKTG-DIR', 6, 110000, 200000, 'full-time'),
('Marketing Manager', 'MKTG-MGR', 6, 75000, 130000, 'full-time'),
('Marketing Specialist', 'MKTG-SPEC', 6, 50000, 80000, 'full-time'),
('Operations Director', 'OPS-DIR', 7, 115000, 190000, 'full-time'),
('Operations Manager', 'OPS-MGR', 7, 70000, 110000, 'full-time'),
('Warehouse Manager', 'OPS-WH', 7, 55000, 85000, 'full-time'),
('Support Manager', 'SUPP-MGR', 8, 65000, 100000, 'full-time'),
('Support Specialist', 'SUPP-SPEC', 8, 40000, 60000, 'full-time'),
('R&D Director', 'RND-DIR', 9, 140000, 230000, 'full-time'),
('Product Manager', 'RND-PM', 9, 90000, 140000, 'full-time'),
('Research Scientist', 'RND-SCI', 9, 85000, 130000, 'full-time'),
('Legal Counsel', 'LEGAL-COUN', 10, 110000, 180000, 'full-time');

-- ============================================================================
-- EMPLOYEES
-- ============================================================================
INSERT INTO employees (employee_number, first_name, last_name, email, phone, date_of_birth, hire_date, position_id, manager_id, salary, city, state, country, status) VALUES
('EMP001', 'John', 'Anderson', 'john.anderson@company.com', '555-0101', '1975-03-15', '2010-01-15', 1, NULL, 350000, 'New York', 'NY', 'USA', 'active'),
('EMP002', 'Sarah', 'Mitchell', 'sarah.mitchell@company.com', '555-0102', '1980-07-22', '2011-03-01', 2, 1, 280000, 'New York', 'NY', 'USA', 'active'),
('EMP003', 'Michael', 'Chen', 'michael.chen@company.com', '555-0103', '1978-11-08', '2011-05-15', 3, 1, 290000, 'San Francisco', 'CA', 'USA', 'active'),
('EMP004', 'Emily', 'Rodriguez', 'emily.rodriguez@company.com', '555-0104', '1985-02-14', '2012-06-01', 4, 1, 150000, 'Chicago', 'IL', 'USA', 'active'),
('EMP005', 'David', 'Kim', 'david.kim@company.com', '555-0105', '1987-09-30', '2013-01-15', 5, 4, 95000, 'Chicago', 'IL', 'USA', 'active'),
('EMP006', 'Jessica', 'Taylor', 'jessica.taylor@company.com', '555-0106', '1990-04-18', '2014-03-01', 6, 5, 62000, 'Chicago', 'IL', 'USA', 'active'),
('EMP007', 'Robert', 'Williams', 'robert.williams@company.com', '555-0107', '1982-12-05', '2012-08-15', 7, 3, 180000, 'Seattle', 'WA', 'USA', 'active'),
('EMP008', 'Amanda', 'Brown', 'amanda.brown@company.com', '555-0108', '1988-06-20', '2015-01-10', 8, 7, 120000, 'Seattle', 'WA', 'USA', 'active'),
('EMP009', 'Christopher', 'Davis', 'christopher.davis@company.com', '555-0109', '1991-01-25', '2016-07-01', 8, 7, 110000, 'Seattle', 'WA', 'USA', 'active'),
('EMP010', 'Lauren', 'Miller', 'lauren.miller@company.com', '555-0110', '1989-08-12', '2015-09-15', 9, 7, 125000, 'Austin', 'TX', 'USA', 'active'),
('EMP011', 'Daniel', 'Wilson', 'daniel.wilson@company.com', '555-0111', '1986-03-28', '2014-11-01', 10, 7, 55000, 'Austin', 'TX', 'USA', 'active'),
('EMP012', 'Nicole', 'Moore', 'nicole.moore@company.com', '555-0112', '1984-10-15', '2013-02-15', 11, 2, 170000, 'Boston', 'MA', 'USA', 'active'),
('EMP013', 'William', 'Jackson', 'william.jackson@company.com', '555-0113', '1989-05-07', '2015-04-01', 12, 12, 70000, 'Boston', 'MA', 'USA', 'active'),
('EMP014', 'Stephanie', 'White', 'stephanie.white@company.com', '555-0114', '1992-11-22', '2017-06-15', 13, 12, 80000, 'Boston', 'MA', 'USA', 'active'),
('EMP015', 'Joseph', 'Harris', 'joseph.harris@company.com', '555-0115', '1983-07-04', '2013-05-01', 14, 1, 180000, 'Los Angeles', 'CA', 'USA', 'active'),
('EMP016', 'Rachel', 'Martin', 'rachel.martin@company.com', '555-0116', '1987-02-19', '2014-08-15', 15, 15, 110000, 'Los Angeles', 'CA', 'USA', 'active'),
('EMP017', 'Matthew', 'Thompson', 'matthew.thompson@company.com', '555-0117', '1990-09-11', '2016-01-10', 16, 16, 75000, 'Los Angeles', 'CA', 'USA', 'active'),
('EMP018', 'Ashley', 'Garcia', 'ashley.garcia@company.com', '555-0118', '1991-12-28', '2017-03-01', 16, 16, 72000, 'Phoenix', 'AZ', 'USA', 'active'),
('EMP019', 'James', 'Martinez', 'james.martinez@company.com', '555-0119', '1985-04-03', '2014-10-01', 17, 1, 150000, 'Denver', 'CO', 'USA', 'active'),
('EMP020', 'Megan', 'Robinson', 'megan.robinson@company.com', '555-0120', '1988-08-17', '2015-12-15', 18, 19, 95000, 'Denver', 'CO', 'USA', 'active'),
('EMP021', 'Ryan', 'Clark', 'ryan.clark@company.com', '555-0121', '1992-01-30', '2018-02-01', 19, 20, 65000, 'Denver', 'CO', 'USA', 'active'),
('EMP022', 'Olivia', 'Lewis', 'olivia.lewis@company.com', '555-0122', '1986-06-14', '2014-07-01', 20, 1, 155000, 'Houston', 'TX', 'USA', 'active'),
('EMP023', 'Andrew', 'Walker', 'andrew.walker@company.com', '555-0123', '1989-10-27', '2016-04-15', 21, 22, 90000, 'Houston', 'TX', 'USA', 'active'),
('EMP024', 'Sophia', 'Hall', 'sophia.hall@company.com', '555-0124', '1990-03-09', '2017-08-01', 22, 23, 70000, 'Houston', 'TX', 'USA', 'active'),
('EMP025', 'Benjamin', 'Allen', 'benjamin.allen@company.com', '555-0125', '1987-07-23', '2015-05-15', 23, 1, 80000, 'Miami', 'FL', 'USA', 'active'),
('EMP026', 'Isabella', 'Young', 'isabella.young@company.com', '555-0126', '1991-11-05', '2018-01-10', 24, 25, 50000, 'Miami', 'FL', 'USA', 'active'),
('EMP027', 'Ethan', 'King', 'ethan.king@company.com', '555-0127', '1993-02-18', '2019-06-01', 24, 25, 48000, 'Miami', 'FL', 'USA', 'active'),
('EMP028', 'Ava', 'Wright', 'ava.wright@company.com', '555-0128', '1984-09-01', '2013-09-15', 25, 3, 185000, 'San Diego', 'CA', 'USA', 'active'),
('EMP029', 'Alexander', 'Lopez', 'alexander.lopez@company.com', '555-0129', '1988-01-14', '2015-11-01', 26, 28, 115000, 'San Diego', 'CA', 'USA', 'active'),
('EMP030', 'Charlotte', 'Hill', 'charlotte.hill@company.com', '555-0130', '1990-05-28', '2017-04-15', 27, 28, 105000, 'San Diego', 'CA', 'USA', 'active');

-- Update department managers
UPDATE departments SET manager_id = 1 WHERE code = 'EXEC';
UPDATE departments SET manager_id = 4 WHERE code = 'HR';
UPDATE departments SET manager_id = 7 WHERE code = 'IT';
UPDATE departments SET manager_id = 12 WHERE code = 'FIN';
UPDATE departments SET manager_id = 15 WHERE code = 'SALES';
UPDATE departments SET manager_id = 19 WHERE code = 'MKTG';
UPDATE departments SET manager_id = 22 WHERE code = 'OPS';
UPDATE departments SET manager_id = 25 WHERE code = 'SUPP';
UPDATE departments SET manager_id = 28 WHERE code = 'RND';

-- ============================================================================
-- EMPLOYEE SKILLS
-- ============================================================================
INSERT INTO employee_skills (employee_id, skill_name, proficiency_level, certified) VALUES
(8, 'Python', 'expert', TRUE),
(8, 'JavaScript', 'advanced', TRUE),
(8, 'React', 'advanced', TRUE),
(9, 'Java', 'expert', TRUE),
(9, 'Spring Boot', 'advanced', TRUE),
(9, 'Microservices', 'advanced', TRUE),
(10, 'AWS', 'expert', TRUE),
(10, 'Docker', 'advanced', TRUE),
(10, 'Kubernetes', 'advanced', TRUE),
(11, 'Windows Support', 'advanced', FALSE),
(11, 'Linux Support', 'intermediate', FALSE),
(13, 'QuickBooks', 'advanced', TRUE),
(13, 'Excel', 'expert', FALSE),
(14, 'Financial Modeling', 'advanced', TRUE),
(14, 'SQL', 'advanced', FALSE),
(17, 'Salesforce', 'advanced', TRUE),
(17, 'CRM', 'advanced', FALSE),
(18, 'Salesforce', 'intermediate', FALSE),
(18, 'CRM', 'intermediate', FALSE),
(20, 'Google Analytics', 'advanced', TRUE),
(20, 'SEO', 'advanced', TRUE),
(21, 'Social Media Marketing', 'advanced', FALSE),
(29, 'Product Management', 'advanced', TRUE),
(29, 'Agile', 'expert', TRUE),
(30, 'Data Science', 'advanced', TRUE),
(30, 'Machine Learning', 'intermediate', TRUE);

-- ============================================================================
-- ATTENDANCE (Sample for last 30 days)
-- ============================================================================
-- Note: In production, this would be generated programmatically
INSERT INTO attendance (employee_id, date, check_in_time, check_out_time, total_hours, status) VALUES
(1, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE - INTERVAL '1 day' + TIME '09:00:00', CURRENT_DATE - INTERVAL '1 day' + TIME '17:00:00', 8.0, 'present'),
(2, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE - INTERVAL '1 day' + TIME '08:45:00', CURRENT_DATE - INTERVAL '1 day' + TIME '17:30:00', 8.75, 'present'),
(3, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE - INTERVAL '1 day' + TIME '09:15:00', CURRENT_DATE - INTERVAL '1 day' + TIME '18:00:00', 8.75, 'present');

-- ============================================================================
-- PRODUCT CATEGORIES
-- ============================================================================
INSERT INTO product_categories (code, name, description) VALUES
('ELEC', 'Electronics', 'Electronic devices and components'),
('SOFT', 'Software', 'Software licenses and subscriptions'),
('SERV', 'Services', 'Professional and consulting services'),
('OFF', 'Office Supplies', 'Office equipment and supplies'),
('FURN', 'Furniture', 'Office furniture and fixtures');

-- ============================================================================
-- PRODUCTS
-- ============================================================================
INSERT INTO products (sku, name, description, category_id, unit_of_measure, standard_cost, list_price, weight, reorder_point, reorder_quantity) VALUES
('LAPTOP-PRO-15', 'Laptop Pro 15"', 'High-performance business laptop', 1, 'each', 800.00, 1299.99, 2.5, 10, 20),
('LAPTOP-STD-14', 'Laptop Standard 14"', 'Standard business laptop', 1, 'each', 500.00, 899.99, 2.0, 15, 30),
('MONITOR-27-4K', 'Monitor 27" 4K', 'Ultra HD 4K monitor', 1, 'each', 250.00, 399.99, 8.0, 5, 10),
('KEYBOARD-MECH', 'Mechanical Keyboard', 'RGB mechanical keyboard', 1, 'each', 60.00, 149.99, 1.2, 20, 50),
('MOUSE-WIRELESS', 'Wireless Mouse', 'Ergonomic wireless mouse', 1, 'each', 12.00, 29.99, 0.1, 30, 100),
('SOFTWARE-CRM', 'CRM Software License', 'Annual CRM software license', 2, 'each', 0.00, 999.99, 0.0, 0, 0),
('SOFTWARE-ERP', 'ERP Software License', 'Annual ERP software license', 2, 'each', 0.00, 4999.99, 0.0, 0, 0),
('CONSULT-HR', 'HR Consulting', 'HR consulting services per hour', 3, 'hour', 0.00, 150.00, 0.0, 0, 0),
('CONSULT-IT', 'IT Consulting', 'IT consulting services per hour', 3, 'hour', 0.00, 200.00, 0.0, 0, 0),
('CONSULT-FIN', 'Financial Consulting', 'Financial consulting services per hour', 3, 'hour', 0.00, 175.00, 0.0, 0, 0),
('DESK-EXEC', 'Executive Desk', 'Premium executive desk', 5, 'each', 400.00, 799.99, 50.0, 2, 5),
('CHAIR-ERG', 'Ergonomic Chair', 'Premium ergonomic office chair', 5, 'each', 200.00, 449.99, 15.0, 5, 10),
('PAPER-A4', 'A4 Paper Ream', 'Standard A4 paper ream', 4, 'each', 3.00, 8.99, 2.5, 50, 100),
('PEN-BALL', 'Ballpoint Pen', 'Standard ballpoint pen', 4, 'each', 0.50, 2.99, 0.01, 200, 500);

-- ============================================================================
-- SUPPLIERS
-- ============================================================================
INSERT INTO suppliers (supplier_code, company_name, contact_name, email, phone, payment_terms, city, state, country) VALUES
('SUP001', 'TechSupply Inc', 'Robert Johnson', 'robert@techsupply.com', '555-2001', 'Net 30', 'San Francisco', 'CA', 'USA'),
('SUP002', 'Office Depot Pro', 'Mary Smith', 'mary@officedepot.com', '555-2002', 'Net 15', 'Atlanta', 'GA', 'USA'),
('SUP003', 'Furniture Plus', 'David Lee', 'david@furnitureplus.com', '555-2003', 'Net 30', 'Chicago', 'IL', 'USA'),
('SUP004', 'Software Solutions', 'Jennifer Brown', 'jennifer@softwaresol.com', '555-2004', 'Net 30', 'Seattle', 'WA', 'USA');

-- ============================================================================
-- WAREHOUSES
-- ============================================================================
INSERT INTO warehouses (code, name, address_line1, city, state, postal_code, country, manager_id) VALUES
('WH001', 'Main Warehouse', '100 Industrial Blvd', 'Chicago', 'IL', '60601', 'USA', 24),
('WH002', 'West Coast Distribution', '200 Commerce Way', 'Los Angeles', 'CA', '90001', 'USA', 24),
('WH003', 'East Coast Distribution', '300 Logistics Drive', 'New York', 'NY', '10001', 'USA', 24);

-- ============================================================================
-- INVENTORY
-- ============================================================================
INSERT INTO inventory (product_id, warehouse_id, quantity_on_hand, reorder_point) VALUES
(1, 1, 25, 10),
(1, 2, 15, 10),
(2, 1, 40, 15),
(2, 2, 20, 15),
(3, 1, 12, 5),
(3, 2, 8, 5),
(4, 1, 60, 20),
(5, 1, 150, 30),
(5, 2, 100, 30),
(11, 1, 8, 2),
(11, 2, 5, 2),
(12, 1, 15, 5),
(12, 2, 10, 5),
(13, 1, 200, 50),
(13, 2, 150, 50),
(14, 1, 1000, 200);

-- ============================================================================
-- CUSTOMERS
-- ============================================================================
INSERT INTO customers (customer_code, company_name, contact_first_name, contact_last_name, email, phone, industry, customer_type, status, credit_limit, assigned_account_manager_id) VALUES
('CUST001', 'Acme Corporation', 'John', 'Smith', 'john.smith@acme.com', '555-3001', 'Manufacturing', 'enterprise', 'active', 100000.00, 16),
('CUST002', 'TechStart Solutions', 'Sarah', 'Johnson', 'sarah@techstart.com', '555-3002', 'Technology', 'smb', 'active', 50000.00, 17),
('CUST003', 'Global Industries', 'Michael', 'Brown', 'michael@globalind.com', '555-3003', 'Manufacturing', 'enterprise', 'active', 200000.00, 16),
('CUST004', 'Digital Services Co', 'Emily', 'Davis', 'emily@digitalservices.com', '555-3004', 'Services', 'smb', 'active', 30000.00, 18),
('CUST005', 'Retail Plus Inc', 'David', 'Wilson', 'david@retailplus.com', '555-3005', 'Retail', 'enterprise', 'active', 150000.00, 16),
('CUST006', 'Innovation Labs', 'Jessica', 'Martinez', 'jessica@innovationlabs.com', '555-3006', 'Technology', 'smb', 'active', 40000.00, 17),
('CUST007', 'Healthcare Systems', 'Robert', 'Anderson', 'robert@healthcare.com', '555-3007', 'Healthcare', 'enterprise', 'active', 180000.00, 16),
('CUST008', 'Finance First', 'Amanda', 'Taylor', 'amanda@financefirst.com', '555-3008', 'Financial Services', 'smb', 'active', 35000.00, 18),
('CUST009', 'Education Solutions', 'Christopher', 'Thomas', 'chris@edusolutions.com', '555-3009', 'Education', 'smb', 'active', 25000.00, 17),
('CUST010', 'Energy Corp', 'Lauren', 'Jackson', 'lauren@energycorp.com', '555-3010', 'Energy', 'enterprise', 'active', 250000.00, 16);

-- ============================================================================
-- LEADS
-- ============================================================================
INSERT INTO leads (lead_number, first_name, last_name, company_name, email, phone, industry, lead_source, lead_status, estimated_value, assigned_to) VALUES
('LEAD001', 'Mark', 'Thompson', 'Future Tech', 'mark@futuretech.com', '555-4001', 'Technology', 'website', 'qualified', 50000.00, 17),
('LEAD002', 'Lisa', 'White', 'Smart Solutions', 'lisa@smartsolutions.com', '555-4002', 'Services', 'referral', 'contacted', 30000.00, 18),
('LEAD003', 'Paul', 'Harris', 'NextGen Systems', 'paul@nextgen.com', '555-4003', 'Technology', 'trade_show', 'new', 75000.00, 17),
('LEAD004', 'Karen', 'Martin', 'Business Partners', 'karen@businesspartners.com', '555-4004', 'Services', 'social_media', 'contacted', 20000.00, 18);

-- ============================================================================
-- OPPORTUNITIES
-- ============================================================================
INSERT INTO opportunities (opportunity_number, name, customer_id, lead_id, stage, probability_percent, estimated_value, expected_close_date, assigned_to) VALUES
('OPP001', 'Acme Corp - ERP Implementation', 1, NULL, 'negotiation', 75, 150000.00, CURRENT_DATE + INTERVAL '30 days', 16),
('OPP002', 'TechStart - CRM License', 2, NULL, 'proposal', 60, 50000.00, CURRENT_DATE + INTERVAL '45 days', 17),
('OPP003', 'Global Industries - Infrastructure Upgrade', 3, NULL, 'qualification', 40, 200000.00, CURRENT_DATE + INTERVAL '60 days', 16),
('OPP004', 'Future Tech - New Customer', NULL, 1, 'qualification', 30, 50000.00, CURRENT_DATE + INTERVAL '90 days', 17);

-- ============================================================================
-- SALES ORDERS
-- ============================================================================
INSERT INTO sales_orders (order_number, customer_id, opportunity_id, order_date, required_date, status, subtotal, tax_amount, total_amount, sales_rep_id) VALUES
('SO001', 1, NULL, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE - INTERVAL '10 days', 'delivered', 50000.00, 4000.00, 54000.00, 16),
('SO002', 2, NULL, CURRENT_DATE - INTERVAL '20 days', CURRENT_DATE + INTERVAL '10 days', 'shipped', 25000.00, 2000.00, 27000.00, 17),
('SO003', 3, NULL, CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '15 days', 'in_progress', 75000.00, 6000.00, 81000.00, 16),
('SO004', 4, NULL, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '25 days', 'confirmed', 15000.00, 1200.00, 16200.00, 18);

-- ============================================================================
-- SALES ORDER ITEMS
-- ============================================================================
INSERT INTO sales_order_items (order_id, line_number, product_id, description, quantity, unit_price, line_total) VALUES
(1, 1, 7, 'ERP Software License', 10, 4999.99, 49999.90),
(2, 1, 6, 'CRM Software License', 25, 999.99, 24999.75),
(3, 1, 1, 'Laptop Pro 15"', 50, 1299.99, 64999.50),
(3, 2, 3, 'Monitor 27" 4K', 25, 399.99, 9999.75),
(4, 1, 8, 'HR Consulting', 100, 150.00, 15000.00);

-- ============================================================================
-- INVOICES
-- ============================================================================
INSERT INTO invoices (invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, total_amount, status, created_by) VALUES
('INV001', 1, CURRENT_DATE - INTERVAL '25 days', CURRENT_DATE - INTERVAL '5 days', 50000.00, 4000.00, 54000.00, 'paid', 13),
('INV002', 2, CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '15 days', 25000.00, 2000.00, 27000.00, 'sent', 13),
('INV003', 3, CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '20 days', 75000.00, 6000.00, 81000.00, 'sent', 13);

-- ============================================================================
-- INVOICE LINE ITEMS
-- ============================================================================
INSERT INTO invoice_line_items (invoice_id, line_number, product_id, description, quantity, unit_price, line_total) VALUES
(1, 1, 7, 'ERP Software License', 10, 4999.99, 49999.90),
(2, 1, 6, 'CRM Software License', 25, 999.99, 24999.75),
(3, 1, 1, 'Laptop Pro 15"', 50, 1299.99, 64999.50),
(3, 2, 3, 'Monitor 27" 4K', 25, 399.99, 9999.75);

-- ============================================================================
-- PAYMENTS
-- ============================================================================
INSERT INTO payments (payment_number, invoice_id, payment_date, payment_method, amount, status, processed_by) VALUES
('PAY001', 1, CURRENT_DATE - INTERVAL '20 days', 'bank_transfer', 54000.00, 'completed', 13);

-- ============================================================================
-- FINANCIAL PERIODS
-- ============================================================================
INSERT INTO financial_periods (period_name, start_date, end_date, fiscal_year, quarter, is_closed) VALUES
('Q1 2024', '2024-01-01', '2024-03-31', 2024, 1, FALSE),
('Q2 2024', '2024-04-01', '2024-06-30', 2024, 2, FALSE),
('Q3 2024', '2024-07-01', '2024-09-30', 2024, 3, FALSE),
('Q4 2024', '2024-10-01', '2024-12-31', 2024, 4, FALSE);

-- ============================================================================
-- CHART OF ACCOUNTS
-- ============================================================================
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_active) VALUES
('1000', 'Cash', 'asset', TRUE),
('1100', 'Accounts Receivable', 'asset', TRUE),
('1200', 'Inventory', 'asset', TRUE),
('2000', 'Accounts Payable', 'liability', TRUE),
('3000', 'Equity', 'equity', TRUE),
('4000', 'Revenue', 'revenue', TRUE),
('5000', 'Cost of Goods Sold', 'expense', TRUE),
('6000', 'Operating Expenses', 'expense', TRUE);

-- ============================================================================
-- PROJECTS
-- ============================================================================
INSERT INTO projects (project_code, name, description, customer_id, project_type, status, priority, start_date, end_date, budget, project_manager_id) VALUES
('PROJ001', 'Acme ERP Implementation', 'ERP system implementation for Acme Corp', 1, 'client', 'active', 'high', CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE + INTERVAL '120 days', 200000.00, 29),
('PROJ002', 'Internal IT Infrastructure Upgrade', 'Upgrade internal IT infrastructure', NULL, 'internal', 'active', 'medium', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '90 days', 150000.00, 7),
('PROJ003', 'Product Development - New CRM Features', 'Develop new features for CRM product', NULL, 'rnd', 'active', 'high', CURRENT_DATE - INTERVAL '45 days', CURRENT_DATE + INTERVAL '150 days', 300000.00, 29);

-- ============================================================================
-- PROJECT TASKS
-- ============================================================================
INSERT INTO project_tasks (project_id, task_code, name, description, assigned_to, status, priority, estimated_hours, due_date, progress_percent) VALUES
(1, 'TASK001', 'Requirements Gathering', 'Gather and document requirements', 29, 'done', 'high', 40, CURRENT_DATE - INTERVAL '50 days', 100),
(1, 'TASK002', 'System Configuration', 'Configure ERP system', 8, 'in_progress', 'high', 80, CURRENT_DATE + INTERVAL '30 days', 60),
(1, 'TASK003', 'User Training', 'Train end users', 29, 'todo', 'medium', 40, CURRENT_DATE + INTERVAL '90 days', 0),
(2, 'TASK004', 'Server Migration', 'Migrate servers to cloud', 10, 'in_progress', 'high', 120, CURRENT_DATE + INTERVAL '60 days', 40),
(3, 'TASK005', 'Feature Design', 'Design new CRM features', 30, 'done', 'high', 60, CURRENT_DATE - INTERVAL '30 days', 100),
(3, 'TASK006', 'Feature Development', 'Develop new CRM features', 8, 'in_progress', 'high', 200, CURRENT_DATE + INTERVAL '120 days', 30);

-- ============================================================================
-- SUPPORT TICKETS
-- ============================================================================
INSERT INTO support_tickets (ticket_number, customer_id, subject, description, priority, status, category, assigned_to, created_by) VALUES
('TICK001', 1, 'ERP Login Issue', 'Unable to login to ERP system', 'high', 'resolved', 'technical', 26, 1),
('TICK002', 2, 'Billing Question', 'Question about invoice INV002', 'medium', 'open', 'billing', 27, 2),
('TICK003', 3, 'Feature Request', 'Request for new reporting feature', 'low', 'open', 'feature_request', 26, 3);

-- ============================================================================
-- MARKETING CAMPAIGNS
-- ============================================================================
INSERT INTO marketing_campaigns (campaign_code, name, description, campaign_type, status, start_date, end_date, budget, campaign_manager_id) VALUES
('CAMP001', 'Q4 Product Launch', 'Launch campaign for new product line', 'email', 'active', CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '45 days', 50000.00, 20),
('CAMP002', 'Trade Show 2024', 'Annual industry trade show participation', 'event', 'completed', CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '85 days', 75000.00, 20);

-- ============================================================================
-- EVENTS
-- ============================================================================
INSERT INTO events (event_code, name, description, event_type, start_date, end_date, location, venue_name, budget, organizer_id) VALUES
('EVT001', 'Industry Trade Show 2024', 'Annual industry trade show', 'trade_show', CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '88 days', 'Las Vegas, NV', 'Convention Center', 75000.00, 20),
('EVT002', 'Webinar: Digital Transformation', 'Educational webinar on digital transformation', 'webinar', CURRENT_DATE + INTERVAL '30 days', CURRENT_DATE + INTERVAL '30 days', 'Online', 'Zoom', 5000.00, 21);

-- Note: This is a sample seed data file. In production, you would generate
-- more comprehensive data programmatically or use a data generation tool.
-- The above provides a good foundation with realistic relationships across
-- all major modules of the enterprise system.

