from fastapi import FastAPI
from pydantic import BaseModel
from functools import lru_cache

from modules.execute_llm_select_query import execute_llm_select_query
from LLMs.llm_generate_visualization_query import generate_visualization_query
from LLMs.llm_generate_nivo_dataset import generate_nivo_dataset

app = FastAPI(
    title="SmartQueryBI",
    description="""
SmartQueryBI – AI-powered Business Intelligence Platform

An interactive BI platform that uses LLMs to generate SQL queries and transform
results into Nivo.js visualizations.

## Features

### Natural Language Querying
- LLM converts user descriptions into SQL
- Automatic chart type detection

### Automatic Visualization
- SQL results are converted into Nivo.js datasets

### Server-Side Caching
- LRU in-memory caching for repeated requests

## API Endpoints
- `/dynamic-query/server-cache`
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def read_root():
    return {"message": "SmartQueryBI API is running", "status": "healthy"}


class UserRequest(BaseModel):
    description: str


@lru_cache(maxsize=128)
def cached_full_pipeline(description: str):
    """
    Full pipeline:
    - LLM → SQL + chart type
    - SQL → database results
    - Results → Nivo.js dataset
    """

    llm_result = generate_visualization_query(description)
    llm_query = llm_result["sql"]
    chart = llm_result["chart"]

    raw_data = execute_llm_select_query(llm_query).get("results", [])

    nivo_data = generate_nivo_dataset(chart, raw_data)

    return {
        "chart": chart,
        "llm_query": llm_query,
        "raw_data": raw_data,
        "nivo_data": nivo_data
    }


@app.post("/dynamic-query/server-cache")
def dynamic_query_server_cache(request: UserRequest):
    cache_info = cached_full_pipeline.cache_info()

    result = cached_full_pipeline(request.description)

    return {
        "cache_type": "server-side (LRU RAM)",
        "cache_stats": {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "maxsize": cache_info.maxsize,
            "currsize": cache_info.currsize
        },
        "user_request": request.description,
        "data": result["nivo_data"],
        "chart": result["chart"],
        "llm_query": result["llm_query"]
    }




