"""
Test script for RAMA Backend API endpoints.
Validates all SRS requirements.
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "dev_admin_token_change_in_production"  # Change to your token


def print_response(name: str, response: requests.Response):
    """Pretty print API response."""
    print("\n" + "=" * 60)
    print(f"TEST: {name}")
    print("=" * 60)
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print("=" * 60)


def test_health():
    """Test GET /health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "mode" in data
    assert "models" in data
    return data


def test_verify_simple():
    """Test POST /verify with simple claim."""
    payload = {
        "text": "The Earth is round",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/verify", json=payload)
    print_response("Verify Simple Claim", response)
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "verdict" in data
    assert "confidence" in data
    assert "sources_used" in data
    return data


def test_verify_with_category():
    """Test POST /verify with category."""
    payload = {
        "text": "Vaccines cause autism",
        "language": "en",
        "category": "health"
    }
    response = requests.post(f"{BASE_URL}/verify", json=payload)
    print_response("Verify Health Claim", response)
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    return data


def test_verify_invalid():
    """Test POST /verify with invalid input."""
    payload = {
        "text": "short"  # Too short, minimum 10 chars
    }
    response = requests.post(f"{BASE_URL}/verify", json=payload)
    print_response("Verify Invalid (Too Short)", response)
    assert response.status_code == 422  # Validation error
    return response.json()


def test_ingest_without_token():
    """Test POST /admin/ingest without admin token."""
    response = requests.post(f"{BASE_URL}/admin/ingest")
    print_response("Ingest Without Token", response)
    assert response.status_code == 401  # Unauthorized
    return response.json()


def test_ingest_with_token():
    """Test POST /admin/ingest with admin token."""
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    payload = {"force": False}
    response = requests.post(f"{BASE_URL}/admin/ingest", json=payload, headers=headers)
    print_response("Ingest With Token", response)
    # May return 200 or 500 depending on MCP server availability
    data = response.json()
    if response.status_code == 200:
        assert "status" in data
        assert "ingested" in data
    return data


def test_feedback():
    """Test POST /feedback endpoint."""
    payload = {
        "claim_text": "Test claim for feedback",
        "verdict_returned": "false",
        "comment": "This verdict seems incorrect because XYZ"
    }
    response = requests.post(f"{BASE_URL}/feedback", json=payload)
    print_response("Submit Feedback", response)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    return data


def test_admin_logs():
    """Test GET /admin/logs endpoint."""
    headers = {"X-Admin-Token": ADMIN_TOKEN}
    response = requests.get(f"{BASE_URL}/admin/logs?limit=5", headers=headers)
    print_response("Admin Logs", response)
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    return data


def test_root():
    """Test GET / root endpoint."""
    response = requests.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response)
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "endpoints" in data
    return data


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "🚀" * 30)
    print("RAMA BACKEND API TEST SUITE")
    print("🚀" * 30)
    
    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Verify Simple Claim", test_verify_simple),
        ("Verify with Category", test_verify_with_category),
        ("Verify Invalid Input", test_verify_invalid),
        ("Feedback Submission", test_feedback),
        ("Ingest Without Token", test_ingest_without_token),
        ("Ingest With Token", test_ingest_with_token),
        ("Admin Logs", test_admin_logs)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            print(f"\n▶️  Running: {name}")
            test_func()
            results.append((name, "✅ PASS"))
            print(f"✅ {name} PASSED")
        except AssertionError as e:
            results.append((name, f"❌ FAIL: {e}"))
            print(f"❌ {name} FAILED: {e}")
        except Exception as e:
            results.append((name, f"⚠️ ERROR: {e}"))
            print(f"⚠️ {name} ERROR: {e}")
        
        # Small delay between tests
        time.sleep(0.5)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if "PASS" in result)
    failed = sum(1 for _, result in results if "FAIL" in result)
    errors = sum(1 for _, result in results if "ERROR" in result)
    
    for name, result in results:
        print(f"{result.split(':')[0]:4} {name}")
    
    print("\n" + "-" * 60)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print("=" * 60)
    
    return passed == len(tests)


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        exit(1)
