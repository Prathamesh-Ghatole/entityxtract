"""
Gets configurations from .env file or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from typing import Any, Optional
from entityxtract.logging_config import get_logger

logger = get_logger(__name__)

# Try to find .env file:
# 1. First check the source-tree relative path (for development)
# 2. Fall back to find_dotenv() which searches CWD and parent directories (for installed package)
_SOURCE_DOTENV = Path(__file__).parent.parent.parent / ".env"

if _SOURCE_DOTENV.exists():
    logger.info(f"Loading environment variables from {_SOURCE_DOTENV}")
    load_dotenv(dotenv_path=_SOURCE_DOTENV, override=True)
else:
    _found = find_dotenv(usecwd=True)
    if _found:
        logger.info(f"Loading environment variables from {_found}")
        load_dotenv(dotenv_path=_found, override=True)
    else:
        logger.info("No .env file found. Using environment variables as-is.")


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
