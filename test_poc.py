import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_poc():
    print("--- Testing Architecture Generator API POC ---")
    
    # Test 1: Valid Request
    print("\n[Test 1] Valid Request")
    payload1 = {
        "user_requirement": "Please design a high-level architecture.",
        "invention_id": "inv-001"
    }
    response1 = client.post("/api/v1/architecture", json=payload1)
    print(f"Status Code: {response1.status_code}")
    print(f"Response: {response1.json()}")
    
    # Test 2: Invalid Intent
    print("\n[Test 2] Invalid Intent Request ('hi')")
    payload2 = {
        "user_requirement": "hi",
        "invention_id": "inv-002"
    }
    response2 = client.post("/api/v1/architecture", json=payload2)
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.json()}")
    
    # Test 3: Mermaid Generation Error (triggers retry and eventually fails)
    print("\n[Test 3] Simulate LLM Generating Invalid Code (using 'generate error' phrase)")
    payload3 = {
        "user_requirement": "generate error",
        "invention_id": "inv-001"
    }
    response3 = client.post("/api/v1/architecture", json=payload3)
    print(f"Status Code: {response3.status_code}")
    print(f"Response: {response3.json()}")

if __name__ == "__main__":
    test_poc()
