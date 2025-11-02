"""
Gets configurations from .env file or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Optional
from entityxtract.logging_config import get_logger

logger = get_logger(__name__)

DOTENV_PATH = Path(__file__).parent.parent.parent / ".env"
if not DOTENV_PATH.exists():
    logger.info(
        f"'.env' file not found at {DOTENV_PATH}. Skipping loading environment variables from .env file."
    )
else:
    logger.info(f"Loading environment variables from {DOTENV_PATH}")

load_dotenv(dotenv_path=DOTENV_PATH, override=True)


def get_config(key: str) -> Optional[Any]:
    """Get a particular environment variable

    Args:
        key (str): The environment variable key to retrieve.

    Returns:
        Optional[Any]: The value of the environment variable or None if not found.
    """

    # Environment variable takes precedence
    env_value = os.environ.get(key, None)

    if env_value is not None:
        return env_value

    logger.warning(f"Environment variable '{key}' not found.")

    return None


if __name__ == "__main__":
    print("OPENAI_DEFAULT_MODEL =", get_config("OPENAI_DEFAULT_MODEL"))
