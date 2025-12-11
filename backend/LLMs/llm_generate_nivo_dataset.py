def generate_nivo_dataset(chart_type: str, data: list) -> dict:
    """
    Converts raw SQL data rows into a Nivo-compatible dataset for the selected chart type.
    The LLM ALWAYS returns:

    {
        "data": <nivo_ready_data>
    }

    No explanations. No text outside the dict.
    """
    import google.generativeai as genai
    from decouple import config
    import json
    import re

    API_KEY = config("GOOGLE_GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

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
        response = model.generate_content(prompt)
        text = response.text.strip()

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
        except:
            parsed = eval(raw_dict)

        return parsed

    except Exception as e:
        return {"data": None, "error": str(e)}
