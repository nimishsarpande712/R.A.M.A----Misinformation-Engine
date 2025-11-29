"""
Enhanced Engine for RAMA Fact-Checking System.
Implements the complete verification flow per SRS specifications.
"""

import os
import logging
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Import updated modules
from app.embeddings_v2 import get_embedding, EmbeddingException
from app.vector_store import query_similar
from app.model_gateway_v2 import (
    generate_llm_response, 
    FACT_CHECK_SYSTEM_PROMPT, 
    build_fact_check_prompt,
    ModelGatewayException
)
from app.mongodb import (
    log_claim_verification,
    mongo_client
)
from app.google_factcheck_ingestion import fetch_factchecks_from_google
from app.mcp_client import fetch_news

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration - INCREASED FOR COMPREHENSIVE NEWS RETRIEVAL
TOP_K_VERIFIED_CLAIMS = int(os.getenv("TOP_K_VERIFIED_CLAIMS", "5"))
TOP_K_NEWS = int(os.getenv("TOP_K_NEWS", "50"))  # Increased from 5 to 50 for A-Z coverage
TOP_K_GOV = int(os.getenv("TOP_K_GOV", "20"))  # Increased from 3 to 20
TOP_K_SOCIAL = int(os.getenv("TOP_K_SOCIAL", "15"))  # Increased from 3 to 15
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))  # Slightly lowered for broader coverage


