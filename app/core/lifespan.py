import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from azure.cosmos import CosmosClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AppState:
    def __init__(self):
        self.httpx_client: httpx.AsyncClient = None
        self.cosmos_client: CosmosClient = None
        self.cosmos_db = None
        self.cosmos_container = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up: Initializing resources")
    
    # Initialize httpx client
    state.httpx_client = httpx.AsyncClient(timeout=20.0)
    
    # Initialize Cosmos client if configured
    if settings.cosmos_db_endpoint and "mock" not in settings.cosmos_db_endpoint:
        try:
            state.cosmos_client = CosmosClient(settings.cosmos_db_endpoint, settings.cosmos_db_key)
            state.cosmos_db = state.cosmos_client.get_database_client(settings.cosmos_db_database_name)
            state.cosmos_container = state.cosmos_db.get_container_client(settings.cosmos_db_container_name)
            logger.info("Cosmos DB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down: Closing resources")
    if state.httpx_client:
        await state.httpx_client.aclose()
        logger.info("httpx client closed")
    
    if state.cosmos_client:
        # CosmosClient doesn't have an aclose in the sync version, 
        # but if we used the async version it would. 
        # The review mentioned sync CosmosClient construction is expensive.
        # azure-cosmos (sync) client doesn't need explicit close usually, but it's good practice.
        # Actually, if we want to be truly industry standard, we should use the async Cosmos client if possible.
        # But for now, I'll stick to the sync client as requested but shared.
        pass
