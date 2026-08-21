"""Tests for BaseAgent._extract_json's tolerant parsing of model output."""

import json

import pytest

from src.agents.base import BaseAgent

PAYLOAD = {"findings": [], "summary": "clean"}


class TestExtractJson:
    def test_plain_json(self):
        assert BaseAgent._extract_json(json.dumps(PAYLOAD)) == PAYLOAD

    def test_fenced_with_language_tag(self):
        text = f"```json\n{json.dumps(PAYLOAD)}\n```"
        assert BaseAgent._extract_json(text) == PAYLOAD

    def test_fenced_without_language_tag(self):
        text = f"```\n{json.dumps(PAYLOAD)}\n```"
        assert BaseAgent._extract_json(text) == PAYLOAD

    def test_prose_wrapped_json(self):
        text = f"Here is my analysis:\n{json.dumps(PAYLOAD)}\nLet me know if you need more."
        assert BaseAgent._extract_json(text) == PAYLOAD

    def test_leading_and_trailing_whitespace(self):
        text = f"   \n{json.dumps(PAYLOAD)}\n   "
        assert BaseAgent._extract_json(text) == PAYLOAD

    def test_malformed_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            BaseAgent._extract_json("not json at all")

    def test_empty_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            BaseAgent._extract_json("")
