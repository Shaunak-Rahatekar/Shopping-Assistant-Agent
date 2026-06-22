import sys
import json

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)

        payload = json.loads(raw_input)

        # Recursively search the payload for blocked patterns
        def contains_destructive_pattern(data, patterns):
            if isinstance(data, dict):
                for val in data.values():
                    if contains_destructive_pattern(val, patterns):
                        return True
            elif isinstance(data, list):
                for item in data:
                    if contains_destructive_pattern(item, patterns):
                        return True
            elif isinstance(data, str):
                data_lower = data.lower()
                for pattern in patterns:
                    if pattern in data_lower:
                        return True
            return False

        blocked_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "remove-item -recurse -force c:\\",
            "remove-item -recurse -force /",
            "del /s /q /f c:\\"
        ]

        # If any destructive pattern is found in the tool call arguments, block it
        if contains_destructive_pattern(payload, blocked_patterns):
            sys.stderr.write("Validation Error: Destructive command pattern (e.g., 'rm -rf /') detected. Execution blocked by hooks.json.\n")
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Validation Script Error: {str(e)}\n")
        # Fail-open if we can't parse the JSON so we don't accidentally brick the agent
        sys.exit(0)

if __name__ == "__main__":
    main()
