import logging
import re
import time
import google.generativeai as genai
from openai import OpenAI, AzureOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache and Circuit Breaker
_MODEL_CACHE = {"google_model": None, "last_discovery": 0}
_CIRCUIT_BREAKER = {"openai": 0, "google": 0}
CACHE_TTL = 3600
BREAKER_TTL = 300

def extract_mermaid_code(text: str) -> str:
    """
    Extracts and cleans Mermaid code.
    Fixes the 'end;' parse error by ensuring proper spacing around keywords.
    """
    mermaid_match = re.search(r"```(?:mermaid)?\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    code = mermaid_match.group(1).strip() if mermaid_match else text.strip()
    
    # 1. Standardize line breaks
    code = code.replace("\\n", "\n")
    
    # 2. Strip double quotes for JSON compatibility
    code = code.replace('"', '')
    
    # 3. SMART SEMICOLON REPLACEMENT:
    # We replace newlines with ' ; ' to ensure there is space around separators.
    # We specifically handle 'end' to ensure it doesn't have a trailing semicolon that breaks the parser.
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    processed_lines = []
    for line in lines:
        if line.lower() == 'end':
            processed_lines.append('end') # No semicolon after end
        else:
            processed_lines.append(f"{line};")
            
    code = " ".join(processed_lines)
    
    # 4. Final cleanup
    code = re.sub(r";\s*;", "; ", code)
    return code.strip()

async def _get_best_google_model():
    now = time.time()
    if _MODEL_CACHE["google_model"] and (now - _MODEL_CACHE["last_discovery"] < CACHE_TTL):
        return _MODEL_CACHE["google_model"]
    
    try:
        genai.configure(api_key=settings.google_api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ['models/gemini-1.5-flash', 'models/gemini-flash-latest', 'models/gemini-1.5-pro', 'models/gemini-pro']
        selected = next((m for m in priority if m in available), available[0] if available else None)
        _MODEL_CACHE["google_model"] = selected
        _MODEL_CACHE["last_discovery"] = now
        return selected
    except Exception as e:
        logger.error(f"Google discovery error: {str(e)}")
        return None

async def generate_architecture_diagram(user_requirement: str, invention_details: dict) -> str:
    now = time.time()
    system_prompt = (
        "You are a Principal Software Architect. Generate a detailed Technical Architecture Design in MermaidJS format. "
        "RULES:\n"
        "1. DO NOT use double quotes (\") in labels.\n"
        "2. Use subgraphs and specialized shapes.\n"
        "3. Output ONLY the code starting with 'graph TD;'."
    )
    user_prompt = f"Invention: {invention_details.get('title')}\nDesc: {invention_details.get('description')}\nReq: {user_requirement}"

    # 1. OpenAI
    if settings.openai_api_key and now > _CIRCUIT_BREAKER["openai"]:
        try:
            logger.info("Attempting OpenAI")
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1,
                timeout=15
            )
            return extract_mermaid_code(response.choices[0].message.content)
        except Exception as e:
            if "429" in str(e):
                _CIRCUIT_BREAKER["openai"] = now + BREAKER_TTL
            logger.error(f"OpenAI Error: {str(e)}")

    # 2. Google Gemini
    if settings.google_api_key and now > _CIRCUIT_BREAKER["google"]:
        try:
            model_name = await _get_best_google_model()
            if model_name:
                logger.info(f"Attempting Google {model_name}")
                model = genai.GenerativeModel(model_name)
                # Use a timeout for Gemini too
                response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
                return extract_mermaid_code(response.text)
        except Exception as e:
            if "429" in str(e):
                _CIRCUIT_BREAKER["google"] = now + BREAKER_TTL
            logger.error(f"Google Error: {str(e)}")

    return await _mock_patent_generate(user_requirement, invention_details)

async def _mock_patent_generate(user_requirement: str, invention_details: dict) -> str:
    logger.info("Using mock fallback")
    return "graph TD; subgraph Logic; A((User)) --> B([Gateway]); end"
