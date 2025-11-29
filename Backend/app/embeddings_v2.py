"""
Enhanced Embeddings Module with Gemini, OpenRouter, Ollama, and local fallback support.
"""

import os
import logging
import requests
import backoff
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openrouter.ai/api/v1")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OLLAMA_EMBEDDING_ENDPOINT = os.getenv("OLLAMA_EMBEDDING_ENDPOINT", "http://localhost:11434/api/embeddings")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MODEL_RETRY_ATTEMPTS = int(os.getenv("MODEL_RETRY_ATTEMPTS", "3"))
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "10"))

# Initialize clients
gemini_available = False
openai_available = False
sentence_transformer = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_available = True
        logger.info(f"Gemini embeddings initialized: {GEMINI_EMBEDDING_MODEL}")
    except ImportError:
        logger.warning("google-generativeai not installed")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini embeddings: {e}")

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        openai_available = True
        logger.info(f"OpenAI embeddings initialized: {OPENAI_EMBEDDING_MODEL}")
    except ImportError:
        logger.warning("OpenAI library not installed")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        openai_client = None
else:
    openai_client = None


class EmbeddingException(Exception):
    """Exception raised when embedding operations fail."""
    pass


def _normalize_text(text: str) -> str:
    """Normalize text by stripping whitespace and replacing newlines."""
    return text.strip().replace("\n", " ").replace("\r", " ")


def _load_local_model():
    """Lazy-load sentence-transformers model."""
    global sentence_transformer
    if sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            sentence_transformer = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
            logger.info(f"Loaded local embedding model: {LOCAL_EMBEDDING_MODEL}")
        except ImportError:
            raise EmbeddingException("sentence-transformers not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            raise EmbeddingException(f"Failed to load local model: {e}")
    return sentence_transformer


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=MODEL_RETRY_ATTEMPTS
)
def _get_gemini_embedding(text: str) -> List[float]:
    """Get embedding using Gemini API with retry."""
    if not gemini_available:
        raise EmbeddingException("Gemini not available")
    
    try:
        import google.generativeai as genai
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        
        if not result or "embedding" not in result:
            raise EmbeddingException("Invalid response from Gemini")
        
        embedding = result["embedding"]
        logger.debug(f"Generated Gemini embedding: dim={len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Gemini embedding error: {e}")
        raise EmbeddingException(f"Gemini embedding failed: {e}")


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=MODEL_RETRY_ATTEMPTS
)
def _get_openai_embedding(text: str) -> List[float]:
    """Get embedding using OpenAI/OpenRouter API with retry."""
    if not openai_available or not openai_client:
        raise EmbeddingException("OpenAI not available")
    
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text
        )
        
        if not response.data or len(response.data) == 0:
            raise EmbeddingException("Empty response from OpenAI")
        
        embedding = response.data[0].embedding
        logger.debug(f"Generated OpenAI embedding: dim={len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        raise EmbeddingException(f"OpenAI embedding failed: {e}")


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=MODEL_RETRY_ATTEMPTS
)
def _get_ollama_embedding(text: str) -> List[float]:
    """Get embedding using Ollama with retry."""
    try:
        response = requests.post(
            OLLAMA_EMBEDDING_ENDPOINT,
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
            timeout=HTTP_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        if "embedding" not in result:
            raise EmbeddingException("Invalid response from Ollama")
        
        embedding = result["embedding"]
        logger.debug(f"Generated Ollama embedding: dim={len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Ollama embedding error: {e}")
        raise EmbeddingException(f"Ollama embedding failed: {e}")


def _get_local_embedding(text: str) -> List[float]:
    """Get embedding using local sentence-transformers model."""
    try:
        model = _load_local_model()
        embedding = model.encode(text, convert_to_tensor=False).tolist()
        logger.debug(f"Generated local embedding: dim={len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Local embedding error: {e}")
        raise EmbeddingException(f"Local embedding failed: {e}")


def get_embedding(text: str, prefer_local: bool = False) -> List[float]:
    """
    Get embedding vector for text using best available method.
    
    Priority order:
    1. Gemini (if available and not prefer_local)
    2. OpenAI/OpenRouter (if available and not prefer_local)
    3. Ollama (local)
    4. Sentence-transformers (local fallback)
    
    Args:
        text: Text to embed
        prefer_local: If True, skip online APIs and use local models
        
    Returns:
        List[float]: Embedding vector
        
    Raises:
        EmbeddingException: If all methods fail
    """
    normalized_text = _normalize_text(text)
    
    if not normalized_text:
        raise EmbeddingException("Cannot embed empty text")
    
    errors = []
    
    # Try online models first (unless prefer_local)
    if not prefer_local:
        # Try Gemini
        if gemini_available:
            try:
                return _get_gemini_embedding(normalized_text)
            except EmbeddingException as e:
                errors.append(f"Gemini: {e}")
                logger.warning(f"Gemini embedding failed, trying fallback")
        
        # Try OpenAI
        if openai_available:
            try:
                return _get_openai_embedding(normalized_text)
            except EmbeddingException as e:
                errors.append(f"OpenAI: {e}")
                logger.warning(f"OpenAI embedding failed, trying fallback")
    
    # Try Ollama
    try:
        return _get_ollama_embedding(normalized_text)
    except EmbeddingException as e:
        errors.append(f"Ollama: {e}")
        logger.warning(f"Ollama embedding failed, trying local model")
    
    # Final fallback: local sentence-transformers
    try:
        return _get_local_embedding(normalized_text)
    except EmbeddingException as e:
        errors.append(f"Local: {e}")
        logger.error(f"All embedding methods failed: {errors}")
        raise EmbeddingException(f"All embedding methods failed. Errors: {'; '.join(errors)}")


def get_embeddings_batch(texts: List[str], prefer_local: bool = False) -> List[List[float]]:
    """
    Get embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        prefer_local: If True, use local models only
        
    Returns:
        List of embedding vectors
        
    Raises:
        EmbeddingException: If any embedding fails
    """
    embeddings = []
    for text in texts:
        embeddings.append(get_embedding(text, prefer_local=prefer_local))
    return embeddings


def get_embedding_dimension() -> int:
    """
    Get the dimension of embeddings from the current provider.
    
    Returns:
        int: Embedding dimension
    """
    # Test with a sample text
    try:
        sample = get_embedding("test")
        return len(sample)
    except:
        # Default dimensions
        if gemini_available:
            return 768  # Gemini text-embedding-004
        elif openai_available:
            return 1536  # OpenAI text-embedding-3-small
        else:
            return 384  # all-MiniLM-L6-v2 default
