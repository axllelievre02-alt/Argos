"""Gestionnaire des modèles de langage d'ARGOS.

Rôle central (README §24 à §26) :

    ARGOS
      ↓
    ModelManager
      ↓
    ┌──────────┬──────────┬──────────┐
    │ Ollama   │ API      │ modèle C │
    └──────────┴──────────┴──────────┘

Le ModelManager permet :

    - d'enregistrer plusieurs fournisseurs ;
    - de choisir un modèle selon le type de tâche ;
    - de remplacer un modèle par un autre sans toucher au reste ;
    - de continuer à fonctionner si un modèle disparaît.

Le modèle reste un outil d'ARGOS, jamais son identité.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.config import ArgosConfig
from core.models.base import ModelError, ModelProvider
from core.models.ollama_provider import OllamaProvider

# Types de tâches reconnus pour le routage automatique.
TASK_GENERAL = "general"
TASK_CODE = "code"
TASK_REASONING = "reasoning"
TASK_FAST = "fast"

TASK_KINDS = (
    TASK_GENERAL,
    TASK_CODE,
    TASK_REASONING,
    TASK_FAST,
)


class ModelManager:
    """Choisit et interroge le modèle adapté à chaque tâche."""

    def __init__(
        self,
        config: Optional[ArgosConfig] = None,
        providers: Optional[List[ModelProvider]] = None,
    ):

        self.config = config or ArgosConfig()

        self.providers: Dict[str, ModelProvider] = {}

        if providers:
            for provider in providers:
                self.register(provider)
        else:
            self.register(
                OllamaProvider(
                    timeout=self.config.get("models.timeout"),
                )
            )

        # Dernier modèle réellement utilisé (utile pour l'interface).
        self.last_model: Optional[str] = None

        # Dernière erreur rencontrée, exposée pour diagnostic.
        self.last_error: Optional[str] = None

    # =========================================================
    # FOURNISSEURS
    # =========================================================

    def register(self, provider: ModelProvider) -> None:

        if not isinstance(provider, ModelProvider):
            raise TypeError(
                "Un fournisseur doit hériter de ModelProvider."
            )

        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[ModelProvider]:

        return self.providers.get(name)

    def default_provider(self) -> ModelProvider:

        if not self.providers:
            raise ModelError("Aucun fournisseur de modèle enregistré.")

        return next(iter(self.providers.values()))

    # =========================================================
    # CATALOGUE
    # =========================================================

    def is_available(self) -> bool:
        """Indique si au moins un fournisseur répond."""

        return any(
            provider.is_available()
            for provider in self.providers.values()
        )

    def available_models(self) -> List[str]:
        """Retourne tous les modèles utilisables, sans doublon."""

        models: List[str] = []

        for provider in self.providers.values():

            try:
                found = provider.list_models()

            except ModelError as error:
                self.last_error = str(error)
                continue

            for name in found:
                if name not in models:
                    models.append(name)

        models.sort()

        return models

    # =========================================================
    # ROUTAGE
    # =========================================================

    def configured_model(self, task: str = TASK_GENERAL) -> str:
        """Retourne le modèle configuré pour un type de tâche."""

        route = self.config.get(f"models.routes.{task}")

        if not route:
            route = self.config.get("models.default", "")

        return str(route or "").strip()

    def resolve_model(self, task: str = TASK_GENERAL) -> str:
        """Choisit le modèle réellement utilisable pour une tâche.

        Ordre de décision :

            1. modèle configuré pour la tâche ;
            2. modèle par défaut ;
            3. premier modèle installé ;
            4. modèle configuré (même absent) pour produire une
               erreur explicite.
        """

        requested = self.configured_model(task)

        available = self.available_models()

        if not available:
            if requested:
                return requested

            raise ModelError(
                "Aucun modèle disponible. Ollama est-il démarré ?"
            )

        match = self._match(requested, available)

        if match:
            return match

        default = str(self.config.get("models.default", "")).strip()

        match = self._match(default, available)

        if match:
            return match

        return available[0]

    @staticmethod
    def _match(requested: str, available: List[str]) -> Optional[str]:
        """Associe un nom demandé à un modèle réellement installé.

        Permet d'écrire "qwen3" dans la configuration alors qu'Ollama
        expose le modèle sous le nom "qwen3:4b".
        """

        if not requested:
            return None

        if requested in available:
            return requested

        prefix = f"{requested}:"

        for name in available:
            if name.startswith(prefix):
                return name

        return None

    # =========================================================
    # GENERATION
    # =========================================================

    def generate(
        self,
        messages: List[Dict[str, str]],
        task: str = TASK_GENERAL,
        options: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> str:
        """Produit une réponse en utilisant le meilleur modèle disponible.

        Si le modèle choisi échoue, ARGOS essaie automatiquement un
        autre modèle installé avant d'abandonner.
        """

        provider = self.default_provider()

        target = model or self.resolve_model(task)

        errors: List[str] = []

        try:
            answer = provider.chat(target, messages, options)

        except ModelError as error:
            errors.append(str(error))

            answer = None

        if answer is not None:
            self.last_model = target
            self.last_error = None

            return answer

        # -----------------------------------------------------
        # Reprise sur un autre modèle installé
        # -----------------------------------------------------

        for fallback in self.available_models():

            if fallback == target:
                continue

            try:
                answer = provider.chat(fallback, messages, options)

            except ModelError as error:
                errors.append(str(error))
                continue

            self.last_model = fallback
            self.last_error = None

            return answer

        self.last_error = errors[-1] if errors else "Aucun modèle utilisable."

        raise ModelError(self.last_error)

    def generate_text(
        self,
        prompt: str,
        system: Optional[str] = None,
        task: str = TASK_GENERAL,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Raccourci pour une requête simple sans historique."""

        messages: List[Dict[str, str]] = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return self.generate(
            messages,
            task=task,
            options=options,
        )

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def set_default_model(self, model: str) -> None:

        self._validate_model_name(model)

        self.config.set("models.default", model)

    def set_route(self, task: str, model: str) -> None:

        if task not in TASK_KINDS:
            raise ValueError(
                f"Type de tâche inconnu : {task}. "
                f"Types valides : {', '.join(TASK_KINDS)}."
            )

        self._validate_model_name(model)

        self.config.set(f"models.routes.{task}", model)

    def refresh(self) -> List[str]:
        """Relit le catalogue des modèles installés."""

        models: List[str] = []

        for provider in self.providers.values():

            refresh = getattr(provider, "refresh", None)

            if callable(refresh):
                try:
                    models = refresh()
                except ModelError as error:
                    self.last_error = str(error)

        return models

    @staticmethod
    def _validate_model_name(model: str) -> None:

        if not isinstance(model, str) or not model.strip():
            raise ValueError("Le nom du modèle ne peut pas être vide.")

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self) -> Dict[str, Any]:

        return {
            "available": self.is_available(),
            "models": self.available_models(),
            "default": self.config.get("models.default"),
            "routes": {
                task: self.configured_model(task) for task in TASK_KINDS
            },
            "last_model": self.last_model,
            "last_error": self.last_error,
            "providers": {
                name: provider.name
                for name, provider in self.providers.items()
            },
        }
