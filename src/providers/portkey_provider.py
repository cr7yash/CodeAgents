"""Access models through the Portkey AI gateway."""

import time
from typing import Any

from openai import AsyncOpenAI

from src.providers.base import GenerationConfig, GenerationResult, LLMProvider
from src.providers.portkey_catalog import ModelSpec, all_models, find_any


class PortkeyProvider(LLMProvider):
    """
    Access any catalogued model through the Portkey AI gateway.

    Portkey speaks the OpenAI chat-completions protocol for every upstream
    vendor, so a single client covers all of them. Requests are assembled per
    model rather than uniformly: the gateway forwards unsupported parameters
    straight to the upstream vendor, which rejects them with a 400. See
    ``portkey_catalog`` for the measured parameter matrix.
    """

    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def name(self) -> str:
        return "portkey"

    @property
    def available_models(self) -> list[str]:
        return [spec.slug for spec in all_models()]

    def _resolve(self, model: str) -> ModelSpec:
        spec = find_any(model)
        if spec is None:
            raise ValueError(
                f"Unknown model '{model}'. Run `codeagents models` to see "
                f"available models."
            )
        return spec

    async def generate(
        self,
        prompt: str,
        model: str,
        config: GenerationConfig | None = None,
        system_prompt: str | None = None,
    ) -> GenerationResult:
        """Generate text through the Portkey gateway."""
        config = config or GenerationConfig()
        spec = self._resolve(model)
        caps = spec.caps

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Always max_completion_tokens: reasoning models reject max_tokens
        # outright, and every model on every route accepts this form.
        kwargs: dict[str, Any] = {
            "model": spec.model_id,
            "messages": messages,
            "max_completion_tokens": max(config.max_tokens, caps.min_output_tokens),
        }
        if caps.temperature:
            kwargs["temperature"] = config.temperature
        if caps.top_p:
            kwargs["top_p"] = config.top_p
        if caps.stop and config.stop_sequences:
            kwargs["stop"] = config.stop_sequences
        if caps.reasoning_effort and config.reasoning_effort:
            kwargs["reasoning_effort"] = config.reasoning_effort

        start = time.perf_counter()
        response = await self.client.chat.completions.create(**kwargs)
        latency = (time.perf_counter() - start) * 1000

        choice = response.choices[0]
        usage = response.usage

        # Some routes return null content rather than an empty string.
        text = choice.message.content or ""

        # completion_tokens_details is absent on several upstream routes.
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0

        return GenerationResult(
            text=text,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            latency_ms=latency,
            model=model,
            finish_reason=choice.finish_reason,
            reasoning_tokens=reasoning_tokens,
        )

    def is_priced(self, model: str) -> bool:
        """Whether list pricing is known for this model."""
        spec = find_any(model)
        return spec is not None and spec.pricing is not None

    def get_cost_per_1k_tokens(self, model: str) -> dict[str, float]:
        """Pricing per 1K tokens, or zeros when unknown (see is_priced)."""
        spec = find_any(model)
        if spec is None or spec.pricing is None:
            return {"input": 0.0, "output": 0.0}
        return dict(spec.pricing)

    def estimate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> tuple[float, bool]:
        """
        Estimate USD cost for a generation.

        Returns (cost_usd, pricing_known). When pricing is unknown, cost_usd
        is 0.0 and pricing_known is False — callers must not present that as
        a genuinely free run.
        """
        if not self.is_priced(model):
            return 0.0, False
        pricing = self.get_cost_per_1k_tokens(model)
        cost = (input_tokens / 1000) * pricing["input"] + (
            output_tokens / 1000
        ) * pricing["output"]
        return cost, True
