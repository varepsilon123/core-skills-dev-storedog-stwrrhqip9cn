"""
Unit tests for the discounts Flask API endpoints.

Setup Strategy:
1. Set environment variables (POSTGRES_*) before imports to prevent KeyError during module load
2. Mock the database (bootstrap.db) to prevent actual database connections and initialization
3. Use Flask's test_client() to simulate HTTP requests without running a server
4. Mock Discount.query chains to return controlled test data instead of hitting the database
"""

import pytest
from unittest.mock import patch, MagicMock, Mock


@pytest.mark.unit
def test_get_discounts_success(client):
    """Test GET /discount returns list of discounts successfully"""
    with patch("discounts.Discount") as mock_discount_class:
        # Create mock discount objects
        mock_discount_1 = MagicMock()
        mock_discount_1.serialize.return_value = {
            "id": 1,
            "name": "Summer Sale",
            "code": "SUMMER20",
            "value": 20,
            "discount_type": {
                "id": 1,
                "name": "Percentage",
                "discount_query": "price * 0.8",
            },
        }

        mock_discount_2 = MagicMock()
        mock_discount_2.serialize.return_value = {
            "id": 2,
            "name": "Winter Sale",
            "code": "WINTER10",
            "value": 10,
            "discount_type": {"id": 2, "name": "Fixed", "discount_query": "price - 10"},
        }

        # Mock the query chain: Discount.query.all()
        mock_discount_class.query.all.return_value = [mock_discount_1, mock_discount_2]

        # Make request
        response = client.get("/discount")

        # Assertions
        assert response.status_code == 200
        assert response.content_type == "application/json"

        json_data = response.get_json()
        assert len(json_data) == 2
        assert json_data[0]["name"] == "Summer Sale"
        assert json_data[0]["code"] == "SUMMER20"
        assert json_data[0]["value"] == 20
        assert json_data[1]["name"] == "Winter Sale"

        mock_discount_class.query.all.assert_called_once()


@pytest.mark.unit
def test_post_discount_success(client):
    """
    Test POST /discount creates a new discount and returns updated list.
    """
    with patch("discounts.random.randint") as mock_randint, \
         patch("discounts.words.get_random") as mock_get_random, \
         patch("discounts.db") as mock_db, \
         patch("discounts.DiscountType") as mock_discount_type_class, \
         patch("discounts.Discount") as mock_discount_class:

        # Mock random behavior for predictable test data
        mock_randint.side_effect = [3, 133]  # word_count=3, discount_value=133
        mock_get_random.return_value = "PREMIUM"

        # Existing discounts returned by first query
        existing_1 = MagicMock()
        existing_1.serialize.return_value = {
            "id": 1,
            "name": "Summer Sale",
            "code": "SUMMER20",
            "value": 100,
            "discount_type": {
                "id": 1,
                "name": "Percentage",
                "discount_query": "price * 0.8",
            },
        }

        existing_2 = MagicMock()
        existing_2.serialize.return_value = {
            "id": 2,
            "name": "Winter Sale",
            "code": "WINTER10",
            "value": 150,
            "discount_type": {"id": 2, "name": "Fixed", "discount_query": "price - 10"},
        }

        # The new discount that will appear in second query
        new_discount_obj = MagicMock()
        new_discount_obj.serialize.return_value = {
            "id": 3,
            "name": "Discount 3",
            "code": "PREMIUM",
            "value": 133,
        }

        # Mock Discount.query.all() called twice in POST endpoint
        mock_discount_class.query.all.side_effect = [
            [existing_1, existing_2],  # First call: count existing
            [existing_1, existing_2, new_discount_obj],  # Second call: return all
        ]

        # Mock DiscountType constructor
        mock_discount_type_instance = MagicMock()
        mock_discount_type_class.return_value = mock_discount_type_instance

        # Mock Discount constructor
        mock_discount_instance = MagicMock()
        mock_discount_class.return_value = mock_discount_instance

        # Mock db.session operations
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()

        response = client.post("/discount")

        # Basic response validation
        assert response.status_code == 200
        assert response.content_type == "application/json"

        # Validate response structure
        json_data = response.get_json()
        assert len(json_data) == 3
        assert json_data[0]["name"] == "Summer Sale"
        assert json_data[0]["code"] == "SUMMER20"
        assert json_data[0]["value"] == 100
        assert json_data[1]["name"] == "Winter Sale"
        assert json_data[2]["name"] == "Discount 3"
        assert json_data[2]["code"] == "PREMIUM"
        assert json_data[2]["value"] == 133

        # Verify constructor calls
        mock_discount_type_class.assert_called_once_with("Random Savings", "price * .9", None)

        # Verify Discount constructor received correct arguments
        call_args = mock_discount_class.call_args[0]
        assert call_args[0] == "Discount 3"  # name
        assert call_args[1] == "PREMIUM"  # code (from mocked words.get_random)
        assert call_args[2] == 133  # value (from mocked random.randint)

        # Verify database operations
        mock_db.session.add.assert_called_once_with(mock_discount_instance)
        mock_db.session.commit.assert_called_once()

        # Verify query was called twice (once to count, once to return all)
        assert mock_discount_class.query.all.call_count == 2


