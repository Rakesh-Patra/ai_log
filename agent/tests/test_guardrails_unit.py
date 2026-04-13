import sys
from unittest.mock import patch

# Ensure app is importable
sys.path.append(".")

try:
    from app.guardrails.validators import validate_input, validate_output
    print("Import successful", flush=True)
except Exception as e:
    print(f"Import failed: {e}", flush=True)
    sys.exit(1)

def run_env_tests():
    report = []
    report.append("=== Guardrails Environment Verification Report ===\n")

    # --- TEST PROD ---
    report.append("[PROD ENVIRONMENT]")
    with patch("app.guardrails.validators.get_settings") as mock_settings:
        mock_settings.return_value.app_env = "prod"
        mock_settings.return_value.guardrails_enabled = True
        mock_settings.return_value.allow_destructive_actions = False
        
        # Should Block Off-Topic
        res = validate_input("What is the weather?")
        report.append(f"  - Off-topic blocked: {not res.is_valid} (Expected: True)")
        
        # Should Block Destructive
        res = validate_input("Delete all pods")
        report.append(f"  - Destructive blocked: {not res.is_valid} (Expected: True)")

    # --- TEST STAGING ---
    report.append("\n[STAGING ENVIRONMENT]")
    with patch("app.guardrails.validators.get_settings") as mock_settings:
        mock_settings.return_value.app_env = "staging"
        mock_settings.return_value.guardrails_enabled = True
        mock_settings.return_value.allow_destructive_actions = False
        
        # Should ALLOW Off-Topic (but log/custom logic)
        res = validate_input("What is the weather?")
        report.append(f"  - Off-topic allowed: {res.is_valid} (Expected: True)")
        
        # Should Block Destructive
        res = validate_input("Delete all pods")
        report.append(f"  - Destructive blocked: {not res.is_valid} (Expected: True)")

    # --- TEST DEV ---
    report.append("\n[DEV ENVIRONMENT]")
    with patch("app.guardrails.validators.get_settings") as mock_settings:
        mock_settings.return_value.app_env = "dev"
        mock_settings.return_value.guardrails_enabled = True
        mock_settings.return_value.allow_destructive_actions = True
        
        # Should ALLOW Off-Topic
        res = validate_input("What is the weather?")
        report.append(f"  - Off-topic allowed: {res.is_valid} (Expected: True)")
        
        # Should ALLOW Destructive
        res = validate_input("Delete all pods")
        report.append(f"  - Destructive allowed: {res.is_valid} (Expected: True)")

    final_report = "\n".join(report)
    with open("tests/env_test_report.txt", "w") as f:
        f.write(final_report)
    print(final_report)

if __name__ == "__main__":
    run_env_tests()
