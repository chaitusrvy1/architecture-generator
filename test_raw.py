import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_raw_endpoint_success():
    """Test the raw mermaid endpoint with assertions."""
    invention_id = "inv-001"
    url = f"/api/v1/architecture/{invention_id}/raw"
    
    mock_mermaid = "graph TD;\nA --> B;"
    
    # Mock the underlying create_architecture call (or the services it uses)
    # Patching at the route level for simplicity in this specific test
    with patch("app.api.routes.get_invention_details") as mock_db, \
         patch("app.api.routes.generate_architecture_diagram") as mock_llm, \
         patch("app.api.routes.validate_mermaid_code") as mock_val:
        
        mock_db.return_value = {"title": "Test"}
        mock_llm.return_value = mock_mermaid
        mock_val.return_value = True
        
        response = client.get(url)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "graph TD" in response.text
    assert "A --> B" in response.text

def test_raw_endpoint_failure():
    """Test the raw mermaid endpoint failure case."""
    invention_id = "inv-001"
    url = f"/api/v1/architecture/{invention_id}/raw"
    
    with patch("app.api.routes.get_invention_details") as mock_db, \
         patch("app.api.routes.generate_architecture_diagram") as mock_llm, \
         patch("app.api.routes.validate_mermaid_code") as mock_val:
        
        mock_db.return_value = {"title": "Test"}
        mock_llm.return_value = "invalid"
        mock_val.return_value = False
        
        response = client.get(url)
    
    assert response.status_code == 200
    assert response.text == "Error"

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
