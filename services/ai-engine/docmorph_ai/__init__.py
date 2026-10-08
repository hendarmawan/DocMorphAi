"""AI engine: document understanding and validated design patches.

Model providers are reached only through :class:`AIProvider` adapters, so the
platform can run fully offline (``heuristic``), on a hosted model
(``anthropic``) or on enterprise-controlled inference later.
"""

from docmorph_ai.engine import DesignChange, propose_design_change
from docmorph_ai.providers import AIProvider, ContentEditRefused, NoDesignChange, get_provider
from docmorph_ai.types import DocumentAnalysis

__all__ = [
    "AIProvider",
    "ContentEditRefused",
    "DesignChange",
    "DocumentAnalysis",
    "NoDesignChange",
    "get_provider",
    "propose_design_change",
]
