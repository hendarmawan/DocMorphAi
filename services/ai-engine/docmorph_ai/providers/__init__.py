from __future__ import annotations

from docmorph_ai.providers.base import AIProvider, ContentEditRefused, NoDesignChange


def get_provider(name: str = "heuristic", **kwargs) -> AIProvider:
    if name == "heuristic":
        from docmorph_ai.providers.heuristic import HeuristicProvider

        return HeuristicProvider()
    if name == "anthropic":
        from docmorph_ai.providers.anthropic import AnthropicProvider

        return AnthropicProvider(**kwargs)
    raise ValueError(f"Unknown AI provider {name!r}")


__all__ = ["AIProvider", "ContentEditRefused", "NoDesignChange", "get_provider"]
