import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def stub_architecture_dependencies():
    """
    Stub external dependencies (DB, LLM, Kroki) so tests are deterministic and fast.
    """
    # Mock for get_invention_details
    with patch("app.api.routes.get_invention_details") as mock_db, \
         patch("app.api.routes.generate_architecture_diagram") as mock_llm, \
         patch("app.api.routes.validate_mermaid_code") as mock_val, \
         patch("app.api.routes.get_kroki_url") as mock_kroki:
        
        mock_db.return_value = {
            "invention_id": "inv-001",
            "title": "Test Invention",
            "description": "A deterministic invention description for testing.",
            "owner": "test-owner",
        }
        
        mock_llm.return_value = "graph TD;\nA[Test Client] --> B[Architecture API];\nB --> C[Deterministic Service];"
        mock_val.return_value = True
        mock_kroki.return_value = "https://kroki.example.com/diagram/test-diagram-id"
        
        yield {
            "db": mock_db,
            "llm": mock_llm,
            "val": mock_val,
            "kroki": mock_kroki
        }

def test_architecture_success(stub_architecture_dependencies):
    """Test 1: Valid Request"""
    payload = {
        "user_requirement": "Please design a high-level architecture.",
        "invention_id": "inv-001"
    }
    response = client.post("/api/v1/architecture", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mermaid_code"] is not None
    assert "graph TD" in data["mermaid_code"]
    assert data["svg_url"] == "https://kroki.example.com/diagram/test-diagram-id"
    assert data["message"] == "Architecture diagram generated successfully."

def test_architecture_invalid_intent():
    """Test 2: Invalid Intent Request ('hi')"""
    payload = {
        "user_requirement": "hi",
        "invention_id": "inv-002"
    }
    
    # Mock the LLM to return INVALID_INTENT
    with patch("app.api.routes.get_invention_details") as mock_db, \
         patch("app.api.routes.generate_architecture_diagram") as mock_llm:
        
        mock_db.return_value = {"title": "Test"}
        mock_llm.return_value = "INVALID_INTENT"
        
        response = client.post("/api/v1/architecture", json=payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid request intent."

def test_architecture_validation_error():
    """Test 3: Mermaid Generation Error (triggers failure path)"""
    payload = {
        "user_requirement": "generate error",
        "invention_id": "inv-001"
    }
    
    # Force the mermaid validation to fail
    with patch("app.api.routes.get_invention_details") as mock_db, \
         patch("app.api.routes.generate_architecture_diagram") as mock_llm, \
         patch("app.api.routes.validate_mermaid_code") as mock_val:
        
        mock_db.return_value = {"title": "Test"}
        mock_llm.return_value = "graph TD; Invalid Mermaid"
        mock_val.return_value = False
        
        response = client.post("/api/v1/architecture", json=payload)
    
    assert response.status_code == 200 # Current implementation returns 200 with status: error
    data = response.json()
    assert data["status"] == "error"
    assert data["mermaid_code"] is None
    assert data["message"] == "Generation failed or syntax is invalid."

if __name__ == "__main__":
    # If run directly, use pytest to run this file
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
