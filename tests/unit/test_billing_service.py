import pytest
from app.services.billing_service import estimate_cost

def test_estimate_cost():
    assert estimate_cost("gpt-4", 100) > 0