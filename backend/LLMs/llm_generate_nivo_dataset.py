def generate_nivo_dataset(chart_type: str, data: list) -> dict:
    """
    Converts raw SQL data rows into a Nivo-compatible dataset for the selected chart type.
    The LLM ALWAYS returns:

    {
        "data": <nivo_ready_data>
    }

    No explanations. No text outside the dict.
    """
    from decouple import config
    from groq import Groq
    import json
    import re

    # --------------------------------------------------
    # Groq Client
    # --------------------------------------------------
    client = Groq(api_key=config("GROQ_API_KEY"))

    # Convert Python list to JSON for injecting into prompt
    raw_data_json = json.dumps(data)

    prompt = f"""
You are an AI specialized in transforming SQL result rows into 
valid Nivo.js chart datasets.

Your task:
Given a chart type "{chart_type}" and a list of input rows, output EXACTLY:

{{
  "data": <NIVO_DATA>
}}

NO explanations.
NO markdown.
NO comments.
NO extra text.
Only the dictionary above.

-------------------------------------------------------------
INPUT
-------------------------------------------------------------
Chart type: "{chart_type}"
Rows: {raw_data_json}

-------------------------------------------------------------
TASK
-------------------------------------------------------------
Transform the input rows into EXACTLY the required Nivo dataset
format for the selected chart type.

Output only:

{{
  "data": <NIVO_DATA>
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_completion_tokens=3500
        )

        text = response.choices[0].message.content.strip() if response.choices else ""

        dict_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not dict_match:
            return {
                "data": None,
                "error": "Could not extract dictionary from LLM output.",
                "raw": text
            }

        raw_dict = dict_match.group()

        try:
            parsed = json.loads(raw_dict.replace("'", '"'))
        except Exception:
            parsed = eval(raw_dict)

        return parsed

    except Exception as e:
        return {"data": None, "error": str(e)}