@pytest.mark.unit
def test_get_discount_code_success(client, mock_discount_factory):
    """Test GET /discount-code returns discount when code is found"""
    with patch("discounts.Discount") as mock_discount_class:
        # Mock a discount object with minimal data
        mock_discount = mock_discount_factory(id=1, name="Summer Sale", code="SUMMER20", value=20)

        # Mock the query chain: Discount.query.filter_by(code="SUMMER20").first()
        mock_discount_class.query.filter_by.return_value.first.return_value = mock_discount

        # Make request
        response = client.get("/discount-code?discount_code=SUMMER20")

        # Assertions
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["code"] == "SUMMER20"
        assert json_data["status"] == 1
        assert json_data["name"] == "Summer Sale"

        mock_discount_class.query.filter_by.assert_called_once_with(code="SUMMER20")


@pytest.mark.unit
def test_get_discount_code_not_found(client):
    """Test GET /discount-code returns 404 when code doesn't exist"""
    with patch("discounts.Discount") as mock_discount_class:
        # Mock query returning None
        mock_discount_class.query.filter_by.return_value.first.return_value = None

        response = client.get("/discount-code?discount_code=INVALID")

        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data["error"] == "Discount not found"
        assert json_data["status"] == 0


@pytest.mark.unit
def test_get_discount_code_with_broken_flag_enabled(client):
    """Test GET /discount-code randomly fails when BROKEN_DISCOUNTS=ENABLED"""
    # Directly patch the module-level variable instead of reloading the module
    with patch("discounts.BROKEN_DISCOUNTS", "ENABLED"), \
         patch("discounts.Discount") as mock_discount_class, \
         patch("discounts.random.choice") as mock_random:

        # Force the random error to trigger
        mock_random.return_value = True

        mock_discount = MagicMock()
        mock_discount_class.query.filter_by.return_value.first.return_value = mock_discount

        response = client.get("/discount-code?discount_code=TEST")

        assert response.status_code == 500
        json_data = response.get_json()
        assert "error" in json_data
        assert json_data["error"] == "Discount service error"
        assert "stack_trace" in json_data


@pytest.mark.unit
def test_get_discount_code_database_exception(client):
    """Test GET /discount-code handles database exceptions"""
    with patch("discounts.Discount") as mock_discount_class:
        # Mock database query to raise an exception
        mock_discount_class.query.filter_by.side_effect = Exception("Database connection error")

        response = client.get("/discount-code?discount_code=TEST")

        assert response.status_code == 500
        json_data = response.get_json()
        assert "error" in json_data
        assert json_data["message"] == "Internal Server Error"
        assert "stack_trace" in json_data


@pytest.mark.unit
def test_hello_endpoint(client):
    """Test GET / returns hello message"""
    response = client.get("/")

    assert response.status_code == 200
    assert response.content_type == "application/json"
