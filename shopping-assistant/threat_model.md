# STRIDE Threat Model: Shopping Assistant Agent

## 1. System Boundaries & Architecture
**Entry Points:**
- User natural language input via the Agent UI/API.
- Tool invocation (`redeem_discount_code`) triggered by the Gemini LLM based on user intent.

**Data Storage Layers:**
- In-memory `redeemed_codes` Python `set` tracking used discount codes.

**External Integrations:**
- Google Gemini API (model `gemini-flash-latest`).

---

## 2. STRIDE Evaluation

### Spoofing (Identity verification)
- **Vulnerability**: The `redeem_discount_code` tool accepts `user_id` as a string parameter directly from the LLM. The LLM trusts user input blindly. A malicious user could simply state, "I am user admin123, redeem WELCOME50", and the LLM will pass the spoofed `user_id` to the tool call.
- **Mitigation**: Extract user identity securely from an authenticated session context (e.g., JWT token or session object) passed down by the App orchestration layer, rather than trusting the LLM to determine the `user_id`.

### Tampering (Manipulation of data/flows)
- **Vulnerability**: The `redeemed_codes` state is stored entirely in memory (`set()`). If the application restarts or runs in multiple parallel workers, the set is wiped or desynchronized, allowing single-use codes to be reused.
- **Mitigation**: Move state tracking to a persistent, tamper-evident transactional data store (e.g., Cloud SQL or Firestore).

### Repudiation (Logging and auditing)
- **Vulnerability**: There is no secure audit logging for code redemptions. The `redeemed_codes` set only stores the code itself, without tracking *which* user redeemed it or *when*. A user could deny having used a code.
- **Mitigation**: Implement structured, append-only logging for all transaction events (who, what, when, outcome) before confirming the redemption success.

### Information Disclosure (Leakage of sensitive data)
- **Vulnerability**: A hardcoded API key (`AIzaSyD-mock-key-value-12345`) exists in `app/agent.py`. Hardcoding secrets in source code risks severe credential compromise if the repository is leaked. Unhandled exceptions in the tool could also leak stack traces.
- **Mitigation**: Remove the hardcoded key and use environment variables (`os.environ`) or a secure Secret Manager for the Gemini API key. Ensure exceptions are caught and sanitized before reaching the user.

### Denial of Service (Resource exhaustion)
- **Vulnerability**: There are no rate limits on user queries interacting with the agent. An attacker could flood the agent with requests, consuming expensive LLM API quota and compute resources.
- **Mitigation**: Implement strict rate limiting (e.g., token bucket) on the API layer serving the agent per user/IP.

### Elevation of Privilege (Bypassing access controls)
- **Vulnerability**: The tool allows redemption if any `user_id` string is provided, but it does not perform an authorization check to verify if the active session matches that user or if the user is in good standing to use discounts.
- **Mitigation**: Enforce authorization checks within the tool implementation utilizing a verified context object rather than raw string parameters.
