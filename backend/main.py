from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Tuple, List
import time

from modules.execute_llm_select_query import execute_llm_select_query
from LLMs.llm_generate_visualization_query import generate_visualization_query
from LLMs.llm_generate_nivo_dataset import generate_nivo_dataset

# ======================================
# FastAPI Application
# ======================================
app = FastAPI(
    title="SmartQueryBI",
    description="""
SmartQueryBI – AI-powered Business Intelligence Platform

This API provides endpoints to:
- Convert natural language descriptions into SQL queries via LLM
- Execute SQL queries securely against Supabase
- Transform SQL results into Nivo.js visualization datasets
- Cache results in-memory to optimize repeated queries
- Monitor cache and API health
""",
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ======================================
# Cache Configuration
# ======================================
CACHE_TTL_SECONDS = 60  # 60 seconds TTL
CACHE: Dict[str, Tuple[dict, float]] = {}

# ======================================
# Pydantic Models
# ======================================
class UserRequest(BaseModel):
    description: str = "Natural language description for visualization"

class NivoDataModel(BaseModel):
    values: List[dict]

class PipelineResponse(BaseModel):
    chart: str
    llm_query: str
    raw_data: list
    nivo_data: NivoDataModel

# ======================================
# Cache Helper Functions
# ======================================
def get_cache(key: str):
    """Return cached value if present and not expired."""
    entry = CACHE.get(key)
    if entry:
        value, expire_at = entry
        if time.time() < expire_at:
            return value
        del CACHE[key]
    return None

def set_cache(key: str, value: dict):
    """Store value in cache with TTL."""
    expire_at = time.time() + CACHE_TTL_SECONDS
    CACHE[key] = (value, expire_at)

def invalidate_cache(key: str | None = None):
    """
    Invalidate cache entries.
    - key provided → invalidate a single entry
    - key None → clear entire cache
    """
    if key:
        return CACHE.pop(key, None) is not None
    CACHE.clear()
    return True

# ======================================
# Core Pipeline
# ======================================
def run_full_pipeline(description: str) -> dict:
    llm_result = generate_visualization_query(description)
    llm_query = llm_result["sql"].strip().rstrip(";")  
    chart = llm_result["chart"]

    raw_data = execute_llm_select_query(llm_query).get("results", [])
    nivo_data_raw = generate_nivo_dataset(chart, raw_data)

    # Normalize nivo_data to always be a dict with 'values' list
    if isinstance(nivo_data_raw, dict):
        if "data" in nivo_data_raw and isinstance(nivo_data_raw["data"], dict):
            nivo_values = nivo_data_raw["data"].get("values", [])
        else:
            nivo_values = nivo_data_raw.get("values", [])
    elif isinstance(nivo_data_raw, list):
        nivo_values = nivo_data_raw
    else:
        nivo_values = []

    return {
        "chart": chart,
        "llm_query": llm_query,
        "raw_data": raw_data,
        "nivo_data": {"values": nivo_values} 
    }


# ======================================
# API Endpoints
# ======================================
@app.get("/", summary="Root / Health Indicator", tags=["System"])
def read_root():
    """Returns basic service status"""
    return {"status": "ok", "service": "SmartQueryBI"}

@app.get("/health", summary="Health Check", tags=["System"])
def health_check():
    """Returns health info including cache status"""
    return {
        "status": "healthy",
        "cache_entries": len(CACHE),
        "cache_ttl_seconds": CACHE_TTL_SECONDS
    }

@app.post(
    "/dynamic-query/server-cache",
    response_model=PipelineResponse,
    summary="Execute LLM-powered query with caching",
    tags=["Query Pipeline"]
)
def dynamic_query_server_cache(request: UserRequest):
    """
    Executes the full LLM → SQL → Visualization pipeline.

    - Checks the in-memory cache for repeated requests
    - Cache TTL is 60 seconds
    - Returns a Nivo.js compatible dataset
    """
    cached_response = get_cache(request.description)
    if cached_response:
        return cached_response

    result = run_full_pipeline(request.description)
    set_cache(request.description, result)
    return result

@app.post("/cache/invalidate", summary="Invalidate Entire Cache", tags=["Cache"])
def invalidate_entire_cache():
    """Clears all cached entries"""
    invalidate_cache()
    return {"cache_cleared": True}

@app.post(
    "/cache/invalidate/{description}",
    summary="Invalidate Cache for Specific Request",
    tags=["Cache"]
)
def invalidate_single_cache(description: str):
    """Deletes cache entry for a specific user description"""
    removed = invalidate_cache(description)
    if not removed:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    return {"invalidated": True}

# ======================================
# Lifecycle Events
# ======================================
@app.on_event("startup")
def on_startup():
    print("SmartQueryBI started. In-memory cache initialized.")

@app.on_event("shutdown")
def on_shutdown():
    print("SmartQueryBI shutting down. Cache cleared.")
    CACHE.clear()
