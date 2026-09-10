import pytest

from scraper.config import Config, ConfigError, load_config


def test_load_example_config():
    config = load_config("config.example.toml")
    assert config.name == "quotes-example"
    assert config.start_urls == ["https://quotes.toscrape.com/"]
    assert config.item.selector == "div.quote"
    assert len(config.item.fields) == 3
    assert config.pagination.max_pages == 3


def test_missing_user_agent_raises():
    with pytest.raises(ConfigError):
        Config.from_dict({"start_urls": ["https://example.com"], "item": {"selector": "div"}})


def test_missing_item_raises():
    with pytest.raises(ConfigError):
        Config.from_dict({"user_agent": "bot", "start_urls": ["https://example.com"]})
