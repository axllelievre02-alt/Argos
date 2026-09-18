"""Couche modèles d'ARGOS.

Le modèle de langage n'est qu'un outil interchangeable :
ARGOS doit pouvoir changer de cerveau linguistique sans être réécrit.
"""

from core.models.base import ModelError, ModelProvider
from core.models.ollama_provider import OllamaProvider

__all__ = [
    "ModelError",
    "ModelProvider",
    "OllamaProvider",
]
