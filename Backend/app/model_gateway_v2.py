"""
Enhanced Model Gateway with Gemini, OpenRouter, and Ollama support.
Implements strict prompt enforcement, retries with exponential backoff, and rate limiting.
"""

import os
import time
import logging
import requests
import backoff
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-oss-20b:free")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openrouter.ai/api/v1")
MODEL_PRIORITY = os.getenv("MODEL_PRIORITY", "gemini")
MODEL_RETRY_ATTEMPTS = int(os.getenv("MODEL_RETRY_ATTEMPTS", "3"))
MODEL_TIMEOUT_SECONDS = int(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))
FORCE_OFFLINE_MODE = os.getenv("FORCE_OFFLINE_MODE", "0") == "1"

# Initialize clients
gemini_client = None
openai_client = None

if GEMINI_API_KEY and not FORCE_OFFLINE_MODE:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini client initialized successfully")
    except ImportError:
        logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}")

if OPENAI_API_KEY and not FORCE_OFFLINE_MODE:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        logger.info(f"OpenAI client initialized with model: {OPENAI_MODEL}")
    except ImportError:
        logger.warning("OpenAI library not installed.")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI client: {e}")


class ModelGatewayException(Exception):
    """Exception raised when all model attempts fail."""
    pass


# STRICT SYSTEM PROMPT FOR FACT-CHECKING
FACT_CHECK_SYSTEM_PROMPT = """You are a fact-checking AI assistant. Your task is to verify claims based ONLY on the provided CONTEXT.

STRICT RULES:
1. Use ONLY information from the provided CONTEXT below
2. If the CONTEXT is insufficient to make a determination, respond with verdict "NOT ENOUGH EVIDENCE"
3. Provide a clear verdict: TRUE, FALSE, MISLEADING, or NOT ENOUGH EVIDENCE
4. Give a short 2-3 line explanation
5. Cite specific sources from the CONTEXT with exact source names and snippets
6. Provide a confidence score between 0.00 and 1.00
7. DO NOT use external knowledge or make assumptions
8. DO NOT be overly cautious - if CONTEXT clearly supports/refutes claim, state it confidently

Response Format:
VERDICT: [TRUE|FALSE|MISLEADING|NOT ENOUGH EVIDENCE]
CONFIDENCE: [0.00-1.00]
EXPLANATION: [2-3 line explanation]
SOURCES: [List source names and relevant snippets from CONTEXT]
"""


