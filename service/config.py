"""Configuration loader for LLM pricing."""

import logging
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


def load_pricing_config(config_path: str) -> Dict[str, Any]:
    """Load pricing configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing pricing configuration, or empty dict on error
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f"Successfully loaded pricing config from {config_path}")
            return config if config else {}
    except FileNotFoundError:
        logger.warning(f"Pricing config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config file {config_path}: {e}")
        return {}
