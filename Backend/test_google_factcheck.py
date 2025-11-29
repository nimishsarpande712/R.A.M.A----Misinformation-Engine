"""
Test script for Google Fact Check Tools API integration.

Usage:
    Set GOOGLE_FACTCHECK_API_KEY environment variable first, then run this script.
    
    Example:
        $env:GOOGLE_FACTCHECK_API_KEY = "your-api-key"
        python test_google_factcheck.py
"""

import os
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.google_factcheck_ingestion import (
    fetch_factchecks_from_google,
    ingest_factchecks_from_google,
    ingest_multiple_queries_from_google,
    normalize_google_response,
)


def test_single_query():
    """Test fetching fact checks for a single query."""
    print("\n=== Test: Single Query ===")
    
    try:
        results = fetch_factchecks_from_google(
            query="vaccine",
            language_code="en",
            max_claims=5
        )
        
        print(f"Retrieved {len(results)} fact checks")
        for item in results:
            print(f"\nClaim: {item['claim'][:100]}...")
            print(f"Verdict: {item['verdict']}")
            print(f"Source: {item['source']}")
            print(f"Tags: {item['tags']}")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_multiple_queries():
    """Test fetching fact checks for multiple queries."""
    print("\n=== Test: Multiple Queries ===")
    
    queries = ["election", "climate", "health"]
    
    try:
        results = ingest_multiple_queries_from_google(
            queries=queries,
            language_code="en",
            max_claims_per_query=3
        )
        
        print("Ingestion results:")
        for query, count in results.items():
            print(f"  {query}: {count} fact checks")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_normalization():
    """Test the normalization function with sample data."""
    print("\n=== Test: Normalization ===")
    
    sample_claim_reviews = [
        {
            "claimText": "Vaccines cause autism",
            "claimDate": "2024-01-15",
            "languageCode": "en",
            "claimReview": {
                "url": "https://example.com/claim-review/1",
                "title": "False claim about vaccines and autism",
                "publisher": {
                    "name": "Fact Check Organization",
                    "site": "https://example.com"
                },
                "reviewRating": {
                    "ratingValue": 1,
                    "bestRating": 5,
                    "worstRating": 1,
                    "name": "False"
                },
                "textualRating": "This claim is false. Extensive research has shown no link between vaccines and autism."
            }
        }
    ]
    
    normalized = normalize_google_response(sample_claim_reviews)
    
    print(f"Normalized {len(normalized)} items:")
    for item in normalized:
        print(f"  ID: {item['id']}")
        print(f"  Claim: {item['claim']}")
        print(f"  Verdict: {item['verdict']}")
        print(f"  Tags: {item['tags']}")
    
    return len(normalized) > 0


def main():
    """Run all tests."""
    print("Google Fact Check Tools API Integration Test")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: GOOGLE_FACTCHECK_API_KEY environment variable not set")
        print("To use the live API test, set it first:")
        print("  $env:GOOGLE_FACTCHECK_API_KEY = 'your-api-key'")
        print("\nSkipping live API tests. Running normalization test only...\n")
        
        # Test normalization with sample data
        if test_normalization():
            print("\n✓ Normalization test passed")
        else:
            print("\n✗ Normalization test failed")
    else:
        print(f"\n✓ API key found: {api_key[:10]}...\n")
        
        # Run all tests
        tests = [
            ("Single Query", test_single_query),
            ("Multiple Queries", test_multiple_queries),
            ("Normalization", test_normalization),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                success = test_func()
                results.append((name, success))
            except Exception as e:
                print(f"\n✗ {name} test error: {e}")
                results.append((name, False))
        
        print("\n" + "=" * 50)
        print("Test Results:")
        for name, success in results:
            status = "✓ PASSED" if success else "✗ FAILED"
            print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
