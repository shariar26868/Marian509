import pytest
import json
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

# Fixture for sample room data
@pytest.fixture
def sample_room():
    return {"length": 15, "width": 12, "height": 9}

# Fixture for furniture selection
@pytest.fixture
def sample_furniture():
    return [
        {"type": "Sofa", "subtype": "3-Seater Sofa", "width": 84, "depth": 36, "height": 34},
        {"type": "Coffee Table", "subtype": "Rectangular", "width": 48, "depth": 24, "height": 18}
    ]

# ===================================================================
# 1. Test Room Dimension Endpoint
# ===================================================================
def test_set_room_dimensions(sample_room):
    response = client.post("/room/dimensions", json=sample_room)
    assert response.status_code == 200
    data = response.json()
    assert data["square_feet"] == 15 * 12  # 180
    assert "message" in data


def test_set_room_dimensions_invalid_input():
    response = client.post("/room/dimensions", json={"length": -10, "width": 12})
    assert response.status_code == 422  # Pydantic validation error


# ===================================================================
# 2. Test Furniture Fit Check
# ===================================================================
def test_furniture_fit_check_success(sample_room, sample_furniture):
    # First set room
    client.post("/room/dimensions", json=sample_room)

    payload = {
        "room": sample_room,
        "furnitures": sample_furniture
    }
    response = client.post("/room/fit-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fits"] is True
    assert "fits in the room" in data["message"]


def test_furniture_fit_check_failure(sample_room):
    large_furniture = [
        {"type": "Sofa", "subtype": "Sectional Sofa (U-Shape)", "width": 130, "depth": 95, "height": 34},
        {"type": "TV Stand", "subtype": "Large (up to 75\" TV)", "width": 66, "depth": 18, "height": 24}
    ]
    payload = {
        "room": sample_room,
        "furnitures": large_furniture
    }
    response = client.post("/room/fit-check", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Please deselect one item because the dimension is bigger."


# ===================================================================
# 3. Test Furniture Search (Mock Web Scraping)
# ===================================================================
@patch("ai_backend.services.furniture.requests.get")
def test_search_furniture(mock_get):
    # Mock HTML response
    mock_html = """
    <div class="product-item">
        <h3>Minimal Sofa</h3>
        <a href="/products/sofa-123"></a>
        <span class="price">$799.00</span>
        <img src="https://example.com/sofa.jpg">
    </div>
    """
    mock_response = MagicMock()
    mock_response.text = mock_html
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    payload = {
        "theme": "MINIMAL SCANDINAVIAN",
        "room_type": "Living Room Furniture",
        "furniture_types": ["Sofa"],
        "price_range": {"min": 500, "max": 1000}
    }

    response = client.post("/furniture/search", json=payload)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    item = results[0]
    assert item["name"] == "Minimal Sofa"
    assert item["price"] == 799.0
    assert "sofa-123" in item["link"]


# ===================================================================
# 4. Test Image Generation Endpoint (Mock Replicate & S3)
# ===================================================================
def test_generate_image_success(tmp_path):
    # Create dummy image file
    dummy_image_path = tmp_path / "room.jpg"
    dummy_image_path.write_bytes(b"fake image data")

    with open(dummy_image_path, "rb") as f:
        files = {"room_image": ("room.jpg", f, "image/jpeg")}
        data = {
            "prompt": "Place sofa on left wall, table in center",
            "theme": "MINIMAL SCANDINAVIAN",
            "furniture_links": "https://example.com/sofa,https://example.com/table"
        }

        # Mock Replicate
        with patch("ai_backend.services.ai_generator.replicate.run") as mock_replicate:
            mock_replicate.return_value = ["https://replicate.com/output.jpg"]

            # Mock S3 upload
            with patch("ai_backend.services.storage.upload_to_s3") as mock_s3:
                mock_s3.return_value = "https://s3.amazonaws.com/bucket/gen123.jpg"

                response = client.post("/generation/generate", data=data, files=files)

                assert response.status_code == 200
                result = response.json()
                assert result["generated_image_url"] == "https://s3.amazonaws.com/bucket/gen123.jpg"


def test_generate_image_missing_file():
    data = {
        "prompt": "test",
        "theme": "MINIMAL SCANDINAVIAN",
        "furniture_links": ""
    }
    response = client.post("/generation/generate", data=data)
    assert response.status_code == 422  # Missing room_image


# ===================================================================
# 5. Test Full Flow (Integration Style)
# ===================================================================
def test_full_flow_integration(sample_room, sample_furniture, tmp_path):
    # Step 1: Set room
    client.post("/room/dimensions", json=sample_room)

    # Step 2: Check fit
    fit_payload = {"room": sample_room, "furnitures": sample_furniture}
    fit_resp = client.post("/room/fit-check", json=fit_payload)
    assert fit_resp.status_code == 200

    # Step 3: Search furniture
    search_payload = {
        "theme": "MINIMAL SCANDINAVIAN",
        "room_type": "Living Room Furniture",
        "furniture_types": ["Sofa", "Coffee Table"],
        "price_range": {"min": 100, "max": 2000}
    }
    with patch("ai_backend.services.furniture.requests.get"):
        search_resp = client.post("/furniture/search", json=search_payload)
        assert search_resp.status_code == 200

    # Step 4: Generate image (mocked)
    dummy_img = tmp_path / "test.jpg"
    dummy_img.write_bytes(b"img")
    with open(dummy_img, "rb") as f:
        gen_data = {
            "prompt": "Sofa on left, table in center",
            "theme": "MINIMAL SCANDINAVIAN",
            "furniture_links": "https://example.com/1,https://example.com/2"
        }
        files = {"room_image": ("test.jpg", f, "image/jpeg")}
        with patch("ai_backend.services.ai_generator.replicate.run"), \
             patch("ai_backend.services.storage.upload_to_s3") as mock_s3:
            mock_s3.return_value = "https://s3.mock/gen.jpg"
            gen_resp = client.post("/generation/generate", data=gen_data, files=files)
            assert gen_resp.status_code == 200
            assert "generated_image_url" in gen_resp.json()


# ===================================================================
# 6. Test Edge Cases
# ===================================================================
def test_zero_dimension_room():
    response = client.post("/room/dimensions", json={"length": 0, "width": 10})
    assert response.status_code == 422


def test_theme_not_found():
    payload = {
        "theme": "INVALID_THEME",
        "room_type": "Living Room Furniture",
        "furniture_types": ["Sofa"],
        "price_range": {"min": 100, "max": 1000}
    }
    response = client.post("/furniture/search", json=payload)
    assert response.status_code == 200
    assert response.json()["results"] == []  # Empty list if no sites


# ===================================================================
# 7. Test JSON Data Loading (furniture_data.json)
# ===================================================================
def test_furniture_data_json_exists():
    data_path = "ai_backend/data/furniture_data.json"
    assert os.path.exists(data_path), f"{data_path} not found!"
    with open(data_path, "r") as f:
        data = json.load(f)
    assert "Living Room Furniture" in data
    assert "Sofa" in data["Living Room Furniture"]
    assert "3-Seater Sofa" in data["Living Room Furniture"]["Sofa"]


# ===================================================================
# 8. Run with: pytest -v
# ===================================================================
if __name__ == "__main__":
    pytest.main(["-v", __file__])