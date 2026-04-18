"""Tests for configuration loader."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from service.config import load_pricing_config


def test_load_pricing_config():
    """Test loading pricing config from YAML file."""
    # Create temporary YAML file with pricing data
    pricing_data = {
        "openai": {
            "gpt-4": {
                "input_price_per_million": 30.0,
                "output_price_per_million": 60.0
            },
            "gpt-3.5-turbo": {
                "input_price_per_million": 0.5,
                "output_price_per_million": 1.5
            }
        },
        "deepseek": {
            "deepseek-chat": {
                "input_price_per_million": 0.14,
                "output_price_per_million": 0.28
            }
        }
    }

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(pricing_data, f)
        temp_path = f.name

    try:
        # Load config
        config = load_pricing_config(temp_path)

        # Verify structure
        assert "openai" in config
        assert "deepseek" in config
        assert "gpt-4" in config["openai"]
        assert config["openai"]["gpt-4"]["input_price_per_million"] == 30.0
        assert config["openai"]["gpt-4"]["output_price_per_million"] == 60.0
        assert "deepseek-chat" in config["deepseek"]
        assert config["deepseek"]["deepseek-chat"]["input_price_per_million"] == 0.14
    finally:
        # Clean up temp file
        os.unlink(temp_path)


def test_load_pricing_config_file_not_found():
    """Test loading non-existent config returns empty dict."""
    config = load_pricing_config("/nonexistent/path/to/config.yaml")
    assert config == {}
