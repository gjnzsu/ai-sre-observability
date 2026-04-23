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
        Dictionary containing pricing configuration in nested format:
        {
            "provider": {
                "model": {
                    "prompt": float,
                    "completion": float
                }
            }
        }
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

            if not config or 'models' not in config:
                logger.warning(f"No models found in pricing config: {config_path}")
                return {}

            # Transform list format to nested dictionary
            pricing = {}
            for model_config in config['models']:
                provider = model_config['provider']
                model = model_config['model']

                if provider not in pricing:
                    pricing[provider] = {}

                pricing[provider][model] = {
                    'prompt': model_config['input_price_per_million'],
                    'completion': model_config['output_price_per_million']
                }

            logger.info(f"Successfully loaded pricing config from {config_path}")
            return pricing

    except FileNotFoundError:
        logger.warning(f"Pricing config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config file {config_path}: {e}")
        return {}
    except KeyError as e:
        logger.error(f"Missing required field in pricing config: {e}")
        return {}
