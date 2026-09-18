"""Configuration globale d'ARGOS.

ArgosConfig centralise les réglages techniques du système :

    - modèles de langage et routage
    - niveau de permissions
    - modes d'exécution
    - interface et voix

Elle est strictement indépendante de ProfileMemory.

    ProfileMemory  -> ce qu'ARGOS sait de l'utilisateur
    ArgosConfig    -> la manière dont ARGOS fonctionne

La configuration est lue et écrite dans data/settings.json
et reste donc portable avec le dossier du projet.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict

from core.paths import SETTINGS_FILE, ensure_directories

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": 1,
    "models": {
        # Modèle utilisé par défaut.
        "default": "qwen3:4b",
        # Modèles dédiés par type de tâche.
        # Une valeur vide signifie : utiliser le modèle par défaut.
        "routes": {
            "general": "qwen3:4b",
            "code": "qwen3:4b",
            "reasoning": "qwen3:4b",
            "fast": "qwen3:4b",
        },
        # Interdit tout appel à un service distant.
        "local_only": True,
        "timeout": 120,
    },
    "permissions": {
        # Niveau courant accordé à ARGOS.
        "level": 1,
        # Niveau à partir duquel une confirmation est exigée.
        "confirm_from": 2,
        # Dossiers supplémentaires autorisés en écriture.
        "extra_allowed_paths": [],
    },
    "modes": {
        "current": "normal",
    },
    "interface": {
        "user_label": "Ikaris",
        "assistant_label": "ARGOS",
        "language": "fr",
    },
    "voice": {
        "enabled": False,
        "rate": 175,
        "volume": 0.9,
    },
    "memory": {
        "persist_conversation": True,
        "max_messages": 50,
        "long_term": True,
        "learn_from_internet": True,
    },
    "tools": {
        "enabled": True,
        "timeout": 60,
    },
    "verification": {
        "enabled": True,
        "max_attempts": 3,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Fusionne deux dictionnaires en conservant les valeurs par défaut.

    Les clés absentes du fichier de configuration sont complétées
    automatiquement, ce qui permet de faire évoluer les réglages
    sans casser une configuration existante.
    """

    result = deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


class ArgosConfig:
    """Accès unifié aux réglages d'ARGOS."""

    def __init__(self, file_path=None):

        ensure_directories()

        self.file_path = file_path or SETTINGS_FILE

        self._settings: Dict[str, Any] = {}

        self.load()

    # =========================================================
    # LECTURE / ECRITURE
    # =========================================================

    def load(self) -> Dict[str, Any]:
        """Charge les réglages depuis le disque."""

        data: Dict[str, Any] = {}

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                loaded = json.load(file)

            if isinstance(loaded, dict):
                data = loaded

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            data = {}

        self._settings = _deep_merge(DEFAULT_SETTINGS, data)

        # Un fichier absent ou incomplet est immédiatement réécrit
        # afin que l'utilisateur puisse inspecter ses réglages.
        if data != self._settings:
            self.save()

        return self._settings

    def save(self) -> None:
        """Ecrit les réglages de façon atomique."""

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temporary = self.file_path.with_suffix(".tmp")

        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(
                self._settings,
                file,
                ensure_ascii=False,
                indent=4,
            )

        temporary.replace(self.file_path)

    # =========================================================
    # ACCES
    # =========================================================

    def all(self) -> Dict[str, Any]:
        """Retourne une copie complète des réglages."""

        return deepcopy(self._settings)

    def get(self, key: str, default: Any = None) -> Any:
        """Lit une valeur avec une clé pointée.

        Exemple :

            config.get("models.default")
        """

        node: Any = self._settings

        for part in str(key).split("."):
            if not isinstance(node, dict) or part not in node:
                return default

            node = node[part]

        return node

    def set(self, key: str, value: Any) -> None:
        """Ecrit une valeur avec une clé pointée."""

        parts = [part for part in str(key).split(".") if part]

        if not parts:
            raise ValueError("Clé de configuration vide.")

        node = self._settings

        for part in parts[:-1]:
            child = node.get(part)

            if not isinstance(child, dict):
                child = {}
                node[part] = child

            node = child

        node[parts[-1]] = value

        self.save()

    def section(self, name: str) -> Dict[str, Any]:
        """Retourne une section complète sous forme de dictionnaire."""

        value = self.get(name, {})

        if not isinstance(value, dict):
            return {}

        return deepcopy(value)

    # =========================================================
    # REINITIALISATION
    # =========================================================

    def reset(self) -> None:
        """Restaure les réglages par défaut."""

        self._settings = deepcopy(DEFAULT_SETTINGS)

        self.save()

    def summary(self) -> Dict[str, Any]:
        """Résumé utilisable par l'interface."""

        return {
            "file": str(self.file_path),
            "model": self.get("models.default"),
            "permission_level": self.get("permissions.level"),
            "mode": self.get("modes.current"),
            "voice": bool(self.get("voice.enabled")),
        }
