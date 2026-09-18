"""Interface commune des fournisseurs de modèles de langage.

ARGOS ne dépend d'aucun modèle particulier.

Un fournisseur peut être :

    - Ollama (local)
    - une API distante
    - un futur moteur interne

Tant qu'un fournisseur respecte cette interface, ARGOS peut
changer de cerveau linguistique sans être modifié.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ModelError(RuntimeError):
    """Erreur levée lorsqu'un modèle ne peut pas répondre."""


class ModelProvider:
    """Contrat minimal que tout fournisseur de modèle doit respecter."""

    # Nom technique du fournisseur ("ollama", "openai", "local"...).
    name = "base"

    # Indique si le fournisseur travaille uniquement en local.
    is_local = True

    # =========================================================
    # DISPONIBILITE
    # =========================================================

    def is_available(self) -> bool:
        """Indique si le fournisseur est joignable."""

        return False

    def list_models(self) -> List[str]:
        """Retourne les modèles réellement utilisables."""

        return []

    def supports(self, model: str) -> bool:
        """Indique si un modèle précis est utilisable."""

        return model in self.list_models()

    # =========================================================
    # GENERATION
    # =========================================================

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Retourne le texte produit par le modèle.

        Args:
            model: nom du modèle à utiliser.
            messages: historique au format OpenAI / Ollama.
            options: paramètres de génération (temperature, etc.).
        """

        raise NotImplementedError(
            f"Le fournisseur '{self.name}' doit implémenter chat()."
        )

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self) -> Dict[str, Any]:

        return {
            "provider": self.name,
            "local": self.is_local,
            "available": self.is_available(),
            "models": self.list_models(),
        }
