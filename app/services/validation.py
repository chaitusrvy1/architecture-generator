import logging
import base64
import zlib
import httpx
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

# Persistent client for connection pooling
_client = httpx.AsyncClient(timeout=20.0)

async def validate_mermaid_code(mermaid_code: str) -> bool:
    """
    Validates Mermaid syntax using Kroki API via POST request.
    This is more robust for large diagrams and avoids URL length limits.
    """
    if not mermaid_code or "graph" not in mermaid_code.lower():
        return False

    # Standardize to newlines for validation to ensure the parser is happy
    clean_code = mermaid_code.replace(";", "\n")

    for attempt in range(2):
        try:
            # POST raw code to Kroki's mermaid endpoint
            url = f"{settings.kroki_api_url}mermaid/svg"
            response = await _client.post(url, content=clean_code)
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Mermaid validation failed (Status {response.status_code})")
                return False
                
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.warning(f"Validation timeout/network error (Attempt {attempt+1}): {str(e)}")
            if attempt == 0:
                await asyncio.sleep(1)
                continue
            return False
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    return False

def get_kroki_url(mermaid_code: str):
    """
    Generates SVG URL for Kroki.
    """
    try:
        clean_code = mermaid_code.replace(";", "\n")
        compressed = zlib.compress(clean_code.encode('utf-8'), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        
        return f"{settings.kroki_api_url}mermaid/svg/{encoded}"
    except:
        return None
