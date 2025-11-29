"""
Test script for embeddings helper
"""

from app.embeddings import get_embedding, batch_get_embeddings, get_embedding_info, EmbeddingException

print("=" * 70)
print("Embeddings Helper - Test Script")
print("=" * 70)

# Get configuration info
info = get_embedding_info()
print(f"\n[CONFIG]")
print(f"  Backend: {info['backend']}")
print(f"  Model: {info['model']}")
print(f"  Endpoint: {info['endpoint']}")
print(f"  Dimensions: {info['dimensions']}")

# Test 1: Single embedding
print(f"\n[TEST 1] Single Embedding")
print("-" * 70)

test_text = "The quick brown fox jumps over the lazy dog"
try:
    embedding = get_embedding(test_text)
    print(f"✓ Text: '{test_text}'")
    print(f"✓ Embedding length: {len(embedding)} dimensions")
    print(f"✓ First 5 values: {embedding[:5]}")
    print(f"✓ Last 5 values: {embedding[-5:]}")
except EmbeddingException as e:
    print(f"✗ Error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

# Test 2: Text normalization
print(f"\n[TEST 2] Text Normalization")
print("-" * 70)

texts_with_newlines = [
    "Line 1\nLine 2\nLine 3",
    "  Leading and trailing spaces  ",
    "Mixed\r\nWindows\nUnix\rMac\nNewlines"
]

for text in texts_with_newlines:
    try:
        embedding = get_embedding(text)
        print(f"✓ Text (with special chars): embedded ({len(embedding)} dims)")
    except EmbeddingException as e:
        print(f"✗ Error: {e}")

# Test 3: Batch embedding
print(f"\n[TEST 3] Batch Embeddings")
print("-" * 70)

batch_texts = [
    "First document about machine learning",
    "Second document about artificial intelligence",
    "Third document about deep learning",
]

try:
    batch_embeddings = batch_get_embeddings(batch_texts)
    print(f"✓ Batch size: {len(batch_texts)} texts")
    print(f"✓ Embeddings generated: {len(batch_embeddings)}")
    print(f"✓ Embedding dimensions: {[len(e) for e in batch_embeddings]}")
    for i, (text, embedding) in enumerate(zip(batch_texts, batch_embeddings)):
        print(f"  [{i+1}] {text[:40]}... -> {len(embedding)} dims")
except EmbeddingException as e:
    print(f"✗ Error: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

# Test 4: Empty text handling
print(f"\n[TEST 4] Error Handling - Empty Text")
print("-" * 70)

try:
    embedding = get_embedding("")
    print(f"✗ Should have raised an exception for empty text")
except EmbeddingException as e:
    print(f"✓ Correctly rejected empty text: {e}")
except Exception as e:
    print(f"✗ Wrong exception type: {e}")

print("\n" + "=" * 70)
print("Embeddings Test Complete!")
print("=" * 70)
