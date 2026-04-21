import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.models.schemas import ArchitectureRequest, ArchitectureResponse
from app.services.cosmos_db import get_invention_details
from app.services.llm_service import generate_architecture_diagram
from app.services.validation import validate_mermaid_code, get_kroki_url

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/architecture", response_model=ArchitectureResponse)
async def create_architecture(request: ArchitectureRequest):
    logger.info(f"Received request for ID: {request.invention_id}")
    
    invention_details = await get_invention_details(request.invention_id)
    
    llm_output = await generate_architecture_diagram(
        user_requirement=request.user_requirement,
        invention_details=invention_details
    )
    
    if llm_output == "INVALID_INTENT":
        raise HTTPException(status_code=400, detail="Invalid request intent.")

    if await validate_mermaid_code(llm_output):
        svg_url = get_kroki_url(llm_output)
        return ArchitectureResponse(
            status="success",
            mermaid_code=llm_output,
            svg_url=svg_url,
            message="Architecture diagram generated successfully."
        )
    
    return ArchitectureResponse(
        status="error",
        mermaid_code=None,
        message="Generation failed or syntax is invalid."
    )

@router.get("/architecture/{invention_id}/raw", response_class=PlainTextResponse)
async def get_raw_architecture(invention_id: str, user_requirement: str = "Design architecture"):
    response = await create_architecture(ArchitectureRequest(
        user_requirement=user_requirement,
        invention_id=invention_id
    ))
    return response.mermaid_code or "Error"
