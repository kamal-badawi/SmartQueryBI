from fastapi import FastAPI, Response
from pydantic import BaseModel
from functools import lru_cache
import json
import redis

from modules.execute_llm_select_query import execute_llm_select_query
from LLMs.llm_generate_visualization_query import generate_visualization_query
from LLMs.llm_generate_nivo_dataset import generate_nivo_dataset

# Attempt to connect to Redis
try:
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    redis_client = None
    REDIS_AVAILABLE = False

app = FastAPI(
    title="SmartQueryBI",
    description="""
SmartQueryBI – AI-powered Business Intelligence Platform

## Overview
An interactive BI platform that leverages Large Language Models (LLMs) to dynamically generate SQL queries for Supabase from natural language descriptions. Results are automatically transformed into interactive Nivo.js visualizations.

## Core Features

###  **Natural Language Querying**
- Users describe their data requests in plain English (e.g., "Show me sales trends for Q4 2023")
- LLM translates descriptions into optimized SQL queries
- Automatic chart type selection based on data characteristics

###  **Automatic Visualization**
- Raw SQL results transformed into Nivo.js compatible datasets
- Intelligent chart selection (line, bar, pie, scatter, etc.)
- Ready-to-use visualization data for frontend applications

###  **Multi-Level Caching System**
- **Client-Side Caching**: HTTP cache headers for browser caching
- **Server-Side LRU Cache**: In-memory Python caching for frequent requests
- **Redis Cache**: Distributed caching for scalability and persistence
- Reduces LLM API costs and improves response times

###  **Technical Architecture**
- LLM → SQL Query Generation → Supabase Execution → Nivo.js Transformation
- Modular design with separate LLM modules for different tasks
- Error handling and fallback mechanisms

## API Endpoints
- `/dynamic-query/client-cache` - Client-side cached responses
- `/dynamic-query/server-cache` - Server-side LRU cached responses  
- `/dynamic-query/redis-cache` - Redis-backed distributed caching

## Use Cases
- Business intelligence dashboards
- Ad-hoc data exploration
- Automated report generation
- Real-time data visualization

## Benefits
- No SQL knowledge required for end users
- Reduced development time for BI features
- Cost optimization through intelligent caching
- Scalable architecture for enterprise use
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def read_root():
    return {"message": "SmartQueryBI API is running", "status": "healthy", "redis_available": REDIS_AVAILABLE}


# Request Model
class UserRequest(BaseModel):
    description: str


# FULL RESULT CACHE (LLM + SQL + NIVO)
@lru_cache(maxsize=128)
def cached_full_pipeline(description: str):
    """
    Complete pipeline cache:
    - LLM → SQL Query + Chart Type
    - SQL → Database Results
    - Results → Nivo.js Dataset
    """

    # LLM -> SQL + Chart type
    llm_result = generate_visualization_query(description)
    llm_query = llm_result["sql"]
    chart = llm_result["chart"]

    # Execute database query
    raw_data = execute_llm_select_query(llm_query).get("results", [])

    # Transform into Nivo.js format
    nivo_data = generate_nivo_dataset(chart, raw_data)

    return {
        "chart": chart,
        "llm_query": llm_query,
        "raw_data": raw_data,
        "nivo_data": nivo_data
    }


# CLIENT-SIDE CACHE
@app.post("/dynamic-query/client-cache")
def dynamic_query_client_cache(request: UserRequest, response: Response):
    """
    Returns results with HTTP cache headers for client-side caching.
    Cache-Control headers instruct browsers/CDNs to cache responses.
    """
    
    response.headers["Cache-Control"] = "public, max-age=60"
    response.headers["X-Cache-Type"] = "client-side"

    # Execute full pipeline (cached or computed)
    result = cached_full_pipeline(request.description)

    return {
        "cache_type": "client-side",
        "cache_duration": "60 seconds",
        "user_request": request.description,
        "data": result["nivo_data"],
        "chart": result["chart"],
        "llm_query": result["llm_query"],
        "cache_hit": "true" if cached_full_pipeline.cache_info().hits > 0 else "false"
    }


# SERVER-SIDE LRU CACHE (RAM)
@app.post("/dynamic-query/server-cache")
def dynamic_query_server_cache(request: UserRequest):
    """
    Uses Python's LRU cache for server-side in-memory caching.
    Ideal for frequently repeated queries with low memory footprint.
    """
    
    cache_info = cached_full_pipeline.cache_info()

    # Execute full pipeline (cached or computed)
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


# REDIS CACHE (Distributed)
@app.post("/dynamic-query/redis-cache")
def dynamic_query_redis_cache(request: UserRequest):
    """
    Redis-based distributed caching for scalable deployments.
    Supports multiple application instances and persistent caching.
    """
    
    if not REDIS_AVAILABLE:
        return {
            "error": "Redis is not connected",
            "advice": "Start Redis: docker run -p 6379:6379 redis",
            "fallback": "Using server-side LRU cache instead"
        }

    cache_key = f"smartquerybi:{hash(request.description)}"

    # Check Redis cache first
    cached = redis_client.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        cached_data["cache_status"] = "hit"
        cached_data["source"] = "redis"
        return cached_data

    # Cache miss - compute full pipeline
    result = cached_full_pipeline(request.description)

    # Prepare Redis payload
    redis_payload = {
        "cache_type": "redis",
        "cache_status": "miss",
        "source": "computed",
        "user_request": request.description,
        "data": result["nivo_data"],
        "chart": result["chart"],
        "llm_query": result["llm_query"],
        "ttl_seconds": 60
    }

    # Store in Redis with 60-second expiration
    redis_client.setex(cache_key, 60, json.dumps(redis_payload))

    return redis_payload


# Health check endpoint
@app.get("/health")
async def health_check():
    """System health and dependency status"""
    return {
        "status": "healthy",
        "redis": "connected" if REDIS_AVAILABLE else "disconnected",
        "cache_size": cached_full_pipeline.cache_info().currsize,
        "version": "1.0.0"
    }


# Cache statistics endpoint
@app.get("/cache-stats")
async def cache_statistics():
    """Returns caching performance statistics"""
    lru_info = cached_full_pipeline.cache_info()
    
    stats = {
        "lru_cache": {
            "hits": lru_info.hits,
            "misses": lru_info.misses,
            "hit_ratio": f"{(lru_info.hits / (lru_info.hits + lru_info.misses)) * 100:.1f}%" if (lru_info.hits + lru_info.misses) > 0 else "0%",
            "max_size": lru_info.maxsize,
            "current_size": lru_info.currsize
        },
        "redis": {
            "available": REDIS_AVAILABLE,
            "status": "connected" if REDIS_AVAILABLE else "disconnected"
        }
    }
    
    return stats