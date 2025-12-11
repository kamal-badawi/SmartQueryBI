-- ============================================================
-- STAR SCHEMA: Sales Fact & Dimension Tables
-- For Supabase / PostgreSQL
-- ============================================================

-- ----------------------------
--  Product Dimension
-- ----------------------------
create table if not exists product_dim (
    product_id uuid primary key default gen_random_uuid(),
    product_name text not null,
    category text,
    brand text,
    supplier text,
    cost_price numeric(10,2)
);

-- ----------------------------
--  Employee Dimension
-- ----------------------------
create table if not exists employee_dim (
    employee_id uuid primary key default gen_random_uuid(),
    first_name text not null,
    last_name text not null,
    role text,
    hire_date date,
    department text
);

-- ----------------------------
--  Store Dimension
-- ----------------------------
create table if not exists store_dim (
    store_id uuid primary key default gen_random_uuid(),
    store_name text not null,
    location text,
    region text,
    manager_id uuid references employee_dim(employee_id)
);

-- ----------------------------
--  Customer Dimension
-- ----------------------------
create table if not exists customer_dim (
    customer_id uuid primary key default gen_random_uuid(),
    first_name text not null,
    last_name text not null,
    email text,
    phone text,
    city text,
    country text
);

-- ----------------------------
--  Date Dimension
-- ----------------------------
create table if not exists date_dim (
    date_id date primary key,
    year int,
    month int,
    day int,
    quarter int,
    weekday int
);

-- ----------------------------
--  Sales Fact Table
-- ----------------------------
create table if not exists sales_fact (
    sale_id uuid primary key default gen_random_uuid(),
    date_id date not null references date_dim(date_id),
    product_id uuid not null references product_dim(product_id),
    employee_id uuid not null references employee_dim(employee_id),
    store_id uuid not null references store_dim(store_id),
    customer_id uuid not null references customer_dim(customer_id),
    quantity int not null,
    unit_price numeric(10,2) not null,
    discount numeric(5,2) default 0,
    total_amount numeric(12,2) generated always as (quantity*unit_price - discount) stored
);

-- ============================================================
-- Optional: Indexes for faster queries
-- ============================================================
create index if not exists idx_sales_date on sales_fact(date_id);
create index if not exists idx_sales_product on sales_fact(product_id);
create index if not exists idx_sales_store on sales_fact(store_id);
create index if not exists idx_sales_customer on sales_fact(customer_id);
