"""
Core claim checking engine for R.A.M.A News.
"""

import logging
from typing import Optional, Dict, Any, List

from app.vector_store import query_similar
from app.model_gateway import generate_llm_response
from app.google_factcheck_ingestion import fetch_factchecks_from_google
from app.mcp_client import fetch_news

logger = logging.getLogger(__name__)


def check_claim(claim_text: str, language: str = "en") -> Dict[str, Any]:
    """
    Check a claim for veracity using the R.A.M.A engine.
    
    Algorithm:
    1) Query verified_claims for top_k=3 similar claims.
       - If a hit exists with metadata["verdict"] in {"true","false","misleading"}, return:
         {"mode":"existing_fact_check","verdict":..., "explanation":..., "source":...}
    2) Otherwise query news_articles, gov_bulletins, social_posts top_k=3 each.
       - Build a CONTEXT string by joining snippets prefixed with "[NEWS - source] url".
       - Build a list sources_used = [{ "type": "news"|"gov"|"social", "source":..., "url":... }, ...]
    3) Create a strict system prompt for fact-checking.
    4) Call generate_llm_response and return:
       {"mode":"reasoned","raw_answer":..., "sources_used": sources_used}
    
    Args:
        claim_text (str): The claim text to check
        language (str): ISO 639-1 language code (e.g., 'en'). Defaults to 'en'
                       
    Returns:
        Dict[str, Any]: Result object containing:
            - mode: str - Either "existing_fact_check" or "reasoned"
            - verdict: str - One of 'TRUE', 'FALSE', 'UNVERIFIED', 'NOT ENOUGH EVIDENCE'
            - explanation: str - 2-3 line explanation
            - sources_used: list - List of source objects with type, source, url
            - raw_answer: str - Full LLM response (for reasoned mode)
            
    Raises:
        Exception: If claim checking fails
    """
    logger.info(f"Checking claim: {claim_text[:100]}... (language: {language})")
    
    try:
        # Step 1: Query verified_claims for existing fact checks
        verified_results = query_similar("verified_claims", claim_text, top_k=3)
        
        # Check if we found a matching existing fact check
        for i, doc in enumerate(verified_results.get("documents", [[]])[0]):
            metadata = verified_results.get("metadatas", [[]])[0][i] if verified_results.get("metadatas") else {}
            verdict = metadata.get("verdict", "").lower()
            
            if verdict in {"true", "false", "misleading"}:
                logger.info(f"Found existing fact check with verdict: {verdict}")
                return {
                    "mode": "existing_fact_check",
                    "verdict": verdict.upper(),
                    "explanation": metadata.get("explanation", ""),
                    "source": metadata.get("source", ""),
                    "claim": claim_text,
                    "language": language
                }
        
        # Step 1.5: Live Google Fact Check
        try:
            google_results = fetch_factchecks_from_google(claim_text, language_code=language, max_claims=1)
            if google_results:
                best = google_results[0]
                return {
                    "mode": "live_fact_check",
                    "verdict": best.get("verdict", "UNVERIFIED"),
                    "explanation": f"Fact check by {best.get('source')}: {best.get('explanation')}",
                    "source": best.get("source"),
                    "claim": claim_text,
                    "language": language
                }
        except Exception as e:
            logger.warning(f"Live Google Fact Check failed: {e}")

        # Step 2: Query multiple sources for context
        logger.info("No existing fact check found. Querying sources for context...")
        
        news_results = query_similar("news_articles", claim_text, top_k=3)
        gov_results = query_similar("gov_bulletins", claim_text, top_k=3)
        social_results = query_similar("social_posts", claim_text, top_k=3)
        
        # Build context string and sources_used list
        context_parts = []
        sources_used: List[Dict[str, Any]] = []
        
        # Live News Fetch
        try:
            live_news = fetch_news(topic=claim_text, limit=3)
            for article in live_news:
                source = article.get("source", "Unknown")
                url = article.get("url", "")
                text = (article.get("title", "") or "") + " - " + (article.get("description", "") or "")
                context_parts.append(f"[LIVE NEWS - {source}] {url}\n{text}\n---")
                sources_used.append({
                    "type": "news",
                    "source": source,
                    "url": url
                })
        except Exception as e:
            logger.warning(f"Live News Fetch failed: {e}")

        # Process news articles
        for i, doc in enumerate(news_results.get("documents", [[]])[0]):
            metadata = news_results.get("metadatas", [[]])[0][i] if news_results.get("metadatas") else {}
            url = metadata.get("url", "unknown")
            source = metadata.get("source", "unknown")
            context_parts.append(f"[NEWS - {source}] {url}\n{doc}\n---")
            sources_used.append({
                "type": "news",
                "source": source,
                "url": url
            })
        
        # Process government bulletins
        for i, doc in enumerate(gov_results.get("documents", [[]])[0]):
            metadata = gov_results.get("metadatas", [[]])[0][i] if gov_results.get("metadatas") else {}
            url = metadata.get("url", "unknown")
            source = metadata.get("source", "unknown")
            context_parts.append(f"[GOV - {source}] {url}\n{doc}\n---")
            sources_used.append({
                "type": "gov",
                "source": source,
                "url": url
            })
        
        # Process social posts
        for i, doc in enumerate(social_results.get("documents", [[]])[0]):
            metadata = social_results.get("metadatas", [[]])[0][i] if social_results.get("metadatas") else {}
            url = metadata.get("url", "unknown")
            source = metadata.get("source", "unknown")
            context_parts.append(f"[SOCIAL - {source}] {url}\n{doc}\n---")
            sources_used.append({
                "type": "social",
                "source": source,
                "url": url
            })
        
        context = "\n".join(context_parts) if context_parts else "No relevant sources found."
        
        # Step 3: Create strict system prompt
        system_prompt = (
            "You are a strict misinformation checker. Use ONLY the CONTEXT provided. "
            "Classify the claim as one of: TRUE, FALSE, UNVERIFIED. "
            "If the context is insufficient, say 'NOT ENOUGH EVIDENCE'. "
            "Provide a 2-3 line explanation and list which context sources you used."
        )
        
        # Step 4: Call LLM with low temperature (deterministic)
        prompt = f"Claim to verify: {claim_text}\n\nCONTEXT:\n{context}"
        raw_answer = generate_llm_response(
            prompt=prompt,
            system=system_prompt,
            temperature=0.2
        )
        
        logger.info(f"LLM response received ({len(raw_answer)} chars)")
        
        return {
            "mode": "reasoned",
            "raw_answer": raw_answer,
            "sources_used": sources_used,
            "claim": claim_text,
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error during claim checking: {str(e)}", exc_info=True)
        raise
