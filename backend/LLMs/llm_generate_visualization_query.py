def generate_visualization_query(question: str) -> dict:
    """
    Generates a safe SQL SELECT query AND a strictly valid Nivo.js chart type
    based on a natural language question using the Groq LLaMA LLM.

    Always returns a dict:
    {
        "chart": "<valid_nivo_chart_type>",
        "sql": "<SELECT ... ;>"
    }
    """
    from decouple import config
    from groq import Groq
    import re
    import json

    VALID_NIVO_CHARTS = [
        "line", "area", "bar", "pie", "donut", "radar", "heat", "calendar",
        "scatter", "waffle", "treemap", "sunburst", "circle_packing",
        "stream", "funnel", "chord", "sankey", "network", "geo", "choropleth",
        "radial_bar", "boxplot", "bullet"
    ]

    # --------------------------------------------------
    # Groq Client
    # --------------------------------------------------
    client = Groq(api_key=config("GROQ_API_KEY"))

    prompt_text = f"""
You are an AI specialized in generating SQL SELECT queries for Supabase PostgreSQL and choosing the best Nivo.js chart type.

Return ONLY a dictionary with:
{{
  "chart": "<the most appropriate Nivo.js chart type based on the data>",
  "sql": "<SELECT ... ;>"
}}

STRICT SQL RULES FOR SUPABASE POSTGRESQL:
- ONLY generate SELECT statements - this is for READ-ONLY data visualization
- Allowed: SELECT, FROM, WHERE, JOIN (INNER, LEFT, RIGHT, FULL, CROSS), 
           GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET, 
           WITH (CTEs), UNION, UNION ALL, INTERSECT, EXCEPT,
           CASE WHEN, COALESCE, NULLIF, CAST, :: (type casting),
           Window Functions (ROW_NUMBER, RANK, SUM OVER, etc.),
           Aggregations (COUNT, SUM, AVG, MIN, MAX, STRING_AGG, ARRAY_AGG)
- MUST end with semicolon (;)
- Use LIMIT for pagination when appropriate
- EXPLICITLY FORBIDDEN: INSERT, UPDATE, DELETE, DROP, TRUNCATE, 
                       ALTER, CREATE, GRANT, REVOKE, MERGE, EXECUTE,
                       BEGIN, COMMIT, ROLLBACK, SAVEPOINT
- This is for Supabase PostgreSQL - use standard PostgreSQL syntax
- The chart must be strictly one of the valid Nivo.js chart types:
{', '.join(VALID_NIVO_CHARTS)}.
- Automatically choose the Nivo.js chart type that best represents the data.

DATABASE SCHEMA FOR SUPABASE:
-- Product Dimension
product_dim(
    product_id uuid PRIMARY KEY,
    product_name text NOT NULL,
    category text,
    brand text,
    supplier text,
    cost_price numeric(10,2)
)

-- Employee Dimension  
employee_dim(
    employee_id uuid PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    role text,
    hire_date date,
    department text
)

-- Store Dimension
store_dim(
    store_id uuid PRIMARY KEY,
    store_name text NOT NULL,
    location text,
    region text,
    manager_id uuid REFERENCES employee_dim(employee_id)
)

-- Customer Dimension
customer_dim(
    customer_id uuid PRIMARY KEY,
    first_name text,
    last_name text,
    email text,
    phone text,
    city text,
    country text
)

-- Date Dimension
date_dim(
    date_id date PRIMARY KEY,
    year int,
    month int,
    day int,
    quarter int,
    weekday int
)

-- Sales Fact Table
sales_fact(
    sale_id uuid PRIMARY KEY,
    date_id date REFERENCES date_dim(date_id),
    product_id uuid REFERENCES product_dim(product_id),
    employee_id uuid REFERENCES employee_dim(employee_id),
    store_id uuid REFERENCES store_dim(store_id),
    customer_id uuid REFERENCES customer_dim(customer_id),
    quantity int,
    unit_price numeric(10,2),
    discount numeric(5,2),
    total_amount numeric(12,2)
)

BEST PRACTICES FOR SUPABASE VISUALIZATION QUERIES:
1. Always JOIN dimension tables to get readable names (not UUIDs)
2. Use date_dim for time-based queries
3. Add LIMIT for performance when exploring data
4. Use appropriate aggregations for charts
5. Handle NULL values with COALESCE
6. Use aliases for clear column names

EXAMPLE QUERIES:
- "Top 10 products by sales": 
  SELECT p.product_name, SUM(s.total_amount) as total_sales
  FROM sales_fact s
  JOIN product_dim p ON s.product_id = p.product_id
  GROUP BY p.product_name
  ORDER BY total_sales DESC
  LIMIT 10;

- "Monthly sales trend":
  SELECT d.year, d.month, SUM(s.total_amount) as monthly_sales
  FROM sales_fact s
  JOIN date_dim d ON s.date_id = d.date_id
  GROUP BY d.year, d.month
  ORDER BY d.year, d.month;

- "Sales by category":
  SELECT p.category, COUNT(*) as transaction_count, SUM(s.total_amount) as total_sales
  FROM sales_fact s
  JOIN product_dim p ON s.product_id = p.product_id
  GROUP BY p.category
  ORDER BY total_sales DESC;

--------------------------------------------
TASK
--------------------------------------------
User Question: "{question}"

1. Generate a SAFE, READ-ONLY SELECT query optimized for Supabase PostgreSQL
2. Pick the best Nivo.js chart type for this data
3. Return ONLY the dictionary:

{{
  "chart": "<chart_type>",
  "sql": "<SELECT ... ;>"
}}

Remember: Only SELECT, use LIMIT when exploring, and make it efficient for visualization.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.0,
            max_completion_tokens=4000
        )

        result_text = response.choices[0].message.content.strip() if response.choices else ""

        dict_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if not dict_match:
            return {
                "chart": "bar",
                "sql": f"-- ERROR: Could not extract dict from LLM:\n-- {result_text}"
            }

        raw_dict_text = dict_match.group()

        try:
            result_dict = json.loads(raw_dict_text.replace("'", '"'))
        except json.JSONDecodeError:
            result_dict = eval(raw_dict_text)

        # Ensure SQL ends with semicolon
        if "sql" in result_dict and not result_dict["sql"].strip().endswith(";"):
            result_dict["sql"] = result_dict["sql"].strip() + ";"

        # Validate chart type
        chart = result_dict.get("chart", "").lower()
        if chart not in VALID_NIVO_CHARTS:
            result_dict["chart"] = "bar"
            result_dict["error"] = "-- ERROR: Invalid Nivo.js chart type returned; defaulted to 'bar'."
        else:
            result_dict["chart"] = chart

        return result_dict

    except Exception as e:
        return {
            "chart": "bar",
            "sql": f"-- Internal error: {str(e)}",
            "error": str(e)
        }