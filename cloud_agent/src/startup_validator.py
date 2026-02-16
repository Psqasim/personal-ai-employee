"""
Cloud Agent Startup Validator
Validates environment and refuses to start if prohibited credentials found
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.env_validator import EnvValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [STARTUP] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_and_start():
    """
    Validate Cloud Agent environment before starting
    Exit with error if validation fails
    """
    logger.info("="*50)
    logger.info("  CLOUD AGENT STARTUP VALIDATION")
    logger.info("="*50)

    try:
        # Run full validation
        result = EnvValidator.validate_cloud_agent()

        # Print config summary
        EnvValidator.print_config_summary("cloud")

        # Check for warnings
        if result["warnings"]:
            logger.warning(f"Found {len(result['warnings'])} warning(s):")
            for warning in result["warnings"]:
                logger.warning(f"  - {warning}")

        logger.info("✅ Cloud Agent environment validated successfully")
        logger.info("="*50)

        return True

    except Exception as e:
        logger.error("="*50)
        logger.error("❌ STARTUP VALIDATION FAILED")
        logger.error("="*50)
        logger.error(str(e))
        logger.error("")
        logger.error("Cloud Agent will NOT start until validation passes.")
        logger.error("Please fix the issues above and retry.")
        logger.error("="*50)

        return False


if __name__ == "__main__":
    # Run validation
    if validate_and_start():
        logger.info("Validation passed - Cloud Agent can start")
        sys.exit(0)
    else:
        logger.error("Validation failed - Cloud Agent will NOT start")
        sys.exit(1)
