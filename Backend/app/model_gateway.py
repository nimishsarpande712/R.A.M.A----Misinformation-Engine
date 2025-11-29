"""
Model Gateway - Unified interface for LLM backends (Gemini + Ollama)
"""

import os
import logging
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Initialize Gemini client if key is available
USE_GEMINI = False
genai = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        USE_GEMINI = True
        logger.info(f"Gemini client initialized with model: {GEMINI_MODEL}")
    except ImportError:
        logger.warning("google-generativeai library not installed. Falling back to Ollama.")
else:
    logger.info(f"No GEMINI_API_KEY found. Using Ollama endpoint: {OLLAMA_ENDPOINT}")


class ModelGatewayException(Exception):
    """Exception raised when model gateway operations fail."""
    pass


def generate_llm_response(
    prompt: str,
    system: str = "",
    temperature: float = 0.2,
    max_tokens: Optional[int] = None
) -> str:
    """
    Generate a response from the LLM (Gemini or Ollama).
    
    Tries Gemini first if key is available, then falls back to Ollama
    if the remote API is unreachable or fails.
    
    Args:
        prompt (str): The user prompt
        system (str): System message/context for the model
    temperature (float): Temperature parameter (0.0 to 1.0 typical)
    max_tokens (Optional[int]): Maximum tokens in response
        
    Returns:
        str: The generated response text
        
    Raises:
    ModelGatewayException: If both Gemini and Ollama fail
    """
    if USE_GEMINI:
        try:
            return _generate_gemini_response(prompt, system, temperature, max_tokens)
        except ModelGatewayException as e:
            # If Gemini fails (e.g., no internet), try Ollama as fallback
            logger.warning(f"Gemini failed, attempting Ollama fallback: {str(e)}")
            try:
                return _generate_ollama_response(prompt, system, temperature)
            except ModelGatewayException:
                # If both fail, re-raise the original error
                raise
    else:
        return _generate_ollama_response(prompt, system, temperature)


def _generate_gemini_response(
    prompt: str,
    system: str = "",
    temperature: float = 0.2,
    max_tokens: Optional[int] = None
) -> str:
    """
    Generate response using Google Gemini API.

    Args:
        prompt (str): The user prompt
        system (str): System instruction for the model
        temperature (float): Temperature parameter
        max_tokens (Optional[int]): Maximum output tokens

    Returns:
        str: Response text

    Raises:
        ModelGatewayException: If API request fails
    """
    try:
        if not USE_GEMINI:
            raise ModelGatewayException("Gemini is not configured")

        logger.info(f"Using Gemini ({GEMINI_MODEL}) for prompt: {prompt[:50]}...")

        # Build model with optional system instruction per-call to allow dynamic system prompts
        if system:
            model = genai.GenerativeModel(model_name=GEMINI_MODEL, system_instruction=system)
        else:
            model = genai.GenerativeModel(model_name=GEMINI_MODEL)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or 2048,
        }

        response = model.generate_content(prompt, generation_config=generation_config)

        # google-generativeai responses expose `.text`
        result = getattr(response, "text", None) or ""
        if not result:
            # Some responses return candidates; try to extract
            try:
                candidates = getattr(response, "candidates", []) or []
                if candidates and candidates[0].content.parts:
                    result = "".join(p.text for p in candidates[0].content.parts if getattr(p, "text", None))
            except Exception:
                pass

        if not result:
            logger.error("Empty response from Gemini")
            raise ModelGatewayException("Gemini returned empty response")

        logger.info(f"Gemini response generated successfully ({len(result)} chars)")
        return result.strip()

    except Exception as e:
        error_str = str(e).lower()
        # Heuristic network error detection
        if any(x in error_str for x in ["nameresolution", "failed to resolve", "getaddrinfo", "network", "timeout"]):
            logger.error("Network error while calling Gemini API")
            raise ModelGatewayException(
                "Cannot reach Gemini API. Check your internet connection or network settings."
            ) from e
        logger.error(f"Gemini API request failed: {str(e)}")
        raise ModelGatewayException(f"Gemini API error: {str(e)}") from e


def _generate_ollama_response(
    prompt: str,
    system: str = "",
    temperature: float = 0.2
) -> str:
    """
    Generate response using Ollama local HTTP endpoint.
    
    Args:
        prompt (str): The user prompt
        system (str): System message
        temperature (float): Temperature parameter (0.0 to 1.0)
        
    Returns:
        str: Response text
        
    Raises:
        ModelGatewayException: If Ollama request fails
    """
    try:
        logger.info(f"Using Ollama ({OLLAMA_MODEL}) for prompt: {prompt[:50]}...")
        
        # Construct the full prompt with system context
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\nUser: {prompt}\nAssistant:"
        
        # Prepare request payload
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        logger.debug(f"Sending request to Ollama: {OLLAMA_ENDPOINT}")
        response = requests.post(
            OLLAMA_ENDPOINT,
            json=payload,
            timeout=120  # 2 minute timeout for long-running requests
        )
        
        if response.status_code != 200:
            error_msg = f"Ollama HTTP {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise ModelGatewayException(error_msg)
        
        data = response.json()
        result = data.get("response", "")
        
        if not result:
            logger.error("Empty response from Ollama")
            raise ModelGatewayException("Ollama returned empty response")
        
        logger.info(f"Ollama response generated successfully ({len(result)} chars)")
        return result.strip()
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Could not connect to Ollama at {OLLAMA_ENDPOINT}. Is it running?"
        logger.error(error_msg)
        raise ModelGatewayException(error_msg) from e
    except requests.exceptions.Timeout as e:
        error_msg = f"Ollama request timed out. The model might be slow or overloaded."
        logger.error(error_msg)
        raise ModelGatewayException(error_msg) from e
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama request failed: {str(e)}"
        logger.error(error_msg)
        raise ModelGatewayException(error_msg) from e
    except (KeyError, ValueError) as e:
        error_msg = f"Invalid Ollama response format: {str(e)}"
        logger.error(error_msg)
        raise ModelGatewayException(error_msg) from e


def generate_streamed_response(
    prompt: str,
    system: str = "",
    temperature: float = 0.2
):
    """
    Generate a streamed response (placeholder for future implementation).
    
    This could be implemented to yield chunks of text as they arrive
    from either Gemini (streaming) or Ollama (with stream=True).
    
    Args:
        prompt (str): The user prompt
        system (str): System message
        temperature (float): Temperature parameter
        
    Yields:
        str: Chunks of generated text
        
    Raises:
        NotImplementedError: Currently not implemented
    """
    raise NotImplementedError("Streaming response not yet implemented")


def get_model_info() -> dict:
    """
    Get information about the current model configuration.
    
    Returns:
        dict: Dictionary containing:
            - backend: "gemini" or "ollama"
            - model: The model name being used
            - endpoint: API endpoint (for Ollama)
    """
    if USE_GEMINI:
        return {
            "backend": "gemini",
            "model": GEMINI_MODEL,
            "endpoint": "https://generativelanguage.googleapis.com"
        }
    return {
        "backend": "ollama",
        "model": OLLAMA_MODEL,
        "endpoint": OLLAMA_ENDPOINT
    }
