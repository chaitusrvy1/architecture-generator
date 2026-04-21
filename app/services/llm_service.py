import logging
import re
import time
import asyncio
from dataclasses import dataclass
import google.generativeai as genai
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- State Management ---

@dataclass
class ModelCache:
    google_model: str | None = None
    last_discovery: float = 0.0

@dataclass
class CircuitBreaker:
    openai_block_until: float = 0.0
    google_block_until: float = 0.0

_MODEL_CACHE = ModelCache()
_CIRCUIT_BREAKER = CircuitBreaker()
CACHE_TTL = 3600
BREAKER_TTL = 300

def is_openai_available(now: float) -> bool:
    return now > _CIRCUIT_BREAKER.openai_block_until

def record_openai_backoff(now: float) -> None:
    _CIRCUIT_BREAKER.openai_block_until = now + BREAKER_TTL

def is_google_available(now: float) -> bool:
    return now > _CIRCUIT_BREAKER.google_block_until

def record_google_backoff(now: float) -> None:
    _CIRCUIT_BREAKER.google_block_until = now + BREAKER_TTL

# --- Helper Functions ---

def extract_mermaid_code(text: str) -> str:
    """Extracts and cleans Mermaid code while preserving line structure."""
    # 1. Extract from code blocks
    mermaid_match = re.search(r"```(?:mermaid)?\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    code = mermaid_match.group(1).strip() if mermaid_match else text.strip()

    # 2. Normalize ALL possible newline encodings
    code = code.replace("\\n", "\n").replace("\\r", "\n").replace("\r\n", "\n")
    
    # 3. Line-based processing
    processed_lines = []
    for raw_line in code.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        
        # Remove double quotes as requested for labels/JSON safety
        line = line.replace('"', '')

        # 4. SMART FORMATTING RULES:
        # - Header (graph TD, etc.) should NOT have a semicolon
        # - 'end' should NOT have a semicolon
        # - Everything else should have a semicolon for robustness
        line_lower = line.lower()
        if line_lower.startswith("graph ") or line_lower.startswith("flowchart "):
            processed_lines.append(line) # Header: no semicolon
        elif line_lower == "end":
            processed_lines.append("end") # End: no semicolon
        else:
            # Add semicolon if missing
            processed_lines.append(line if line.endswith(";") else f"{line};")

    return " ".join(processed_lines).strip()

async def _get_best_google_model():
    now = time.time()
    if _MODEL_CACHE.google_model and (now - _MODEL_CACHE.last_discovery < CACHE_TTL):
        return _MODEL_CACHE.google_model
    
    try:
        # Note: genai.list_models() is sync, but it's a lightweight discovery call.
        # For a truly async approach, we could wrap it in a thread if it becomes a bottleneck.
        genai.configure(api_key=settings.google_api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-1.5-flash', 'models/gemini-flash-latest', 'models/gemini-1.5-pro', 'models/gemini-pro']
        selected = next((m for m in priority if m in available), available[0] if available else None)
        
        _MODEL_CACHE.google_model = selected
        _MODEL_CACHE.last_discovery = now
        return selected
    except Exception as e:
        logger.error(f"Google discovery error: {str(e)}")
        return None

# --- Provider Implementation Helpers ---

async def _try_openai(system_prompt: str, user_prompt: str, now: float) -> str | None:
    if not settings.openai_api_key or not is_openai_available(now):
        return None
    try:
        logger.info("Attempting OpenAI")
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            timeout=15,
        )
        return extract_mermaid_code(response.choices[0].message.content)
    except Exception as e:
        if "429" in str(e):
            record_openai_backoff(now)
        logger.error(f"OpenAI Error: {str(e)}")
        return None

async def _try_google(system_prompt: str, user_prompt: str, now: float) -> str | None:
    if not settings.google_api_key or not is_google_available(now):
        return None
    try:
        model_name = await _get_best_google_model()
        if not model_name:
            return None
        logger.info(f"Attempting Google {model_name}")
        model = genai.GenerativeModel(model_name)
        # Gemini SDK has generate_content_async
        response = await model.generate_content_async(f"{system_prompt}\n\n{user_prompt}")
        return extract_mermaid_code(response.text)
    except Exception as e:
        if "429" in str(e):
            record_google_backoff(now)
        logger.error(f"Google Error: {str(e)}")
        return None

# --- Main Orchestrator ---

async def generate_architecture_diagram(user_requirement: str, invention_details: dict) -> str:
    now = time.time()
    system_prompt = (
        "You are a Principal Software Architect. Generate a detailed Technical Architecture Design in MermaidJS format. "
        "RULES:\n"
        "1. DO NOT use double quotes (\") in labels.\n"
        "2. Use subgraphs and specialized shapes.\n"
        "3. Output ONLY the code starting with 'graph TD;'."
    )
    user_prompt = (
        f"Invention: {invention_details.get('title')}\n"
        f"Desc: {invention_details.get('description')}\n"
        f"Req: {user_requirement}"
    )

    # 1. Attempt OpenAI
    diagram = await _try_openai(system_prompt, user_prompt, now)
    if diagram:
        return diagram

    # 2. Attempt Google Gemini
    diagram = await _try_google(system_prompt, user_prompt, now)
    if diagram:
        return diagram

    # 3. Fallback to mock
    return await _mock_patent_generate(user_requirement, invention_details)

async def _mock_patent_generate(user_requirement: str, invention_details: dict) -> str:
    logger.info("Using mock fallback")
    # Return valid Mermaid code
    return "graph TD;\nsubgraph Logic;\nA((User)) --> B([Gateway]);\nend"
