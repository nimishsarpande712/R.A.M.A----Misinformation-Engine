"""
Embeddings helper - Unified interface for generating embeddings (Gemini + Ollama)
"""

import os
import logging
import requests
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/embeddings")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Initialize Gemini client if key is available
USE_GEMINI = False
genai = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        USE_GEMINI = True
        logger.info(f"Gemini embeddings initialized with model: {GEMINI_EMBEDDING_MODEL}")
    except ImportError:
        logger.warning("google-generativeai library not installed. Falling back to Ollama.")
else:
    logger.info(f"No GEMINI_API_KEY found. Using Ollama endpoint: {OLLAMA_ENDPOINT}")


class EmbeddingException(Exception):
    """Exception raised when embedding operations fail."""
    pass


def _normalize_text(text: str) -> str:
    """
    Normalize text by stripping whitespace and replacing newlines with spaces.
    
    Args:
        text (str): The text to normalize
        
    Returns:
        str: Normalized text
    """
    return text.strip().replace("\n", " ").replace("\r", " ")


def get_embedding(text: str) -> list:
    """
    Get embedding vector for a single text using Gemini or Ollama.
    
    Automatically falls back to Ollama if Gemini is unavailable.
    
    Args:
        text (str): The text to embed
        
    Returns:
        list: A list of floats representing the embedding vector
        
    Raises:
    EmbeddingException: If both Gemini and Ollama fail
    """
    # Normalize the text
    normalized_text = _normalize_text(text)
    
    if not normalized_text:
        raise EmbeddingException("Cannot embed empty text")
    
    if USE_GEMINI:
        try:
            return _get_gemini_embedding(normalized_text)
        except EmbeddingException as e:
            # Fall back to Ollama if Gemini fails
            logger.warning(f"Gemini embedding failed, attempting Ollama fallback: {str(e)}")
            try:
                return _get_ollama_embedding(normalized_text)
            except EmbeddingException:
                # If both fail, re-raise the original error
                raise
    return _get_ollama_embedding(normalized_text)

def _get_gemini_embedding(text: str) -> list:
    """
    Get embedding using Gemini API.

    Args:
        text (str): The normalized text to embed

    Returns:
        list: Embedding vector

    Raises:
        EmbeddingException: If Gemini request fails
    """
    try:
        logger.debug(f"Getting Gemini embedding for text: {text[:50]}...")

        # Using google-generativeai embed_content
        result = genai.embed_content(model=GEMINI_EMBEDDING_MODEL, content=text)
        # Support both possible shapes: list or dict with 'values'
        embedding = None
        if isinstance(result, dict):
            # Newer SDK returns {'embedding': [...]}
            if isinstance(result.get("embedding"), list):
                embedding = result["embedding"]
            elif isinstance(result.get("embedding"), dict) and isinstance(result["embedding"].get("values"), list):
                embedding = result["embedding"]["values"]
        if embedding is None:
            raise EmbeddingException("Gemini returned empty embedding")

        logger.debug(f"Gemini embedding generated ({len(embedding)} dimensions)")
        return embedding

    except Exception as e:
        logger.error(f"Gemini embedding request failed: {str(e)}")
        raise EmbeddingException(f"Gemini API error: {str(e)}") from e


def _get_ollama_embedding(text: str) -> list:
    """
    Get embedding using Ollama local HTTP endpoint.
    
    Args:
        text (str): The normalized text to embed
        
    Returns:
        list: Embedding vector
        
    Raises:
        EmbeddingException: If Ollama request fails
    """
    try:
        logger.debug(f"Getting Ollama embedding for text: {text[:50]}...")
        
        # Prepare request payload
        payload = {
            "model": OLLAMA_EMBEDDING_MODEL,
            "prompt": text
        }
        
        logger.debug(f"Sending request to Ollama: {OLLAMA_ENDPOINT}")
        response = requests.post(
            OLLAMA_ENDPOINT,
            json=payload,
            timeout=60  # 1 minute timeout for embedding requests
        )
        
        if response.status_code != 200:
            error_msg = f"Ollama HTTP {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise EmbeddingException(error_msg)
        
        data = response.json()
        embedding = data.get("embedding")
        
        if embedding is None:
            logger.error("Empty embedding from Ollama")
            raise EmbeddingException("Ollama returned empty embedding")
        
        if not isinstance(embedding, list):
            logger.error(f"Invalid embedding type from Ollama: {type(embedding)}")
            raise EmbeddingException("Ollama returned invalid embedding format")
        
        logger.debug(f"Ollama embedding generated ({len(embedding)} dimensions)")
        return embedding
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Could not connect to Ollama at {OLLAMA_ENDPOINT}. Is it running?"
        logger.error(error_msg)
        raise EmbeddingException(error_msg) from e
    except requests.exceptions.Timeout as e:
        error_msg = f"Ollama embedding request timed out."
        logger.error(error_msg)
        raise EmbeddingException(error_msg) from e
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama request failed: {str(e)}"
        logger.error(error_msg)
        raise EmbeddingException(error_msg) from e
    except (KeyError, ValueError, TypeError) as e:
        error_msg = f"Invalid Ollama response format: {str(e)}"
        logger.error(error_msg)
        raise EmbeddingException(error_msg) from e


