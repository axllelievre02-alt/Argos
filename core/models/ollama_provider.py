"""Fournisseur de modèles basé sur Ollama.

Ollama permet à ARGOS d'utiliser un modèle local, sans API distante
et sans envoyer la mémoire personnelle de l'utilisateur à un service
externe (confidentialité, README §41).

Ce fournisseur est le seul endroit du projet qui connaisse Ollama.
Le reste d'ARGOS ne parle qu'à ModelManager.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from ollama import Client

from core.models.base import ModelError, ModelProvider

DEFAULT_HOST = "http://127.0.0.1:11434"

# Certains modèles (qwen3...) renvoient leur raisonnement entre balises.
# Ce raisonnement ne doit jamais être montré à l'utilisateur.
_THINKING_BLOCK = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Retire les blocs de raisonnement internes d'un modèle."""

    if not text:
        return ""

    cleaned = _THINKING_BLOCK.sub("", text)

    return cleaned.strip()


class OllamaProvider(ModelProvider):
    """Fournisseur local s'appuyant sur le serveur Ollama."""

    name = "ollama"
    is_local = True

    def __init__(
        self,
        host: Optional[str] = None,
        timeout: Optional[float] = None,
        keep_alive: str = "10m",
    ):

        self.host = host or os.environ.get("OLLAMA_HOST") or DEFAULT_HOST

        options: Dict[str, Any] = {}

        if timeout:
            options["timeout"] = timeout

        self.keep_alive = keep_alive

        self._client = Client(host=self.host, **options)

        # Le catalogue des modèles est mis en cache : interroger Ollama
        # à chaque message ralentirait inutilement ARGOS.
        self._models_cache: Optional[List[str]] = None

    # =========================================================
    # DISPONIBILITE
    # =========================================================

    def is_available(self) -> bool:

        try:
            self._client.list()

        except Exception:
            return False

        return True

    def list_models(self) -> List[str]:
        """Retourne les modèles installés sur le serveur Ollama."""

        if self._models_cache is not None:
            return list(self._models_cache)

        try:
            response = self._client.list()

        except Exception as error:
            raise ModelError(
                f"Serveur Ollama injoignable ({self.host}) : {error}"
            ) from error

        names: List[str] = []

        for item in self._extract_models(response):
            name = self._model_name(item)

            if name:
                names.append(name)

        names.sort()

        self._models_cache = names

        return list(names)

    def refresh(self) -> List[str]:
        """Force la relecture du catalogue de modèles."""

        self._models_cache = None

        return self.list_models()

    # =========================================================
    # GENERATION
    # =========================================================

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not model:
            raise ModelError("Aucun modèle demandé.")

        self._require_model(model)

        generation_options: Dict[str, Any] = dict(options or {})

        think = generation_options.pop("think", False)

        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                options=generation_options or None,
                think=think,
                keep_alive=self.keep_alive,
            )

        except Exception as error:
            raise ModelError(
                f"Le modèle '{model}' n'a pas pu répondre : {error}"
            ) from error

        content = _strip_thinking(self._content(response))

        if not content:
            raise ModelError(
                f"Le modèle '{model}' a renvoyé une réponse vide."
            )

        return content

    # =========================================================
    # VERIFICATIONS
    # =========================================================

    def _require_model(self, model: str) -> None:
        """Vérifie qu'un modèle existe avant de lancer une génération."""

        try:
            available = self.list_models()

        except ModelError:
            # Le serveur n'est pas joignable : on laisse chat() produire
            # une erreur plus précise.
            return

        if model not in available:
            raise ModelError(
                f"Le modèle '{model}' n'est pas installé. "
                f"Modèles disponibles : "
                f"{', '.join(available) or 'aucun'}."
            )

    # =========================================================
    # EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_models(response) -> List[Any]:
        """Lit la réponse de Client.list() quelle que soit sa forme."""

        if isinstance(response, dict):
            models = response.get("models", [])

        else:
            models = getattr(response, "models", [])

        return list(models or [])

    @staticmethod
    def _model_name(item) -> str:
        """Lit le nom d'un modèle quelle que soit sa forme."""

        if isinstance(item, dict):
            return str(item.get("model") or item.get("name") or "").strip()

        return str(
            getattr(item, "model", None) or getattr(item, "name", "") or ""
        ).strip()

    @staticmethod
    def _content(response) -> str:
        """Lit le texte produit par Client.chat()."""

        message = None

        if isinstance(response, dict):
            message = response.get("message")

        else:
            message = getattr(response, "message", None)

        if message is None:
            return ""

        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self) -> Dict[str, Any]:

        summary = super().summary()

        summary["host"] = self.host

        return summary
