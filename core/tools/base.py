"""Base du système d'outils d'ARGOS.

La différence essentielle entre un chatbot et un agent (README §12) :

    un chatbot répond ;
    un agent peut faire.

Un outil est une capacité concrète qu'ARGOS peut exécuter :
lire un fichier, lancer une commande, chercher sur Internet...

Chaque outil déclare :

    - son nom et sa description ;
    - ses paramètres et ceux qui sont obligatoires ;
    - son niveau de permission de base.

Le niveau réellement appliqué est décidé par le registre, en
combinant le niveau déclaré et le risque mesuré. Un outil ne peut
donc pas se déclarer inoffensif si son action est dangereuse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from core.permissions import SAFE

# Longueur maximale d'une sortie renvoyée au modèle.
MAX_OUTPUT_CHARS = 8000


@dataclass
class ToolResult:
    """Résultat normalisé d'un outil."""

    ok: bool
    tool: str = ""
    output: str = ""
    error: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def as_text(self) -> str:
        """Rend le résultat lisible par un humain ou un modèle."""

        if not self.ok:
            return f"Echec de {self.tool} : {self.error}"

        if not self.output:
            return f"{self.tool} : terminé sans sortie."

        return self.output

    def clipped(self, limit: int = MAX_OUTPUT_CHARS) -> str:
        """Retourne le texte, tronqué s'il est trop long."""

        text = self.as_text()

        if len(text) <= limit:
            return text

        return (
            text[:limit]
            + f"\n... [sortie tronquée, {len(text)} caractères au total]"
        )

    def to_dict(self) -> Dict[str, Any]:

        return {
            "ok": self.ok,
            "tool": self.tool,
            "output": self.output,
            "error": self.error,
            "data": self.data,
        }


class Tool:
    """Capacité exécutable par ARGOS."""

    # Nom technique utilisé pour appeler l'outil.
    name = "tool"

    # Description destinée au modèle et à l'interface.
    description = ""

    # Niveau de permission minimal (voir core/permissions.py).
    level = SAFE

    # Paramètres attendus : nom -> description.
    parameters: Dict[str, str] = {}

    # Paramètres obligatoires.
    required: Tuple[str, ...] = ()

    # Indique si l'outil ne modifie rien (lecture seule).
    read_only = False

    # =========================================================
    # EVALUATION
    # =========================================================

    def assess_level(self, **kwargs: Any) -> int:
        """Retourne le niveau de risque de cet appel précis.

        Les outils qui touchent au système de fichiers ou au terminal
        redéfinissent cette méthode à partir de core.safety.
        """

        return self.level

    def target(self, **kwargs: Any) -> str:
        """Décrit la cible de l'action, pour le message de confirmation."""

        return ""

    # =========================================================
    # EXECUTION
    # =========================================================

    def run(self, **kwargs: Any) -> ToolResult:
        """Exécute l'outil. Chaque outil concret doit l'implémenter."""

        raise NotImplementedError(
            f"L'outil '{self.name}' doit implémenter run()."
        )

    # =========================================================
    # DESCRIPTION
    # =========================================================

    def usage(self) -> str:
        """Signature lisible de l'outil."""

        if not self.parameters:
            return f"{self.name}()"

        parts = []

        for key in self.parameters:
            if key in self.required:
                parts.append(key)

            else:
                parts.append(f"{key}?")

        return f"{self.name}({', '.join(parts)})"

    def spec(self) -> Dict[str, Any]:

        return {
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "read_only": self.read_only,
            "parameters": dict(self.parameters),
            "required": list(self.required),
            "usage": self.usage(),
        }


# =============================================================
# COERCITION DES ARGUMENTS
# =============================================================

# Un modèle de langage renvoie souvent des chaînes là où un outil
# attend un booléen ou un entier. Ces fonctions évitent les
# comparaisons silencieusement fausses.

_TRUE_VALUES = frozenset({"1", "true", "vrai", "oui", "yes", "y", "on"})
_FALSE_VALUES = frozenset({"0", "false", "faux", "non", "no", "n", "off", ""})


def as_bool(value: Any, default: bool = False) -> bool:
    """Convertit une valeur en booléen de façon explicite."""

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    text = str(value).strip().lower()

    if text in _TRUE_VALUES:
        return True

    if text in _FALSE_VALUES:
        return False

    return default


def as_int(value: Any, default: Optional[int] = None, minimum: Optional[int] = None) -> Optional[int]:
    """Convertit une valeur en entier, avec borne minimale optionnelle."""

    if value is None or value == "":
        result = default

    else:
        try:
            result = int(value)

        except (TypeError, ValueError):
            result = default

    if result is None:
        return None

    if minimum is not None and result < minimum:
        result = minimum

    return result


def as_text(value: Any, default: str = "") -> str:
    """Convertit une valeur en chaîne nettoyée."""

    if value is None:
        return default

    text = str(value).strip()

    return text or default
