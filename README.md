```markdown
# SmartQueryBI

**Version:** 1.2.0  
**Description:**  
SmartQueryBI is an AI-powered Business Intelligence platform that converts natural language descriptions into SQL queries, executes them securely on a Supabase database, and transforms the results into Nivo.js-compatible visualizations.

---

## Features

- **Natural Language → SQL:** Converts user descriptions into safe SQL SELECT queries via LLM.
- **Secure SQL Execution:** READ-ONLY SELECT queries on Supabase, no data modifications allowed.
- **Nivo.js Visualizations:** Automatically transforms SQL results into Nivo.js-compatible datasets.
- **Caching:** In-memory cache with TTL (60 seconds) for repeated queries.
- **API Health & Cache Monitoring:** Endpoints for health checks and cache management.
- **Extensible:** Supports a wide range of Nivo.js chart types.

---

## Architecture & Workflow

```
[User Description]
        │
        ▼
 [LLM → generate_visualization_query]
        │
        ▼
   Safe SQL Query
        │
        ▼
 [execute_llm_select_query → Supabase RPC]
        │
        ▼
    Raw SQL Data
        │
        ▼
 [LLM → generate_nivo_dataset]
        │
        ▼
Nivo.js-Compatible Dataset
        │
        ▼
   API Response + Cache
```

**Details:**

1. **generate_visualization_query(question: str)**  
   - Generates a safe SELECT query for Supabase.  
   - Automatically chooses the most suitable Nivo.js chart type.  
   - Follows best practices for performance and readable outputs.

2. **execute_llm_select_query(llm_sql_query: str)**  
   - Executes SQL SELECT queries via Supabase RPC (`execute_sql`).  
   - Secure: Only SELECT statements allowed.  
   - Returns results in a consistent JSON format.

3. **generate_nivo_dataset(chart_type: str, data: list)**  
   - Converts SQL results into Nivo.js-compatible datasets.  
   - Supports all major Nivo.js chart types.

4. **Cache**  
   - TTL: 60 seconds  
   - Functions: `get_cache`, `set_cache`, `invalidate_cache`

---

## API Endpoints

### System

| Method | Endpoint       | Description |
|--------|----------------|-------------|
| GET    | `/`            | Root / Health Indicator |
| GET    | `/health`      | Health check including cache status |

### Query Pipeline

| Method | Endpoint                       | Description |
|--------|--------------------------------|-------------|
| POST   | `/dynamic-query/server-cache`  | Executes full pipeline (LLM → SQL → Nivo) with caching |

### Cache Management

| Method | Endpoint                          | Description |
|--------|-----------------------------------|-------------|
| POST   | `/cache/invalidate`               | Clears the entire cache |
| POST   | `/cache/invalidate/{description}`| Deletes cache entry for a specific user request |

---

## Supabase Data Model

- **product_dim:** Product details (`product_id`, `product_name`, `category`, `brand`, `supplier`, `cost_price`)  
- **employee_dim:** Employee details (`employee_id`, `first_name`, `last_name`, `role`, `hire_date`, `department`)  
- **store_dim:** Store details (`store_id`, `store_name`, `location`, `region`, `manager_id`)  
- **customer_dim:** Customer details (`customer_id`, `first_name`, `last_name`, `email`, `phone`, `city`, `country`)  
- **date_dim:** Date details (`date_id`, `year`, `month`, `day`, `quarter`, `weekday`)  
- **sales_fact:** Sales data (`sale_id`, `date_id`, `product_id`, `employee_id`, `store_id`, `customer_id`, `quantity`, `unit_price`, `discount`, `total_amount`)  

---

## Nivo.js Chart Types

Supported chart types:  

`line`, `area`, `bar`, `pie`, `donut`, `radar`, `heat`, `calendar`, `scatter`, `waffle`, `treemap`, `sunburst`, `circle_packing`, `stream`, `funnel`, `chord`, `sankey`, `network`, `geo`, `choropleth`, `radial_bar`, `boxplot`, `bullet`

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd SmartQueryBI

# Create Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Environment variables
# GROQ_API_KEY=<your_groq_api_key>
# SUPABASE_URL=<your_supabase_url>
# SUPABASE_KEY=<your_supabase_api_key>
```

---

## Usage

```bash
# Start FastAPI server
uvicorn main:app --reload
```

- API docs: `/docs`  
- Redoc: `/redoc`

---

## Example Requests

### 1. Last 30 Days Top Employees by Sales

```json
POST /dynamic-query/server-cache
{
  "description": "Analyze sales from the last 30 days: Rank all employees by sales and identify the top 3 performers. Provide individual sales for the top 3 employees and calculate the total sales for all remaining employees, resulting in four values: top 3 employees' sales and cumulative sales of others."
}
```

### 2. List All Employees

```json
POST /dynamic-query/server-cache
{
  "description": "Who are my employees?"
}
```

### 3. Top 3 Products per Top 3 Employees (Treemap)

```json
POST /dynamic-query/server-cache
{
  "description": "Create a list showing the top 3 products for each of the top 3 employees by sales. Each row should contain employee name, product name, and product sales, sorted by employee and product sales in descending order. Visualize as a treemap."
}
```

### 4. Three Lowest-Selling Products

```json
POST /dynamic-query/server-cache
{
  "description": "Identify the three products with the lowest sales."
}
```

### 5. Top 2 Employees per Store and Category (Heatmap + Bar)

```json
POST /dynamic-query/server-cache
{
  "description": "Analyze sales data from the last 60 days: For each store, calculate the top 2 employees by sales per product category. Include average sales per customer, number of distinct customers, and best-selling brand per category. Each row includes store, employee, category, top brand, average sales per customer, and total employee sales. Sort by store, category, and employee sales. Visualize as combined heatmap and bar chart."
}
```

### 6. Top 3 Stores per Category with Employee Metrics (Sunburst + Bar)

```json
POST /dynamic-query/server-cache
{
  "description": "Analyze sales from the last 90 days: For each product category, identify the top 3 stores by total sales. Rank employees within these stores by sales, and calculate average discount and share of premium customers for each employee. Each row includes category, store, employee, sales, average discount, and premium customer ratio. Sort by category, store sales, and employee sales. Visualize using combined sunburst and bar chart to represent hierarchy of category → store → employee."
}
```

### 7. Top 5 Employees by Sales Growth per Category (Line + Heatmap)

```json
POST /dynamic-query/server-cache
{
  "description": "Analyze sales based on the latest available sales date: For each product category, identify the top 5 employees by sales growth compared to the previous period. Include average sales per customer, number of returning customers, and the highest-sales weekday for each employee. Each row contains category, employee, sales growth, average sales per customer, returning customer count, and top weekday. Sort by category and sales growth in descending order. Visualize as a combined line chart and heatmap to show growth and customer activity."
}
```

---

## Security Considerations

- Only SELECT queries are allowed.  
- RPC `execute_sql` prevents SQL injection.  
- LLM outputs are validated (chart type, semicolon-terminated SQL).  

---

## License

[MIT License](LICENSE)
```

