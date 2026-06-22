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

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# In-memory store for tracking redeemed discount codes
redeemed_codes = set()

def redeem_discount_code(code: str, user_id: str) -> str:
    """Redeems a single-use discount code for a registered user.
    
    Args:
        code: The discount code to redeem (e.g., WELCOME50, SUMMER20).
        user_id: The registered user ID attempting to redeem the code.
        
    Returns:
        A string indicating the result of the redemption attempt.
    """
    valid_codes = {"WELCOME50", "SUMMER20"}
    
    if not user_id:
        return "Error: A registered user ID is required."
        
    code_upper = code.upper()
    if code_upper not in valid_codes:
        return f"Error: {code} is not a recognized discount code."
        
    # Check if this specific code has already been redeemed
    if code_upper in redeemed_codes:
        return f"Error: Discount code {code} has already been redeemed and is single-use."
        
    redeemed_codes.add(code_upper)
    return f"Success: Discount code {code} has been redeemed for user {user_id}."


root_agent = Agent(
    name="shopping_assistant",
    model=Gemini(
        model="gemini-flash-latest",
        api_key="AIzaSyD-mock-key-value-12345",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are an AI shopping assistant for a retail store. You help users with their shopping needs and can redeem single-use discount codes for registered users.",
    tools=[redeem_discount_code],
)

app = App(
    root_agent=root_agent,
    name="app",
)
