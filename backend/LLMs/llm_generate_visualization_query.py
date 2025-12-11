def generate_visualization_query(question: str) -> dict:
    """
    Generates a safe SQL SELECT query AND a strictly valid Nivo.js chart type
    based on a natural language question using the Google Gemini LLM.

    Always returns a dict:
    {
        "chart": "<valid_nivo_chart_type>",
        "sql": "<SELECT ... ;>"
    }

    Security safeguards:
    - Only SELECT statements allowed
    - SQL must end with ;
    - No modification queries
    - Chart must be a valid Nivo.js chart type
    """
    import google.generativeai as genai
    from decouple import config
    import re
    import json

    VALID_NIVO_CHARTS = [
        "line", "area", "bar", "pie", "donut", "radar", "heat", "calendar",
        "scatter", "waffle", "treemap", "sunburst", "circle_packing",
        "stream", "funnel", "chord", "sankey", "network", "geo", "choropleth",
        "radial_bar", "boxplot", "bullet"
    ]

    API_KEY = config("GOOGLE_GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt_text = f"""
You are an AI specialized in generating SQL SELECT queries and choosing the best Nivo.js chart type.

Return ONLY a dictionary with:
{{
  "chart": "<the most appropriate Nivo.js chart type based on the data>",
  "sql": "<SELECT ... ;>"
}}

Rules:
- Only generate SELECT statements. Must end with semicolon.
- No INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE.
- Must match the user question and the database schema.
- The chart must be strictly one of the valid Nivo.js chart types:
{', '.join(VALID_NIVO_CHARTS)}.
- Automatically choose the Nivo.js chart type that best represents the data.

Database schema with explicit types:
-- Product Dimension
product_dim(
    product_id uuid,
    product_name text,
    category text,
    brand text,
    supplier text,
    cost_price numeric(10,2)
)
-- Employee Dimension
employee_dim(
    employee_id uuid,
    first_name text,
    last_name text,
    role text,
    hire_date date,
    department text
)
-- Store Dimension
store_dim(
    store_id uuid,
    store_name text,
    location text,
    region text,
    manager_id uuid
)
-- Customer Dimension
customer_dim(
    customer_id uuid,
    first_name text,
    last_name text,
    email text,
    phone text,
    city text,
    country text
)
-- Date Dimension
date_dim(
    date_id date,
    year int,
    month int,
    day int,
    quarter int,
    weekday int
)
-- Sales Fact Table
sales_fact(
    sale_id uuid,
    date_id date,
    product_id uuid,
    employee_id uuid,
    store_id uuid,
    customer_id uuid,
    quantity int,
    unit_price numeric(10,2),
    discount numeric(5,2),
    total_amount numeric(12,2)  -- generated always as (quantity*unit_price - discount)
)

Additional SQL generation rules to prevent runtime errors:
1. Always respect column data types:
   - Join uuid columns with uuid, int with int, text with text
   - Do NOT compare text fields to UUIDs
2. When aggregating by category or employee, map IDs to names using dimension tables
3. For date filters, never use a non-existent column like "date". Instead:
   - Use (SELECT MAX(date_id) FROM sales_fact) to get the last sale date
   - Join date_dim to get year/month/day/weekday as needed
4. Ensure aggregation level is correct:
   - Employee-level metrics aggregate over sales_fact and product_dim as needed
   - Category-level metrics map product_id to category first
5. Avoid division by zero or nulls in calculations
6. Always verify column exists in schema

--------------------------------------------
TASK
--------------------------------------------
1. Generate the best possible SQL SELECT query based on the description: "{question}".
2. Pick the correct valid Nivo.js chart type from the ENUM {VALID_NIVO_CHARTS}.
3. Return ONLY:

{{
  "chart": "<chart_type>",
  "sql": "<SELECT ... ;>"
}}
"""




    try:
        response = model.generate_content(prompt_text)
        result_text = response.text.strip()
        

        dict_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if not dict_match:
            # fallback: default bar chart if parsing fails
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

        # Ensure chart is valid and normalize case
        chart = result_dict.get("chart", "").lower()
        if chart not in VALID_NIVO_CHARTS:
            result_dict["chart"] = "bar"  # default fallback
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
