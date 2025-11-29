#!/usr/bin/env python3
"""
Quick verification that the API returns complete sources with evidence and URLs.
Run this after starting the backend server.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_verify_endpoint():
    """Test the verify endpoint and verify it returns complete sources."""
    
    print("\n" + "="*80)
    print("TESTING: /verify endpoint - Ensuring complete sources with evidence")
    print("="*80)
    
    test_claims = [
        {
            "text": "India has launched a new space mission to Mars",
            "category": "other"
        },
        {
            "text": "The government announced a new vaccination program",
            "category": "health"
        }
    ]
    
    for claim_req in test_claims:
        print(f"\n\nClaim: {claim_req['text']}")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{BASE_URL}/verify",
                json=claim_req,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ ERROR: Status {response.status_code}")
                print(response.text)
                continue
            
            data = response.json()
            
            # Check required fields
            required_fields = ["mode", "verdict", "confidence", "explanation", "sources_used", "timestamp"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print(f"✓ All required fields present")
            
            # Check verdict
            print(f"  Verdict: {data.get('verdict', 'N/A')}")
            print(f"  Confidence: {data.get('confidence', 'N/A')}")
            print(f"  Mode: {data.get('mode', 'N/A')}")
            print(f"  Explanation: {data.get('explanation', 'N/A')[:150]}...")
            
            # Check sources
            sources = data.get('sources_used', [])
            print(f"\n  Sources found: {len(sources)}")
            
            if not sources:
                print("  ⚠️  WARNING: No sources returned!")
            else:
                for idx, source in enumerate(sources[:3], 1):  # Show first 3
                    print(f"\n  Source {idx}:")
                    print(f"    - Type: {source.get('type', 'N/A')}")
                    print(f"    - Source: {source.get('source', 'N/A')}")
                    print(f"    - URL: {source.get('url', 'N/A')}")
                    print(f"    - Credibility: {source.get('credibility_level', 'N/A')}")
                    print(f"    - Snippet: {source.get('snippet', 'N/A')[:80]}...")
                    
                    # Validate
                    if not source.get('url'):
                        print(f"    ⚠️  WARNING: Missing URL!")
                    if not source.get('snippet'):
                        print(f"    ⚠️  WARNING: Missing snippet/evidence!")
            
            print(f"\n  Timestamp: {data.get('timestamp', 'N/A')}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed. Is the backend running on {BASE_URL}?")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_health_check():
    """Test health endpoint."""
    print("\n" + "="*80)
    print("TESTING: /health endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Mode: {data.get('mode', 'N/A')}")
        print(f"Models: {json.dumps(data.get('models', {}), indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                  R.A.M.A. API VERIFICATION TEST                           ║")
    print("║             Checking that /verify returns complete sources                ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    
    test_health_check()
    test_verify_endpoint()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nExpected behavior:")
    print("✓ All required fields present in response")
    print("✓ Sources returned with complete information (URL, snippet, credibility)")
    print("✓ Each source has concrete evidence (snippet)")
    print("✓ Verdict, explanation, and confidence score present")
    print("\n")
