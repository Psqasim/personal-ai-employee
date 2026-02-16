"""
Environment Variable Validator - Security Partition Enforcement
Validates Cloud vs Local environment configurations
"""
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class EnvValidationError(Exception):
    """Raised when environment validation fails"""
    pass


class EnvValidator:
    """
    Validate environment variables for Cloud and Local agents
    Enforce security partition: Cloud NEVER has send credentials
    """

    # Prohibited variables for Cloud Agent (MUST be Local-only)
    CLOUD_PROHIBITED = [
        "SMTP_PASSWORD",
        "WHATSAPP_SESSION_PATH",
        "BANK_API_TOKEN",
        "PAYMENT_API_KEY",
        "ODOO_PASSWORD",
        "LINKEDIN_ACCESS_TOKEN",
        "FACEBOOK_ACCESS_TOKEN",
        "INSTAGRAM_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET",
    ]

    # Required variables for Cloud Agent
    CLOUD_REQUIRED = [
        "TIER",
        "VAULT_PATH",
        "GIT_REMOTE_URL",
        "CLAUDE_API_KEY",
        "WHATSAPP_NOTIFICATION_NUMBER",
    ]

    # Required variables for Local Agent
    LOCAL_REQUIRED = [
        "TIER",
        "VAULT_PATH",
        "GIT_REMOTE_URL",
        "CLAUDE_API_KEY",
        "SMTP_HOST",
        "SMTP_PASSWORD",  # Local MUST have send credentials
        "DASHBOARD_URL",
    ]

    @staticmethod
    def validate_cloud_agent() -> Dict[str, List[str]]:
        """
        Validate Cloud Agent environment

        Returns:
            Dict with "errors" and "warnings" lists

        Raises:
            EnvValidationError: If critical validation fails
        """
        errors = []
        warnings = []

        # Check TIER
        tier = os.getenv("TIER", "")
        if tier != "platinum":
            errors.append(f"TIER must be 'platinum', got '{tier}'")

        # Check prohibited variables (Cloud MUST NOT have)
        for var in EnvValidator.CLOUD_PROHIBITED:
            if os.getenv(var):
                errors.append(
                    f"Security violation: Cloud Agent MUST NOT have {var}. "
                    f"This is a Local-only credential."
                )

        # Check required variables
        for var in EnvValidator.CLOUD_REQUIRED:
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required variable: {var}")
            elif var == "CLAUDE_API_KEY" and not value.startswith("sk-ant-"):
                errors.append(f"Invalid CLAUDE_API_KEY format (must start with 'sk-ant-')")
            elif var == "GIT_REMOTE_URL" and not value.startswith("git@"):
                warnings.append("GIT_REMOTE_URL should use SSH format (git@...)")

        # Check ENABLE_CLOUD_AGENT
        enable_cloud = os.getenv("ENABLE_CLOUD_AGENT", "false").lower()
        if enable_cloud != "true":
            warnings.append("ENABLE_CLOUD_AGENT is not 'true', Cloud Agent may not run")

        if errors:
            raise EnvValidationError(
                f"Cloud Agent environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        if warnings:
            for warning in warnings:
                logger.warning(f"Cloud Agent: {warning}")

        logger.info("✅ Cloud Agent environment validated successfully")
        return {"errors": errors, "warnings": warnings}

    @staticmethod
    def validate_local_agent() -> Dict[str, List[str]]:
        """
        Validate Local Agent environment

        Returns:
            Dict with "errors" and "warnings" lists

        Raises:
            EnvValidationError: If critical validation fails
        """
        errors = []
        warnings = []

        # Check TIER
        tier = os.getenv("TIER", "")
        if tier != "platinum":
            errors.append(f"TIER must be 'platinum', got '{tier}'")

        # Check required variables
        for var in EnvValidator.LOCAL_REQUIRED:
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required variable: {var}")

        # Check ENABLE_CLOUD_AGENT (should be false for Local)
        enable_cloud = os.getenv("ENABLE_CLOUD_AGENT", "false").lower()
        if enable_cloud == "true":
            warnings.append(
                "ENABLE_CLOUD_AGENT is 'true', but this is Local Agent. "
                "Should be 'false' for Local deployment."
            )

        # Verify send credentials exist (security check)
        if not os.getenv("SMTP_PASSWORD"):
            errors.append("Local Agent MUST have SMTP_PASSWORD for email sending")

        if errors:
            raise EnvValidationError(
                f"Local Agent environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        if warnings:
            for warning in warnings:
                logger.warning(f"Local Agent: {warning}")

        logger.info("✅ Local Agent environment validated successfully")
        return {"errors": errors, "warnings": warnings}

    @staticmethod
    def validate(agent_type: str) -> Dict[str, List[str]]:
        """
        Validate environment for specified agent type

        Args:
            agent_type: "cloud" or "local"

        Returns:
            Dict with validation results

        Raises:
            EnvValidationError: If validation fails
        """
        if agent_type == "cloud":
            return EnvValidator.validate_cloud_agent()
        elif agent_type == "local":
            return EnvValidator.validate_local_agent()
        else:
            raise ValueError(f"Invalid agent_type: {agent_type}. Must be 'cloud' or 'local'")

    @staticmethod
    def print_config_summary(agent_type: str):
        """
        Print configuration summary for debugging

        Args:
            agent_type: "cloud" or "local"
        """
        print(f"\n{'='*50}")
        print(f"  {agent_type.upper()} AGENT CONFIGURATION")
        print(f"{'='*50}")

        # Safe variables to print
        safe_vars = [
            "TIER",
            "ENABLE_CLOUD_AGENT",
            f"{agent_type.upper()}_AGENT_ID",
            "VAULT_PATH",
            "GIT_REMOTE_URL",
            "GIT_BRANCH",
            "DASHBOARD_URL",
            "ENABLE_ODOO",
        ]

        for var in safe_vars:
            value = os.getenv(var, "(not set)")
            print(f"  {var}: {value}")

        # Show credential status (not values)
        print(f"\n  Credentials:")
        cred_vars = ["CLAUDE_API_KEY", "SMTP_PASSWORD", "LINKEDIN_ACCESS_TOKEN"]
        for var in cred_vars:
            status = "✓ SET" if os.getenv(var) else "✗ MISSING"
            print(f"    {var}: {status}")

        print(f"{'='*50}\n")
