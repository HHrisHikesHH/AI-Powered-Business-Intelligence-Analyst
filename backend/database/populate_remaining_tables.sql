-- ============================================================================
-- POPULATE REMAINING EMPTY TABLES
-- Fix foreign key references and populate missing data
-- ============================================================================

-- 1. SALES ORDER ITEMS (fix order_id references)
INSERT INTO sales_order_items (order_id, line_number, product_id, description, quantity, unit_price, line_total)
SELECT 
    so.id as order_id,
    row_number() OVER (PARTITION BY so.id ORDER BY random()) as line_number,
    random() * 149 + 1 as product_id,
    'Product description',
    random() * 9 + 1 as quantity,
    random() * 1990 + 10 as unit_price,
    (random() * 9 + 1) * (random() * 1990 + 10) as line_total
FROM sales_orders so
CROSS JOIN generate_series(1, random() * 4 + 1) as line_num
WHERE NOT EXISTS (SELECT 1 FROM sales_order_items WHERE order_id = so.id)
LIMIT 1500;

-- 2. QUOTE LINE ITEMS (fix quote_id references)
INSERT INTO quote_line_items (quote_id, line_number, product_id, description, quantity, unit_price, line_total)
SELECT 
    q.id as quote_id,
    row_number() OVER (PARTITION BY q.id ORDER BY random()) as line_number,
    random() * 149 + 1 as product_id,
    'Product description',
    random() * 19 + 1 as quantity,
    random() * 4950 + 50 as unit_price,
    (random() * 19 + 1) * (random() * 4950 + 50) as line_total
FROM quotes q
CROSS JOIN generate_series(1, random() * 5 + 1) as line_num
WHERE NOT EXISTS (SELECT 1 FROM quote_line_items WHERE quote_id = q.id)
LIMIT 1000;

-- 3. PURCHASE ORDER ITEMS (fix purchase_order_id references)
INSERT INTO purchase_order_items (purchase_order_id, line_number, product_id, description, quantity, unit_price, received_quantity, line_total)
SELECT 
    po.id as purchase_order_id,
    row_number() OVER (PARTITION BY po.id ORDER BY random()) as line_number,
    random() * 149 + 1 as product_id,
    'Product description',
    random() * 90 + 10 as quantity,
    random() * 495 + 5 as unit_price,
    CASE WHEN random() < 0.7 THEN (random() * 90 + 10)::int ELSE (random() * 90)::int END as received_quantity,
    (random() * 90 + 10) * (random() * 495 + 5) as line_total
FROM purchase_orders po
CROSS JOIN generate_series(1, random() * 7 + 1) as line_num
WHERE NOT EXISTS (SELECT 1 FROM purchase_order_items WHERE purchase_order_id = po.id)
LIMIT 1000;

-- 4. TIME ENTRIES (fix task_id references - only use existing task_ids)
INSERT INTO time_entries (employee_id, project_id, task_id, entry_date, hours_worked, description, billable, approved)
SELECT 
    random() * 299 + 1 as employee_id,
    pt.project_id,
    pt.id as task_id,
    CURRENT_DATE - (random() * 365)::int as entry_date,
    random() * 7.5 + 0.5 as hours_worked,
    'Time entry description',
    CASE WHEN random() < 0.6 THEN true ELSE false END as billable,
    CASE WHEN random() < 0.7 THEN true ELSE false END as approved
FROM project_tasks pt
CROSS JOIN generate_series(1, random() * 2 + 1) as entry_num
LIMIT 1500;

-- 5. EVENT ATTENDEES (fix event_id references)
INSERT INTO event_attendees (event_id, lead_id, customer_id, employee_id, registration_date, attended)
SELECT 
    e.id as event_id,
    CASE WHEN random() < 0.3 THEN (random() * 298 + 1)::int ELSE NULL END as lead_id,
    CASE WHEN random() < 0.4 THEN (random() * 199 + 1)::int ELSE NULL END as customer_id,
    CASE WHEN random() < 0.2 THEN (random() * 299 + 1)::int ELSE NULL END as employee_id,
    e.start_date - (random() * 30)::int as registration_date,
    CASE WHEN random() < 0.7 THEN true ELSE false END as attended
FROM events e
CROSS JOIN generate_series(1, random() * 40 + 10) as attendee_num
LIMIT 1500;

-- 6. BUDGETS (fix account_id references - only use existing account_ids)
INSERT INTO budgets (budget_name, department_id, account_id, period_id, budgeted_amount, status, approved_by)
SELECT 
    'Budget ' || generate_series || ' - Q' || (random() * 3 + 1)::int || ' 2024' as budget_name,
    CASE WHEN random() < 0.8 THEN (random() * 14 + 1)::int ELSE NULL END as department_id,
    (random() * 13 + 1)::int as account_id,  -- Only use accounts 1-13 (14 doesn't exist)
    (random() * 15 + 1)::int as period_id,
    random() * 490000 + 10000 as budgeted_amount,
    (ARRAY['draft', 'approved', 'active', 'closed'])[(random() * 3 + 1)::int] as status,
    CASE WHEN random() < 0.5 THEN (random() * 29 + 1)::int ELSE NULL END as approved_by
FROM generate_series(1, 100);

-- 7. GENERAL LEDGER (fix account_id references)
INSERT INTO general_ledger (transaction_date, account_id, debit_amount, credit_amount, description, reference_number, period_id, created_by)
SELECT 
    CURRENT_DATE - (random() * 730)::int as transaction_date,
    (random() * 13 + 1)::int as account_id,  -- Only use accounts 1-13
    CASE WHEN random() < 0.5 THEN random() * 9900 + 100 ELSE 0 END as debit_amount,
    CASE WHEN random() >= 0.5 THEN random() * 9900 + 100 ELSE 0 END as credit_amount,
    'Transaction ' || generate_series as description,
    'REF' || lpad(generate_series::text, 5, '0') as reference_number,
    (random() * 15 + 1)::int as period_id,
    (random() * 49 + 1)::int as created_by
FROM generate_series(1, 1000);