def build_fact_check_prompt(claim: str, context: str) -> str:
    """Build the fact-checking prompt with claim and context."""
    return f"""CLAIM TO VERIFY:
{claim}

CONTEXT (Sources to use):
{context}

Analyze the CLAIM against the CONTEXT and provide your verdict following the strict format specified in the system prompt."""


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, Exception),
    max_tries=MODEL_RETRY_ATTEMPTS,
    max_time=MODEL_TIMEOUT_SECONDS
)
def _call_gemini(prompt: str, system: str = "") -> str:
    """
    Call Gemini with retry logic.
    
    Args:
        prompt: User prompt
        system: System instructions
        
    Returns:
        str: Model response
        
    Raises:
        Exception: If all retries fail
    """
    if not gemini_client:
        raise Exception("Gemini client not initialized")
    
    try:
        # Combine system and user prompt
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        response = gemini_client.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        if not response or not response.text:
            raise Exception("Empty response from Gemini")
        
        logger.info("Gemini response generated successfully")
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, Exception),
    max_tries=MODEL_RETRY_ATTEMPTS,
    max_time=MODEL_TIMEOUT_SECONDS
)
def _call_openrouter(prompt: str, system: str = "") -> str:
    """
    Call OpenRouter with retry logic.
    
    Args:
        prompt: User prompt
        system: System message
        
    Returns:
        str: Model response
        
    Raises:
        Exception: If all retries fail
    """
    if not openai_client:
        raise Exception("OpenAI client not initialized")
    
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        
        if not response.choices or not response.choices[0].message.content:
            raise Exception("Empty response from OpenRouter")
        
        logger.info("OpenRouter response generated successfully")
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        raise


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=MODEL_RETRY_ATTEMPTS,
    max_time=MODEL_TIMEOUT_SECONDS
)
def _call_ollama(prompt: str, system: str = "") -> str:
    """
    Call Ollama with retry logic.
    
    Args:
        prompt: User prompt
        system: System message
        
    Returns:
        str: Model response
        
    Raises:
        Exception: If all retries fail
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1024
            }
        }
        
        if system:
            payload["system"] = system
        
        response = requests.post(
            OLLAMA_ENDPOINT,
            json=payload,
            timeout=MODEL_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        
        result = response.json()
        if "response" not in result:
            raise Exception("Invalid response format from Ollama")
        
        logger.info("Ollama response generated successfully")
        return result["response"]
        
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        raise


def generate_llm_response(
    prompt: str,
    system: str = "",
    temperature: float = 0.2,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a response from the best available LLM.
    
    Priority order (configurable):
    1. Gemini (if available and priority=gemini)
    2. OpenRouter (if available)
    3. Ollama (local fallback)
    
    Args:
        prompt: User prompt
        system: System message/instructions
        temperature: Temperature parameter (unused for now, preset per model)
        max_tokens: Max tokens (unused for now, preset per model)
        
    Returns:
        Dict with keys: 'response' (str), 'model_used' (str), 'mode' (online/offline)
        
    Raises:
        ModelGatewayException: If all models fail
    """
    start_time = time.time()
    model_used = None
    mode = "offline"
    response_text = None
    errors = []
    
    # Try models in priority order
    if MODEL_PRIORITY == "gemini" and gemini_client and not FORCE_OFFLINE_MODE:
        try:
            response_text = _call_gemini(prompt, system)
            model_used = "gemini"
            mode = "online"
        except Exception as e:
            errors.append(f"Gemini failed: {e}")
            logger.warning(f"Gemini failed, trying fallback: {e}")
    
    # Fallback to OpenRouter
    if not response_text and openai_client and not FORCE_OFFLINE_MODE:
        try:
            response_text = _call_openrouter(prompt, system)
            model_used = "openrouter"
            mode = "online"
        except Exception as e:
            errors.append(f"OpenRouter failed: {e}")
            logger.warning(f"OpenRouter failed, trying Ollama: {e}")
    
    # Final fallback to Ollama
    if not response_text:
        try:
            response_text = _call_ollama(prompt, system)
            model_used = "ollama"
            mode = "offline"
        except Exception as e:
            errors.append(f"Ollama failed: {e}")
            logger.error(f"All models failed: {errors}")
            raise ModelGatewayException(f"All models failed. Errors: {'; '.join(errors)}")
    
    latency_ms = (time.time() - start_time) * 1000
    
    logger.info(f"Generated response using {model_used} in {latency_ms:.0f}ms")
    
    return {
        "response": response_text,
        "model_used": model_used,
        "mode": mode,
        "latency_ms": latency_ms
    }


def check_model_availability() -> Dict[str, str]:
    """
    Check availability of all models.
    
    Returns:
        Dict with model names as keys and status ('ok' or 'down') as values
    """
    status = {
        "gemini": "down",
        "openrouter": "down",
        "ollama": "down"
    }
    
    # Check Gemini
    if gemini_client:
        try:
            gemini_client.generate_content("test", generation_config={"max_output_tokens": 10})
            status["gemini"] = "ok"
        except:
            pass
    
    # Check OpenRouter
    if openai_client:
        try:
            openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            status["openrouter"] = "ok"
        except:
            pass
    
    # Check Ollama
    try:
        response = requests.post(
            OLLAMA_ENDPOINT,
            json={"model": OLLAMA_MODEL, "prompt": "test", "stream": False},
            timeout=5
        )
        if response.status_code == 200:
            status["ollama"] = "ok"
    except:
        pass
    
    return status


def get_current_mode() -> str:
    """
    Determine current operational mode.
    
    Returns:
        str: 'online' if any online model is available, 'offline' otherwise
    """
    if FORCE_OFFLINE_MODE:
        return "offline"
    
    if (MODEL_PRIORITY == "gemini" and gemini_client) or openai_client:
        return "online"
    
    return "offline"
