import pytest
from app.agent import redeem_discount_code, redeemed_codes

@pytest.fixture(autouse=True)
def reset_redeemed_codes():
    """Reset the global in-memory state before each test to ensure isolation."""
    redeemed_codes.clear()

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
