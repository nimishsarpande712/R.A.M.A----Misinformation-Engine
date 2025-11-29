from app.model_gateway import generate_llm_response, get_model_info

print("=" * 60)
print("Model Gateway Test")
print("=" * 60)

# Check configuration
info = get_model_info()
print(f"\nBackend: {info['backend']}")
print(f"Model: {info['model']}")
print(f"Endpoint: {info['endpoint']}")

# Test response generation
try:
    print("\n" + "=" * 60)
    print("Testing: generate_llm_response()")
    print("=" * 60)
    
    response = generate_llm_response(
        prompt="Hello, how are you?",
        system="You are a test assistant."
    )
    print(f"\nResponse:\n{response}")
    print(f"\nResponse length: {len(response)} characters")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Test completed successfully!")
print("=" * 60)
