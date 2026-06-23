import pytest
from app.agent import (
    redeem_discount_code,
    redeemed_codes,
    award_loyalty_points,
    AwardPointsSchema,
    user_loyalty_points,
    processed_transactions,
    process_cart_checkout,
    ProcessCheckoutSchema,
    mock_carts,
    processed_orders
)

@pytest.fixture(autouse=True)
def reset_state():
    """Reset the global in-memory state before each test to ensure isolation."""
    redeemed_codes.clear()
    user_loyalty_points.clear()
    processed_transactions.clear()
    processed_orders.clear()
    mock_carts.clear()
    mock_carts["cart_123"] = {"user_id": "user_123", "total": 100.0}
    mock_carts["cart_456"] = {"user_id": "user_456", "total": 200.0}

def test_security_boundary_missing_user_id():
    """Test that redemption fails if an empty or missing user_id is provided."""
    result = redeem_discount_code("WELCOME50", "")
    assert "Error: A registered user ID is required" in result
    assert "WELCOME50" not in redeemed_codes

def test_security_boundary_invalid_code():
    """Test that unauthorized/fake discount codes are rejected."""
    result = redeem_discount_code("HACKER99", "user_123")
    assert "Error: HACKER99 is not a recognized discount code" in result
    assert "HACKER99" not in redeemed_codes

def test_business_logic_successful_redemption():
    """Test the happy path for a valid user and valid code."""
    result = redeem_discount_code("WELCOME50", "user_123")
    assert "Success: Discount code WELCOME50 has been redeemed for user user_123" in result
    assert "WELCOME50" in redeemed_codes

def test_security_boundary_replay_attack_single_use():
    """Test that a code cannot be redeemed more than once (preventing replay attacks)."""
    # 1. First redemption should succeed
    result_initial = redeem_discount_code("SUMMER20", "user_123")
    assert "Success" in result_initial
    assert "SUMMER20" in redeemed_codes

    # 2. Second redemption attempt (even by a different user) should be blocked
    result_replay = redeem_discount_code("SUMMER20", "user_456")
    assert "Error: Discount code SUMMER20 has already been redeemed and is single-use" in result_replay

def test_business_logic_case_insensitivity():
    """Test that the validation handles lowercase codes robustly."""
    result = redeem_discount_code("summer20", "user_789")
    assert "Success" in result
    assert "SUMMER20" in redeemed_codes

def test_award_loyalty_points_success():
    req = AwardPointsSchema(user_id="user_123", points=100, transaction_id="tx_1")
    res = award_loyalty_points(req)
    assert "Success" in res
    assert user_loyalty_points["user_123"] == 100

def test_award_loyalty_points_replay_attack():
    req1 = AwardPointsSchema(user_id="user_123", points=100, transaction_id="tx_1")
    res1 = award_loyalty_points(req1)
    assert "Success" in res1

    req2 = AwardPointsSchema(user_id="user_123", points=100, transaction_id="tx_1")
    res2 = award_loyalty_points(req2)
    assert "Error: Transaction tx_1 has already been processed" in res2
    assert user_loyalty_points["user_123"] == 100

def test_award_loyalty_points_negative_points_validation():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AwardPointsSchema(user_id="user_123", points=-50, transaction_id="tx_2")

def test_award_loyalty_points_zero_points_validation():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AwardPointsSchema(user_id="user_123", points=0, transaction_id="tx_3")

def test_checkout_idor_protection():
    req = ProcessCheckoutSchema(user_id="hacker_99", cart_id="cart_123")
    res = process_cart_checkout(req)
    assert "Error: You are not authorized to checkout cart cart_123" in res
    assert "cart_123" not in processed_orders

def test_checkout_success_no_discount():
    req = ProcessCheckoutSchema(user_id="user_123", cart_id="cart_123")
    res = process_cart_checkout(req)
    assert "Success" in res
    assert "Final total: $100.00" in res
    assert "Awarded 100 loyalty points" in res
    assert user_loyalty_points["user_123"] == 100
    assert "cart_123" in processed_orders

def test_checkout_success_with_discount():
    req = ProcessCheckoutSchema(user_id="user_456", cart_id="cart_456", discount_code="WELCOME50")
    res = process_cart_checkout(req)
    assert "Success" in res
    assert "Final total: $150.00" in res # 200 - 50
    assert "Awarded 150 loyalty points" in res
    assert user_loyalty_points["user_456"] == 150
    assert "cart_456" in processed_orders

def test_checkout_replay_attack():
    req = ProcessCheckoutSchema(user_id="user_123", cart_id="cart_123")
    process_cart_checkout(req)

    # Try again
    res = process_cart_checkout(req)
    assert "Error: Cart cart_123 has already been checked out" in res

def test_checkout_discount_invalid():
    # Make a fresh cart for testing
    mock_carts["cart_999"] = {"user_id": "user_999", "total": 50.0}
    req = ProcessCheckoutSchema(user_id="user_999", cart_id="cart_999", discount_code="INVALID")
    res = process_cart_checkout(req)
    assert "Warning: Discount code is invalid or already used" in res
    assert "cart_999" not in processed_orders # Still not processed
