# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# In-memory store for tracking redeemed discount codes
redeemed_codes = set()

# In-memory store for user loyalty points and processed transactions
user_loyalty_points: dict[str, int] = {}
processed_transactions: set[str] = set()

# In-memory store for tracking carts and processed orders
mock_carts: dict[str, dict] = {
    "cart_123": {"user_id": "user_123", "total": 100.0},
    "cart_456": {"user_id": "user_456", "total": 200.0}
}
processed_orders: set[str] = set()

# Admin RBAC state and dynamic discount store
admin_roles = {"admin_999"}
active_discount_codes: dict[str, dict] = {
    "WELCOME50": {"type": "flat", "value": 50.0},
    "SUMMER20": {"type": "percent", "value": 0.20}
}


class AwardPointsSchema(BaseModel):
    user_id: str = Field(..., min_length=1, description="The registered user ID.")
    points: int = Field(..., gt=0, description="The number of points to award (must be strictly positive).")
    transaction_id: str = Field(..., min_length=1, description="Unique transaction ID to prevent replay attacks.")

def award_loyalty_points(request: AwardPointsSchema) -> str:
    """Awards loyalty points to a user after a successful purchase."""
    if request.transaction_id in processed_transactions:
        return f"Error: Transaction {request.transaction_id} has already been processed."

    current_points = user_loyalty_points.get(request.user_id, 0)
    user_loyalty_points[request.user_id] = current_points + request.points
    processed_transactions.add(request.transaction_id)

    return f"Success: Awarded {request.points} points to user {request.user_id}. New balance: {user_loyalty_points[request.user_id]}."


class UpdateDiscountSchema(BaseModel):
    user_id: str = Field(..., min_length=1, description="The user making the request.")
    code: str = Field(..., min_length=1, description="The discount code to modify.")
    is_active: bool = Field(..., description="True to activate, False to deactivate.")
    discount_type: Literal["flat", "percent"] | None = Field(default=None, description="Type of discount. Required if activating a new code.")
    discount_value: float | None = Field(default=None, description="Value of the discount. Required if activating a new code.")

def update_discount_status(request: UpdateDiscountSchema) -> str:
    """Allows administrators to activate or deactivate discount codes."""
    if request.user_id not in admin_roles:
        return f"Error: User {request.user_id} is not an authorized administrator."

    code_upper = request.code.upper()

    if request.is_active:
        if code_upper not in active_discount_codes:
            if request.discount_type is None or request.discount_value is None:
                return "Error: discount_type and discount_value are required when activating a new code."
            active_discount_codes[code_upper] = {
                "type": request.discount_type,
                "value": request.discount_value
            }
        return f"Success: Discount code {code_upper} is now active."
    else:
        if code_upper in active_discount_codes:
            del active_discount_codes[code_upper]
        return f"Success: Discount code {code_upper} is now deactivated."

class ProcessCheckoutSchema(BaseModel):
    user_id: str = Field(..., min_length=1, description="The registered user ID.")
    cart_id: str = Field(..., min_length=1, description="The ID of the cart to checkout.")
    discount_code: str | None = Field(default=None, description="Optional discount code to apply.")

def process_cart_checkout(request: ProcessCheckoutSchema) -> str:
    """Processes a cart checkout, optionally applying a discount code."""
    if request.cart_id not in mock_carts:
        return f"Error: Cart {request.cart_id} not found."

    cart = mock_carts[request.cart_id]

    # IDOR Protection: User must own the cart
    if cart["user_id"] != request.user_id:
        return f"Error: You are not authorized to checkout cart {request.cart_id}."

    # Replay Attack Prevention: Cart can only be checked out once
    if request.cart_id in processed_orders:
        return f"Error: Cart {request.cart_id} has already been checked out."

    total = cart["total"]

    if request.discount_code:
        # Check discount validity by actually attempting to redeem it
        redeem_result = redeem_discount_code(request.discount_code, request.user_id)
        if "Error:" in redeem_result:
            return f"Warning: Discount code is invalid or already used. Full price is ${total:.2f}. Please ask the user if they want to proceed without a discount."

        # Apply discount amount
        code_upper = request.discount_code.upper()
        if code_upper in active_discount_codes:
            discount_info = active_discount_codes[code_upper]
            if discount_info["type"] == "flat":
                total = max(0.0, total - discount_info["value"])
            elif discount_info["type"] == "percent":
                total = max(0.0, total * (1.0 - discount_info["value"]))

    # Finalize checkout
    processed_orders.add(request.cart_id)

    # Award loyalty points automatically (Standard Practice)
    points_to_award = max(1, int(total)) # 1 point per dollar, min 1 point if free
    award_req = AwardPointsSchema(
        user_id=request.user_id,
        points=points_to_award,
        transaction_id=f"checkout_{request.cart_id}"
    )
    award_loyalty_points(award_req)

    return f"Success: Order processed for cart {request.cart_id}. Final total: ${total:.2f}. Awarded {points_to_award} loyalty points."

def redeem_discount_code(code: str, user_id: str) -> str:
    """Redeems a single-use discount code for a registered user.

    Args:
        code: The discount code to redeem (e.g., WELCOME50, SUMMER20).
        user_id: The registered user ID attempting to redeem the code.

    Returns:
        A string indicating the result of the redemption attempt.
    """
    if not user_id:
        return "Error: A registered user ID is required."

    code_upper = code.upper()
    if code_upper not in active_discount_codes:
        return f"Error: {code} is not a recognized discount code."

    # Check if this specific code has already been redeemed
    if code_upper in redeemed_codes:
        return (
            f"Error: Discount code {code} has already been redeemed and is single-use."
        )

    redeemed_codes.add(code_upper)
    return f"Success: Discount code {code} has been redeemed for user {user_id}."


root_agent = Agent(
    name="shopping_assistant",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are an AI shopping assistant for a retail store. You help users with their shopping needs and can redeem single-use discount codes for registered users.",
    tools=[redeem_discount_code, award_loyalty_points, process_cart_checkout, update_discount_status],
)

app = App(
    root_agent=root_agent,
    name="app",
)