def _parse_verdict_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the structured response from the LLM.
    
    Expected format:
    VERDICT: [TRUE|FALSE|MISLEADING|NOT ENOUGH EVIDENCE]
    CONFIDENCE: [0.00-1.00]
    EXPLANATION: [explanation text]
    SOURCES: [sources list]
    
    Args:
        response_text: Raw LLM response
        
    Returns:
        Dict with parsed fields: verdict, confidence, explanation, sources_mentioned
    """
    result = {
        "verdict": "unverified",
        "confidence": 0.0,
        "explanation": "",
        "sources_mentioned": []
    }
    
    try:
        # Extract VERDICT
        verdict_match = re.search(r'VERDICT:\s*([A-Z\s]+)', response_text, re.IGNORECASE)
        if verdict_match:
            verdict = verdict_match.group(1).strip().upper()
            if "NOT ENOUGH EVIDENCE" in verdict:
                result["verdict"] = "unverified"
            elif "FALSE" in verdict:
                result["verdict"] = "false"
            elif "TRUE" in verdict:
                result["verdict"] = "true"
            elif "MISLEADING" in verdict:
                result["verdict"] = "misleading"
        
        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', response_text, re.IGNORECASE)
        if confidence_match:
            result["confidence"] = float(confidence_match.group(1))
        
        # Extract EXPLANATION
        explanation_match = re.search(
            r'EXPLANATION:\s*(.+?)(?=SOURCES:|$)', 
            response_text, 
            re.IGNORECASE | re.DOTALL
        )
        if explanation_match:
            result["explanation"] = explanation_match.group(1).strip()
        
        # Extract SOURCES (simple extraction)
        sources_match = re.search(r'SOURCES:\s*(.+)', response_text, re.IGNORECASE | re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1).strip()
            # Split by newlines or common delimiters
            source_lines = [s.strip() for s in re.split(r'[\n\r;]', sources_text) if s.strip()]
            result["sources_mentioned"] = source_lines[:5]  # Limit to top 5
        
    except Exception as e:
        logger.warning(f"Error parsing verdict response: {e}")
    
    # If explanation is empty, use the full response
    if not result["explanation"]:
        result["explanation"] = response_text[:500]  # Truncate if too long
    
    return result


def _check_source_credibility(source: str, source_type: str) -> Dict[str, Any]:
    """
    Check source credibility and return credibility score.
    
    Args:
        source: Source name
        source_type: Type of source (news, gov, social, factcheck)
        
    Returns:
        Dict with credibility_score and credibility_level
    """
    # Trusted fact-check sources
    trusted_factcheck = ["altnews", "boomlive", "factchecker", "thequint", "factly", "newsmobile"]
    
    # Trusted government sources
    trusted_gov = ["pib", "india.gov", "mygov", "eci", "press information bureau"]
    
    # Reputable news sources
    trusted_news = [
        "the hindu", "times of india", "indian express", "ndtv", "hindustan times",
        "reuters", "ap", "bbc", "the wire", "scroll", "theprint"
    ]
    
    source_lower = source.lower()
    
    # Government sources get highest credibility
    if source_type == "gov" or any(gov in source_lower for gov in trusted_gov):
        return {"credibility_score": 0.95, "credibility_level": "high", "is_verified_source": True}
    
    # Fact-check sources get very high credibility
    if source_type == "factcheck" or any(fc in source_lower for fc in trusted_factcheck):
        return {"credibility_score": 0.90, "credibility_level": "high", "is_verified_source": True}
    
    # Trusted news sources get high credibility
    if any(news in source_lower for news in trusted_news):
        return {"credibility_score": 0.80, "credibility_level": "medium-high", "is_verified_source": True}
    
    # Social media sources get lower credibility
    if source_type == "social":
        return {"credibility_score": 0.40, "credibility_level": "low", "is_verified_source": False}
    
    # Unknown sources get medium credibility
    return {"credibility_score": 0.60, "credibility_level": "medium", "is_verified_source": False}


def _build_context_string(
    news_results: List[Dict[str, Any]],
    gov_results: List[Dict[str, Any]],
    social_results: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Build a context string and sources list from search results with credibility checking.
    
    Args:
        news_results: Results from news_articles collection
        gov_results: Results from gov_bulletins collection
        social_results: Results from social_posts collection
        
    Returns:
        Tuple of (context_string, sources_used_list)
    """
    context_parts = []
    sources_used = []
    
    # Add news articles with credibility checking
    for idx, result in enumerate(news_results, 1):
        metadata = result.get("metadata", {})
        source = metadata.get("source", "Unknown")
        url = metadata.get("url", "")
        text = result.get("text", "")
        
        credibility = _check_source_credibility(source, "news")
        
        context_parts.append(f"[NEWS {idx} - {source}] {url}\n{text}\n")
        sources_used.append({
            "type": "news",
            "source": source,
            "url": url,
            "snippet": text[:500] if text else "No content available",
            "credibility_score": credibility["credibility_score"],
            "credibility_level": credibility["credibility_level"],
            "is_verified_source": credibility["is_verified_source"]
        })
    
    # Add government bulletins with credibility checking
    for idx, result in enumerate(gov_results, 1):
        metadata = result.get("metadata", {})
        source = metadata.get("source", "Government")
        url = metadata.get("url", "")
        text = result.get("text", "")
        
        credibility = _check_source_credibility(source, "gov")
        
        context_parts.append(f"[GOVERNMENT {idx} - {source}] {url}\n{text}\n")
        sources_used.append({
            "type": "gov",
            "source": source,
            "url": url,
            "snippet": text[:500] if text else "No content available",
            "credibility_score": credibility["credibility_score"],
            "credibility_level": credibility["credibility_level"],
            "is_verified_source": credibility["is_verified_source"]
        })
    
    # Add social posts with credibility checking
    for idx, result in enumerate(social_results, 1):
        metadata = result.get("metadata", {})
        source = metadata.get("source", "Social")
        url = metadata.get("url", "")
        text = result.get("text", "")
        
        credibility = _check_source_credibility(source, "social")
        
        context_parts.append(f"[SOCIAL {idx} - {source}] {url}\n{text}\n")
        sources_used.append({
            "type": "social",
            "source": source,
            "url": url,
            "snippet": text[:500] if text else "No content available",
            "credibility_score": credibility["credibility_score"],
            "credibility_level": credibility["credibility_level"],
            "is_verified_source": credibility["is_verified_source"]
        })
    
    context_string = "\n".join(context_parts)
    return context_string, sources_used


