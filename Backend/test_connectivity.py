"""
Test script to diagnose Gemini connectivity and fallback to Ollama
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("R.A.M.A Model Gateway - Diagnostic Test")
print("=" * 70)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")

print(f"\n[CONFIG]")
print(f"  GEMINI_API_KEY: {'SET' if GEMINI_API_KEY else 'NOT SET'}")
print(f"  Gemini Model: {GEMINI_MODEL}")
print(f"  Ollama Endpoint: {OLLAMA_ENDPOINT}")

# Test 1: Check Gemini endpoint connectivity (basic DNS/HTTPS reachability)
print(f"\n[TEST 1] Testing Gemini endpoint connectivity...")
import requests
try:
    response = requests.head("https://generativelanguage.googleapis.com", timeout=5)
    print(f"  ✓ Gemini endpoint is reachable (HTTP {response.status_code})")
    GEMINI_AVAILABLE = True
except requests.exceptions.ConnectionError:
    print(f"  ✗ Cannot reach Gemini endpoint - DNS/Network issue")
    GEMINI_AVAILABLE = False
except Exception as e:
    print(f"  ✗ Gemini connectivity error: {e}")
    GEMINI_AVAILABLE = False

# Test 2: Check Ollama connectivity
print(f"\n[TEST 2] Testing Ollama connectivity...")
try:
    response = requests.head(OLLAMA_ENDPOINT.replace("/api/generate", ""), timeout=5)
    print(f"  ✓ Ollama is reachable (HTTP {response.status_code})")
    OLLAMA_AVAILABLE = True
except requests.exceptions.ConnectionError:
    print(f"  ✗ Cannot reach Ollama at {OLLAMA_ENDPOINT}")
    OLLAMA_AVAILABLE = False
except Exception as e:
    print(f"  ✗ Ollama connectivity error: {e}")
    OLLAMA_AVAILABLE = False

# Test 3: Recommendation
print(f"\n[RECOMMENDATION]")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    print(f"  → Use Gemini ({GEMINI_MODEL})")
elif OLLAMA_AVAILABLE:
    print(f"  → Gemini unavailable - Falling back to Ollama")
    print(f"  → Make sure Ollama is running: ollama serve")
else:
    print(f"  ✗ Neither Gemini nor Ollama is accessible!")
    print(f"  → Option 1: Enable internet and set GEMINI_API_KEY for Gemini")
    print(f"  → Option 2: Install & run Ollama locally")
    print(f"     Download: https://ollama.ai")
    print(f"     Run: ollama serve")

print("\n" + "=" * 70)
