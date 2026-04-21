from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_raw_endpoint():
    print("--- Testing Raw Mermaid Endpoint ---")
    
    invention_id = "inv-001"
    url = f"/api/v1/architecture/{invention_id}/raw"
    
    response = client.get(url)
    
    print(f"Status Code: {response.status_code}")
    print("Raw Content Output:")
    print("-" * 20)
    print(response.text)
    print("-" * 20)
    
    if "\n" in response.text and "graph TD" in response.text:
        print("SUCCESS: Raw content contains real newlines and valid Mermaid header.")
    else:
        print("FAILURE: Content structure is not as expected.")

if __name__ == "__main__":
    test_raw_endpoint()
