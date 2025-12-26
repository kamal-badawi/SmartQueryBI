-- ----------------------------
--  Product Dimension
-- ----------------------------
INSERT INTO product_dim (product_id, product_name, category, brand, supplier, cost_price) VALUES
(gen_random_uuid(), 'Model S', 'Sedan', 'Tesla', 'Tesla Inc', 75000.00),
(gen_random_uuid(), 'Model 3', 'Sedan', 'Tesla', 'Tesla Inc', 45000.00),
(gen_random_uuid(), 'Mustang', 'Coupe', 'Ford', 'Ford Motors', 55000.00),
(gen_random_uuid(), 'F-150', 'Truck', 'Ford', 'Ford Motors', 40000.00),
(gen_random_uuid(), 'Civic', 'Sedan', 'Honda', 'Honda Ltd', 25000.00),
(gen_random_uuid(), 'Accord', 'Sedan', 'Honda', 'Honda Ltd', 30000.00),
(gen_random_uuid(), 'Corolla', 'Sedan', 'Toyota', 'Toyota Co', 22000.00),
(gen_random_uuid(), 'Camry', 'Sedan', 'Toyota', 'Toyota Co', 28000.00),
(gen_random_uuid(), 'RAV4', 'SUV', 'Toyota', 'Toyota Co', 35000.00),
(gen_random_uuid(), 'CX-5', 'SUV', 'Mazda', 'Mazda Motors', 32000.00);


-- ----------------------------
--  Employee Dimension
-- ----------------------------
INSERT INTO employee_dim (employee_id, first_name, last_name, role, hire_date, department) VALUES
(gen_random_uuid(), 'Max', 'Müller', 'Salesperson', '2018-05-12', 'Sales'),
(gen_random_uuid(), 'Anna', 'Schmidt', 'Salesperson', '2019-03-01', 'Sales'),
(gen_random_uuid(), 'Lukas', 'Weber', 'Manager', '2015-07-23', 'Management'),
(gen_random_uuid(), 'Sophie', 'Fischer', 'Salesperson', '2020-01-15', 'Sales'),
(gen_random_uuid(), 'Tom', 'Neumann', 'Salesperson', '2021-09-30', 'Sales');



-- ----------------------------
--  Store Dimension
-- ----------------------------
INSERT INTO store_dim (store_id, store_name, location, region, manager_id) VALUES
(gen_random_uuid(), 'AutoCity Berlin', 'Berlin', 'North', (SELECT employee_id FROM employee_dim WHERE first_name='Lukas' AND last_name='Weber')),
(gen_random_uuid(), 'CarWorld Hamburg', 'Hamburg', 'North', (SELECT employee_id FROM employee_dim WHERE first_name='Lukas' AND last_name='Weber')),
(gen_random_uuid(), 'Autohaus München', 'Munich', 'South', (SELECT employee_id FROM employee_dim WHERE first_name='Lukas' AND last_name='Weber')),
(gen_random_uuid(), 'Drive Frankfurt', 'Frankfurt', 'West', (SELECT employee_id FROM employee_dim WHERE first_name='Lukas' AND last_name='Weber'));



-- ----------------------------
--  Product Dimension
-- ----------------------------
INSERT INTO customer_dim (customer_id, first_name, last_name, email, phone, city, country) VALUES
(gen_random_uuid(), 'Jonas', 'Klein', 'jonas.klein@example.com', '01761234567', 'Berlin', 'Germany'),
(gen_random_uuid(), 'Laura', 'Becker', 'laura.becker@example.com', '01769876543', 'Hamburg', 'Germany'),
(gen_random_uuid(), 'Felix', 'Hofmann', 'felix.hofmann@example.com', '01763456789', 'Munich', 'Germany'),
(gen_random_uuid(), 'Marie', 'Wolf', 'marie.wolf@example.com', '01762345678', 'Frankfurt', 'Germany'),
(gen_random_uuid(), 'Lena', 'Schulz', 'lena.schulz@example.com', '01761239876', 'Berlin', 'Germany');



-- ----------------------------
--  Date Dimension
-- ----------------------------
INSERT INTO date_dim (date_id, year, month, day, quarter, weekday)
SELECT 
    d::date as date_id,
    EXTRACT(YEAR FROM d)::int as year,
    EXTRACT(MONTH FROM d)::int as month,
    EXTRACT(DAY FROM d)::int as day,
    EXTRACT(QUARTER FROM d)::int as quarter,
    EXTRACT(DOW FROM d)::int + 1 as weekday  -- PostgreSQL: Sunday=0, Monday=1, ...
FROM generate_series('2024-01-01'::date, '2024-12-31'::date, interval '1 day') as d;




-- ----------------------------
--   Sales
-- ----------------------------
-- Insert 300 random records into sales_fact table
-- Alternative: Insert 300 records with more controlled distribution
DO $$
DECLARE
    i INTEGER;
    v_date_id DATE;
    v_product_id UUID;
    v_employee_id UUID;
    v_store_id UUID;
    v_customer_id UUID;
    v_quantity INTEGER;
    v_unit_price NUMERIC(10,2);
    v_discount NUMERIC(5,2);
    v_base_price NUMERIC(10,2);
BEGIN
    FOR i IN 1..300 LOOP
        -- Get random date from 2024
        SELECT date_id INTO v_date_id 
        FROM public.date_dim 
        WHERE year = '2024' 
        ORDER BY RANDOM() 
        LIMIT 1;
        
        -- Get random product
        SELECT product_id, cost_price INTO v_product_id, v_base_price
        FROM public.product_dim 
        ORDER BY RANDOM() 
        LIMIT 1;
        
        -- Get random sales employee
        SELECT employee_id INTO v_employee_id
        FROM public.employee_dim 
        WHERE role = 'Salesperson'
        ORDER BY RANDOM() 
        LIMIT 1;
        
        -- Get random store
        SELECT store_id INTO v_store_id
        FROM public.store_dim 
        ORDER BY RANDOM() 
        LIMIT 1;
        
        -- Get random customer
        SELECT customer_id INTO v_customer_id
        FROM public.customer_dim 
        ORDER BY RANDOM() 
        LIMIT 1;
        
        -- Random quantity (1-3, mostly 1)
        v_quantity := CASE 
            WHEN RANDOM() < 0.8 THEN 1
            WHEN RANDOM() < 0.95 THEN 2
            ELSE 3
        END;
        
        -- Unit price: cost price + 10-30% margin
        v_unit_price := v_base_price * (1.1 + (RANDOM() * 0.2));
        
        -- Discount: mostly 0-10%, occasionally more
        v_discount := CASE 
            WHEN RANDOM() < 0.6 THEN 0
            WHEN RANDOM() < 0.9 THEN ROUND((RANDOM() * 10)::numeric, 2)
            ELSE ROUND((RANDOM() * 20)::numeric, 2)
        END;
        
        -- Insert the record
        INSERT INTO public.sales_fact 
            (date_id, product_id, employee_id, store_id, customer_id, quantity, unit_price, discount)
        VALUES 
            (v_date_id, v_product_id, v_employee_id, v_store_id, v_customer_id, 
             v_quantity, v_unit_price, v_discount);
    END LOOP;
END $$;