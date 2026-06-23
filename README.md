# AI Shopping Assistant Agent

A secure-by-design AI shopping assistant agent built with Google ADK 2.0. This agent helps users with their retail shopping needs and securely manages the redemption of single-use discount codes.

## Project Structure

- `shopping-assistant/app/agent.py`: Core agent logic and orchestration, including the `redeem_discount_code`, `award_loyalty_points`, `process_cart_checkout`, and `update_discount_status` tools.
- `shopping-assistant/tests/test_agent.py`: Outcome-based security test suite validating business boundaries and preventing replay attacks.
- `shopping-assistant/threat_model.md`: A structured STRIDE threat modeling assessment of the agent's architecture.
- `shopping-assistant/.agents/CONTEXT.md`: Local secure coding standards and paved roads.
- `shopping-assistant/.agents/scripts/validate_tool_call.py`: PreToolUse hook script that prevents destructive terminal commands.
- `shopping-assistant/.semgrep/rules.yaml`: Custom Semgrep rules for detecting hardcoded secrets (e.g., Google API keys).
- `shopping-assistant/.pre-commit-config.yaml`: Pre-commit hook configuration for automated security gating and code formatting.

## Security First

This project enforces strict security guardrails during development:
1. **Tool Input Validation**: All tool parameters are strictly validated via Pydantic to prevent boundary exploits.
2. **Role-Based Access Control (RBAC)**: Administrative tools (e.g., `update_discount_status`) enforce strict authorization checks to prevent privilege escalation.
3. **Pre-Commit Remediation Loop**: Security scans (Semgrep) run locally on every commit. Violations automatically block the commit and mandate a refactoring loop.
4. **Agent Hooks**: Run commands are intercepted and validated by our script to prevent destructive actions (like `rm -rf /`).
5. **Threat Modeling**: The architecture is continuously evaluated using the STRIDE framework to ensure edge cases are handled securely.

## Development & Usage

Make sure you have `uv` installed to manage dependencies.

1. **Install dependencies**:
   ```bash
   cd shopping-assistant
   uv sync
   ```

2. **Run the Agent**:
   To start an interactive chat session with the Shopping Assistant:
   ```bash
   # Ensure your GOOGLE_API_KEY is set first
   $env:GOOGLE_API_KEY="your-api-key-here"  # Windows PowerShell
   export GOOGLE_API_KEY="your-api-key-here"  # Mac/Linux

   uv run agents-cli run
   ```

3. **Run tests**:
   ```bash
   uv run pytest tests/
   ```

4. **Install Pre-Commit hooks**:
   ```bash
   uv run pre-commit install -c .pre-commit-config.yaml
   ```
