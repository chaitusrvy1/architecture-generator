import logging
from fastapi import FastAPI
from app.api.routes import router as architecture_router
from app.core.config import settings

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title=settings.app_name,
    description="API for generating MermaidJS architecture diagrams from user requirements and Cosmos DB data.",
    version="1.0.0"
)

# Include routers
app.include_router(architecture_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