def batch_get_embeddings(texts: list) -> list:
    """
    Get embeddings for multiple texts in a batch.
    
    For Gemini, this uses per-item embedding (SDK doesn't batch multiple items at once).
    For Ollama, texts are processed individually.
    
    Args:
        texts (list): List of text strings to embed
        
    Returns:
        list: List of embedding vectors (each is a list of floats)
        
    Raises:
        EmbeddingException: If batch embedding fails
    """
    if not texts:
        raise EmbeddingException("Cannot embed empty text list")
    
    logger.info(f"Getting embeddings for {len(texts)} texts")
    
    if USE_GEMINI:
        try:
            return _batch_get_gemini_embeddings(texts)
        except EmbeddingException as e:
            # Fall back to Ollama
            logger.warning(f"Gemini batch embedding failed, falling back to Ollama: {str(e)}")
            try:
                return _batch_get_ollama_embeddings(texts)
            except EmbeddingException:
                raise
    return _batch_get_ollama_embeddings(texts)


def _batch_get_gemini_embeddings(texts: list) -> list:
    """
    Get multiple embeddings using Gemini API.

    Args:
        texts (list): List of texts to embed

    Returns:
        list: List of embeddings

    Raises:
        EmbeddingException: If request fails
    """
    try:
        logger.debug(f"Getting batch Gemini embeddings for {len(texts)} texts")
        embeddings: List[list] = []
        for text in texts:
            emb = _get_gemini_embedding(_normalize_text(text))
            embeddings.append(emb)
        logger.info(f"Generated {len(embeddings)} Gemini embeddings")
        return embeddings
    except Exception as e:
        logger.error(f"Gemini batch embedding failed: {str(e)}")
        raise EmbeddingException(f"Gemini batch API error: {str(e)}") from e


def _batch_get_ollama_embeddings(texts: list) -> list:
    """
    Get multiple embeddings using Ollama (processed individually).
    
    Args:
        texts (list): List of texts to embed
        
    Returns:
        list: List of embeddings
        
    Raises:
        EmbeddingException: If any request fails
    """
    try:
        logger.debug(f"Getting batch Ollama embeddings for {len(texts)} texts")
        
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = _get_ollama_embedding(_normalize_text(text))
                embeddings.append(embedding)
                logger.debug(f"Processed {i+1}/{len(texts)} embeddings")
            except EmbeddingException as e:
                logger.error(f"Failed to embed text {i}: {str(e)}")
                raise
        
        logger.info(f"Generated {len(embeddings)} Ollama embeddings")
        return embeddings
        
    except EmbeddingException:
        raise
    except Exception as e:
        logger.error(f"Ollama batch embedding failed: {str(e)}")
        raise EmbeddingException(f"Ollama batch error: {str(e)}") from e


def get_embedding_dimension() -> int:
    """
    Get the dimension of the embedding vector.
    
    Returns:
        int: Dimension of the embedding (e.g., 384 for nomic-embed-text, 512 for text-embedding-3-small)
        
    Note:
        This returns a static value based on the model being used.
        - text-embedding-3-small: 512 dimensions
        - nomic-embed-text: 768 dimensions
    """
    if USE_GEMINI:
        # text-embedding-004 returns 768 dimensions
        if "text-embedding-004" in GEMINI_EMBEDDING_MODEL or "embedding-001" in GEMINI_EMBEDDING_MODEL:
            return 768
        # Default fallback
        return 768
    if "nomic" in OLLAMA_EMBEDDING_MODEL:
        return 768
    return 384  # Default for other Ollama models


def get_embedding_info() -> dict:
    """
    Get information about the current embedding configuration.
    
    Returns:
        dict: Dictionary containing:
            - backend: "gemini" or "ollama"
            - model: The model name being used
            - endpoint: API endpoint
            - dimensions: Embedding vector dimensions
    """
    if USE_GEMINI:
        return {
            "backend": "gemini",
            "model": GEMINI_EMBEDDING_MODEL,
            "endpoint": "https://generativelanguage.googleapis.com",
            "dimensions": get_embedding_dimension()
        }
    return {
        "backend": "ollama",
        "model": OLLAMA_EMBEDDING_MODEL,
        "endpoint": OLLAMA_ENDPOINT,
        "dimensions": get_embedding_dimension()
    }
