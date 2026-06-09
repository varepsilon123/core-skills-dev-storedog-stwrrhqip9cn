"""
Unit tests for the discounts Flask API endpoints.

Setup Strategy:
1. Set environment variables (POSTGRES_*) before imports to prevent KeyError during module load
2. Mock the database (bootstrap.db) to prevent actual database connections and initialization
3. Use Flask's test_client() to simulate HTTP requests without running a server
4. Mock Discount.query chains to return controlled test data instead of hitting the database

Note: test_post_discount_success contains intentional flakiness for educational purposes.
The test does NOT mock random.randint(10, 500), so the discount value varies on each run.
The flaky assertion (discount_value < 175) fails ~65% of the time (when value >= 175),
demonstrating Datadog's flaky test management features. This creates true flakiness where
the same commit can pass or fail on different runs.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock


@pytest.mark.unit
def test_get_discounts_success(client, mock_discount_factory):
    """Test GET /discount returns list of discounts successfully"""
    with patch("discounts.Discount") as mock_discount_class:
        # Create mock discount objects with minimal data
        mock_discount_1 = mock_discount_factory(id=1, name="Summer Sale", code="SUMMER20", value=20)
        mock_discount_2 = mock_discount_factory(id=2, name="Winter Sale", code="WINTER10", value=10)

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
def test_post_discount_success(client, mock_discount_factory):
    """
    Test POST /discount creates a new discount and returns updated list.

    FLAKY TEST (intentional): random.randint and words.get_random are NOT mocked,
    so the actual Discount constructor receives truly random values. The flaky
    assertion checks if the random discount value is < 175.
    """
    with patch("discounts.db") as mock_db, \
         patch("discounts.DiscountType") as mock_discount_type_class, \
         patch("discounts.Discount") as mock_discount_class:

        # Existing discounts returned by first query
        existing_1 = mock_discount_factory(id=1, name="Summer Sale", code="SUMMER20", value=100)
        existing_2 = mock_discount_factory(id=2, name="Winter Sale", code="WINTER10", value=150)

        # The new discount that will appear in second query
        # Note: code and value here are just placeholders for response validation;
        # the actual Discount constructor will receive truly random values
        new_discount_obj = mock_discount_factory(id=3, name="Discount 3", code="SOMEWORD", value=123)

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

        # Validate response structure (values come from mocked query.all() results)
        json_data = response.get_json()
        assert len(json_data) == 3
        assert json_data[0]["name"] == "Summer Sale"
        assert json_data[0]["code"] == "SUMMER20"
        assert json_data[0]["value"] == 100
        assert json_data[1]["name"] == "Winter Sale"
        assert json_data[2]["name"] == "Discount 3"
        assert json_data[2]["code"] == "SOMEWORD"
        assert json_data[2]["value"] == 123

        # FLAKY ASSERTION (intentional): depends on random.randint(10, 500)
        # The real random.randint is called in the code, and ~30% of values (354-500) will fail this assertion
        call_args = mock_discount_class.call_args[0]
        discount_value = call_args[2]  # third argument is the value from random.randint(10, 500)
        assert discount_value < 354

        # Verify constructor calls
        mock_discount_type_class.assert_called_once_with("Random Savings", "price * .9", None)

        # Verify Discount constructor was called with expected name pattern
        call_args = mock_discount_class.call_args[0]
        assert call_args[0] == "Discount 3"  # name (deterministic based on count)

        # Verify database operations
        mock_db.session.add.assert_called_once_with(mock_discount_instance)
        mock_db.session.commit.assert_called_once()

        # Verify query was called twice (once to count, once to return all)
        assert mock_discount_class.query.all.call_count == 2
