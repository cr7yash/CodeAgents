"""
Tests for the Portkey gateway provider.

The behaviour under test is request *shaping*: the gateway forwards whatever
we send to the upstream vendor, which rejects unsupported parameters with a
400. These tests pin the rules that were established by probing the live
gateway, so a future refactor cannot quietly reintroduce a bad request.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.providers.base import GenerationConfig
from src.providers.portkey_provider import PortkeyProvider


def make_response(
    content="hello",
    prompt_tokens=10,
    completion_tokens=5,
    finish_reason="stop",
    reasoning_tokens=None,
):
    """Build a minimal OpenAI-shaped chat completion response."""
    details = (
        SimpleNamespace(reasoning_tokens=reasoning_tokens)
        if reasoning_tokens is not None
        else None
    )
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            completion_tokens_details=details,
        ),
    )


def build(response=None):
    """Provider wired to a mocked client; returns (provider, create_mock)."""
    provider = PortkeyProvider(api_key="test-key", base_url="https://api.portkey.ai/v1")
    create = AsyncMock(return_value=response or make_response())
    provider.client.chat.completions.create = create
    return provider, create


async def call(provider, model, **config_kwargs):
    await provider.generate(prompt="hi", model=model, config=GenerationConfig(**config_kwargs))


# --------------------------------------------------------------------------
# Parameter shaping
# --------------------------------------------------------------------------

async def test_never_sends_max_tokens():
    """Reasoning models hard-reject max_tokens, so we never send it."""
    provider, create = build()
    await call(provider, "gpt-4o-mini")
    kwargs = create.call_args.kwargs
    assert "max_tokens" not in kwargs
    assert kwargs["max_completion_tokens"] == 1000


async def test_standard_model_gets_all_sampling_params():
    provider, create = build()
    await call(provider, "gpt-4o-mini", temperature=0.3, top_p=0.9, stop_sequences=["END"])
    kwargs = create.call_args.kwargs
    assert kwargs["temperature"] == 0.3
    assert kwargs["top_p"] == 0.9
    assert kwargs["stop"] == ["END"]


async def test_strict_reasoning_model_omits_all_sampling_params():
    """gpt-5.5 rejects temperature, top_p and stop."""
    provider, create = build()
    await call(provider, "gpt-5.5", temperature=0.3, top_p=0.9, stop_sequences=["END"])
    kwargs = create.call_args.kwargs
    assert "temperature" not in kwargs
    assert "top_p" not in kwargs
    assert "stop" not in kwargs


async def test_sampled_reasoning_model_keeps_temperature_but_drops_stop():
    """gpt-5.4 accepts temperature/top_p but rejects stop."""
    provider, create = build()
    await call(provider, "gpt-5.4", temperature=0.3, top_p=0.9, stop_sequences=["END"])
    kwargs = create.call_args.kwargs
    assert kwargs["temperature"] == 0.3
    assert kwargs["top_p"] == 0.9
    assert "stop" not in kwargs


async def test_newer_claude_omits_sampling_but_keeps_stop():
    """claude-opus-5 rejects temperature/top_p while stop still works."""
    provider, create = build()
    await call(provider, "claude-opus-5", temperature=0.3, top_p=0.9, stop_sequences=["END"])
    kwargs = create.call_args.kwargs
    assert "temperature" not in kwargs
    assert "top_p" not in kwargs
    assert kwargs["stop"] == ["END"]


async def test_reasoning_effort_only_sent_when_supported():
    provider, create = build()
    await call(provider, "gpt-5.5", reasoning_effort="low")
    assert create.call_args.kwargs["reasoning_effort"] == "low"

    provider, create = build()
    await call(provider, "gpt-4o-mini", reasoning_effort="low")
    assert "reasoning_effort" not in create.call_args.kwargs


async def test_reasoning_effort_omitted_when_unset():
    provider, create = build()
    await call(provider, "gpt-5.5")
    assert "reasoning_effort" not in create.call_args.kwargs


async def test_reasoning_effort_never_sent_to_claude():
    """Bedrock Claude rejects it: 'thinking.type.enabled is not supported'."""
    provider, create = build()
    await call(provider, "claude-opus-5", reasoning_effort="low")
    assert "reasoning_effort" not in create.call_args.kwargs


async def test_empty_stop_sequences_not_sent():
    provider, create = build()
    await call(provider, "gpt-4o-mini", stop_sequences=[])
    assert "stop" not in create.call_args.kwargs


async def test_model_id_is_fully_qualified():
    provider, create = build()
    await call(provider, "claude-opus-5")
    assert create.call_args.kwargs["model"] == "@zotgpt-api-bedrock/us.anthropic.claude-opus-5"


async def test_system_prompt_becomes_a_message():
    """Portkey is OpenAI-shaped; there is no Anthropic-style system kwarg."""
    provider, create = build()
    await provider.generate(prompt="hi", model="claude-opus-5", system_prompt="Be terse.")
    kwargs = create.call_args.kwargs
    assert "system" not in kwargs
    assert kwargs["messages"][0] == {"role": "system", "content": "Be terse."}
    assert kwargs["messages"][1] == {"role": "user", "content": "hi"}


# --------------------------------------------------------------------------
# Output token floor
# --------------------------------------------------------------------------

async def test_floor_raises_low_budget_for_reasoning_models():
    """A 64-token cap made gpt-5-nano return an empty string in practice."""
    provider, create = build()
    await call(provider, "gpt-5.5", max_tokens=64)
    assert create.call_args.kwargs["max_completion_tokens"] == 4000


async def test_floor_never_lowers_a_generous_budget():
    provider, create = build()
    await call(provider, "gpt-5.5", max_tokens=8000)
    assert create.call_args.kwargs["max_completion_tokens"] == 8000


async def test_no_floor_for_standard_models():
    provider, create = build()
    await call(provider, "gpt-4o-mini", max_tokens=64)
    assert create.call_args.kwargs["max_completion_tokens"] == 64


# --------------------------------------------------------------------------
# Response parsing
# --------------------------------------------------------------------------

async def test_null_content_becomes_empty_string():
    """Some Gemini routes return null content rather than ''."""
    provider, _ = build(response=make_response(content=None))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert result.text == ""
    assert result.is_empty is True


async def test_whitespace_only_counts_as_empty():
    provider, _ = build(response=make_response(content="   \n "))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert result.is_empty is True


async def test_truncation_is_flagged():
    provider, _ = build(response=make_response(finish_reason="length"))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert result.truncated is True


async def test_reasoning_tokens_captured():
    provider, _ = build(response=make_response(reasoning_tokens=128))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert result.reasoning_tokens == 128


async def test_missing_token_details_defaults_to_zero():
    """completion_tokens_details is absent on several upstream routes."""
    provider, _ = build(response=make_response(reasoning_tokens=None))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert result.reasoning_tokens == 0


async def test_usage_and_model_are_reported():
    provider, _ = build(response=make_response(prompt_tokens=11, completion_tokens=7))
    result = await provider.generate(prompt="hi", model="gpt-4o-mini")
    assert (result.input_tokens, result.output_tokens) == (11, 7)
    assert result.total_tokens == 18
    assert result.model == "gpt-4o-mini"
    assert result.latency_ms > 0


# --------------------------------------------------------------------------
# Model resolution and pricing
# --------------------------------------------------------------------------

async def test_unknown_model_raises_before_any_request():
    provider, create = build()
    with pytest.raises(ValueError, match="Unknown model"):
        await provider.generate(prompt="hi", model="not-a-real-model")
    create.assert_not_awaited()


def test_priced_and_unpriced_models():
    provider = PortkeyProvider("k", "https://api.portkey.ai/v1")
    assert provider.is_priced("gpt-4o-mini") is True
    assert provider.get_cost_per_1k_tokens("gpt-4o-mini")["input"] > 0

    # gpt-5.5 has no confirmed public list price.
    assert provider.is_priced("gpt-5.5") is False
    assert provider.get_cost_per_1k_tokens("gpt-5.5") == {"input": 0.0, "output": 0.0}


def test_pricing_of_unknown_model_is_zero_not_an_error():
    provider = PortkeyProvider("k", "https://api.portkey.ai/v1")
    assert provider.get_cost_per_1k_tokens("nope") == {"input": 0.0, "output": 0.0}
    assert provider.is_priced("nope") is False


def test_available_models_span_all_families():
    provider = PortkeyProvider("k", "https://api.portkey.ai/v1")
    assert "claude-opus-5" in provider.available_models
    assert "gpt-5.5" in provider.available_models
    assert provider.name == "portkey"


def test_estimate_cost_for_priced_model():
    provider = PortkeyProvider("k", "https://api.portkey.ai/v1")
    cost, priced = provider.estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=1000)
    assert priced is True
    assert cost == pytest.approx(0.00015 + 0.0006)


def test_estimate_cost_for_unpriced_model():
    provider = PortkeyProvider("k", "https://api.portkey.ai/v1")
    cost, priced = provider.estimate_cost("gpt-5.5", input_tokens=1000, output_tokens=1000)
    assert priced is False
    assert cost == 0.0