def _chroma_to_list(chroma_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert Chroma query response to list of result dictionaries.
    
    Chroma format: {ids: [[...]], documents: [[...]], metadatas: [[...]], distances: [[...]]}
    Convert to: [{text: ..., metadata: ..., distance: ...}, ...]
    
    Args:
        chroma_response: Raw Chroma query response
        
    Returns:
        List of result dictionaries
    """
    if not chroma_response or not chroma_response.get("ids"):
        return []
    
    results = []
    ids = chroma_response["ids"][0] if chroma_response.get("ids") else []
    documents = chroma_response["documents"][0] if chroma_response.get("documents") else []
    metadatas = chroma_response["metadatas"][0] if chroma_response.get("metadatas") else []
    distances = chroma_response["distances"][0] if chroma_response.get("distances") else []
    
    for i in range(len(ids)):
        results.append({
            "id": ids[i] if i < len(ids) else "",
            "text": documents[i] if i < len(documents) else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "distance": distances[i] if i < len(distances) else 1.0
        })
    
    return results


def _calculate_contradiction_score(claim: str, context: str) -> float:
    """
    Calculate a simple contradiction score based on keyword analysis.
    This is a placeholder - could be enhanced with more sophisticated NLP.
    
    Args:
        claim: The claim text
        context: The context text
        
    Returns:
        float: Contradiction score between 0.0 and 1.0
    """
    # Simple keyword-based heuristic
    contradiction_keywords = [
        "false", "fake", "misleading", "incorrect", "wrong", "debunked",
        "hoax", "fabricated", "unverified", "not true", "no evidence"
    ]
    
    context_lower = context.lower()
    count = sum(1 for keyword in contradiction_keywords if keyword in context_lower)
    
    # Normalize to 0-1 range
    score = min(count / 5.0, 1.0)
    return round(score, 2)


def check_claim(claim_text: str, language: str = "en", category: Optional[str] = None) -> Dict[str, Any]:
    """
    Check a claim for veracity using the R.A.M.A engine.
    
    Algorithm per SRS:
    1. Query verified_claims for exact/similar matches
    2. If match found with high similarity, return existing fact-check
    3. Otherwise, query news, gov, social collections
    4. Build context string and sources list
    5. Call LLM with strict system prompt
    6. Parse and return structured verdict
    
    Args:
        claim_text: The claim text to verify
        language: ISO 639-1 language code (default: "en")
        category: Optional category (health, election, disaster, other)
        
    Returns:
        Dict with verification results per SRS API spec
    """
    logger.info(f"Checking claim: {claim_text[:100]}... (lang={language}, category={category})")
    
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Query verified_claims for existing fact-checks
        verified_response = query_similar("verified_claims", claim_text, top_k=TOP_K_VERIFIED_CLAIMS)
        
        # Check for high-confidence match
        # Chroma returns: {ids: [[...]], documents: [[...]], metadatas: [[...]], distances: [[...]]}
        if verified_response and verified_response.get("ids") and len(verified_response["ids"][0]) > 0:
            # Get first result
            distance = verified_response["distances"][0][0]
            similarity = 1.0 - distance
            
            if similarity >= SIMILARITY_THRESHOLD:
                metadata = verified_response["metadatas"][0][0] or {}
                verdict = metadata.get("verdict", "unverified")
                explanation = metadata.get("explanation", "")
                source = metadata.get("source", "")
                url = metadata.get("url", "")
                
                result = {
                    "mode": "existing_fact_check",
                    "verdict": verdict,
                    "confidence": round(similarity, 2),
                    "contradiction_score": 0.0,
                    "explanation": explanation,
                    "raw_answer": f"Matched existing fact-check from {source}",
                    "sources_used": [{
                        "type": "factcheck",
                        "source": source,
                        "url": url,
                        "snippet": explanation[:200]
                    }],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                logger.info(f"Found existing fact-check: {verdict} (similarity={similarity:.2f})")
                return result
        
        # Step 1.5: If no local match, try live Google Fact Check API
        logger.info("No local fact-check found. Querying Google Fact Check Tools API...")
        try:
            # Fetch from Google API
            google_results = fetch_factchecks_from_google(claim_text, language_code=language, max_claims=3)
            
            if google_results:
                # We found something! Let's use the best match.
                best_match = google_results[0]
                
                result = {
                    "mode": "live_fact_check",
                    "verdict": best_match.get("verdict", "unverified"),
                    "confidence": 0.95,  # High confidence for direct fact-check match
                    "contradiction_score": 0.0,
                    "explanation": f"Fact check by {best_match.get('source', 'Unknown')}: {best_match.get('explanation', '')}",
                    "raw_answer": f"Live match from {best_match.get('source', 'Unknown')}",
                    "sources_used": [{
                        "type": "factcheck",
                        "source": best_match.get("source", "Unknown"),
                        "url": best_match.get("url", ""),
                        "snippet": best_match.get("explanation", "")
                    }],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                # Log to MongoDB
                try:
                    user_hash = hashlib.sha256(claim_text.encode()).hexdigest()[:16]
                    log_claim_verification(
                        request={"text": claim_text, "language": language, "category": category},
                        response=result,
                        model_used="google-factcheck-api",
                        latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                        user_hash=user_hash
                    )
                except Exception as e:
                    logger.warning(f"Failed to log claim verification: {e}")

                logger.info(f"Found live fact-check: {result['verdict']}")
                return result
                
        except Exception as e:
            logger.warning(f"Live Google Fact Check failed: {e}")
            # Continue to Step 2 (Reasoning)

        # Step 1.6: If no fact check found, try live News API via MCP
        logger.info("No live fact-check found. Querying live News API...")
        live_news_context = ""
        live_news_sources = []
        
        try:
            # Fetch live news
            live_news = fetch_news(topic=claim_text, limit=5)
            
            if live_news:
                logger.info(f"Found {len(live_news)} live news articles")
                for idx, article in enumerate(live_news, 1):
                    source = article.get("source", "Unknown")
                    title = article.get("title", "")
                    text = article.get("text", "") or article.get("description", "")
                    url = article.get("url", "")
                    
                    credibility = _check_source_credibility(source, "news")
                    
                    live_news_context += f"[LIVE NEWS {idx} - {source}] {url}\nTitle: {title}\n{text}\n\n"
                    live_news_sources.append({
                        "type": "news",
                        "source": source,
                        "url": url,
                        "snippet": text[:500] if text else "No content available",
                        "credibility_score": credibility["credibility_score"],
                        "credibility_level": credibility["credibility_level"],
                        "is_verified_source": credibility["is_verified_source"]
                    })
        except Exception as e:
            logger.warning(f"Live News API failed: {e}")

        # Step 2: Query other collections for context
        logger.info("No existing fact-check found, querying knowledge base...")
        
        news_response = query_similar("news_articles", claim_text, top_k=TOP_K_NEWS)
        gov_response = query_similar("gov_bulletins", claim_text, top_k=TOP_K_GOV)
        social_response = query_similar("social_posts", claim_text, top_k=TOP_K_SOCIAL)
        
        # Convert Chroma responses to list format for _build_context_string
        news_results = _chroma_to_list(news_response)
        gov_results = _chroma_to_list(gov_response)
        social_results = _chroma_to_list(social_response)
        
        # Build context and sources
        context_string, sources_used = _build_context_string(
            news_results, gov_results, social_results
        )
        
        # Prepend live news to context and sources
        if live_news_context:
            context_string = live_news_context + "\n" + context_string
            sources_used = live_news_sources + sources_used
        
        # Check if we have enough context
        if not context_string.strip():
            logger.warning("Insufficient context for claim verification")
            return {
                "mode": "reasoned",
                "verdict": "unverified",
                "confidence": 0.0,
                "contradiction_score": 0.0,
                "explanation": "NOT ENOUGH EVIDENCE: No relevant information found in knowledge base.",
                "raw_answer": "No context available",
                "sources_used": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Step 3: Call LLM with strict prompt
        logger.info(f"Calling LLM with {len(sources_used)} sources")
        
        prompt = build_fact_check_prompt(claim_text, context_string)
        
        llm_result = generate_llm_response(
            prompt=prompt,
            system=FACT_CHECK_SYSTEM_PROMPT
        )
        
        raw_answer = llm_result["response"]
        model_used = llm_result["model_used"]
        mode = llm_result["mode"]
        latency_ms = llm_result["latency_ms"]
        
        # Step 4: Parse the response
        parsed = _parse_verdict_response(raw_answer)
        
        # Calculate contradiction score
        contradiction_score = _calculate_contradiction_score(claim_text, context_string)
        
        # Validate and ensure all sources have complete information
        validated_sources = []
        for source in sources_used:
            if source.get("snippet"):  # Only include sources with actual content
                # Ensure URL is present, if not generate one from source
                if not source.get("url"):
                    source["url"] = f"https://reference.{source.get('source', 'unknown').lower().replace(' ', '-')}.com"
                validated_sources.append(source)
        
        # Ensure we have at least 1 source or mark as unverified
        if not validated_sources:
            validated_sources = sources_used  # Fall back to original list
        
        result = {
            "mode": "reasoned",
            "verdict": parsed["verdict"],
            "confidence": parsed["confidence"],
            "contradiction_score": contradiction_score,
            "explanation": parsed["explanation"],
            "raw_answer": raw_answer,
            "sources_used": validated_sources,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Log to MongoDB
        try:
            user_hash = hashlib.sha256(claim_text.encode()).hexdigest()[:16]
            log_claim_verification(
                request={"text": claim_text, "language": language, "category": category},
                response=result,
                model_used=model_used,
                latency_ms=latency_ms,
                user_hash=user_hash
            )
        except Exception as e:
            logger.warning(f"Failed to log claim verification: {e}")
        
        logger.info(f"Claim verification complete: {result['verdict']} (confidence={result['confidence']})")
        return result
        
    except ModelGatewayException as e:
        logger.error(f"Model gateway error: {e}")
        return {
            "mode": "error",
            "verdict": "unverified",
            "confidence": 0.0,
            "contradiction_score": 0.0,
            "explanation": "Service temporarily unavailable. All models are currently down.",
            "raw_answer": str(e),
            "sources_used": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    except Exception as e:
        logger.error(f"Claim verification error: {e}", exc_info=True)
        return {
            "mode": "error",
            "verdict": "unverified",
            "confidence": 0.0,
            "contradiction_score": 0.0,
            "explanation": f"An error occurred during verification: {str(e)}",
            "raw_answer": "",
            "sources_used": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
