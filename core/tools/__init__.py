"""Système d'outils d'ARGOS.

Un chatbot répond. Un agent peut faire (README §12).

Ce paquet rassemble toutes les capacités exécutables d'ARGOS :

    filesystem_read   lire, lister, chercher, analyser
    filesystem_write  écrire, créer, compléter, déplacer, supprimer
    execution         lancer une commande ou un script Python
    web               chercher sur Internet, lire une page
    apps              ouvrir un fichier ou lancer un programme

Aucun outil ne s'exécute sans passer par ToolRegistry, et donc
sans passer par le système de permissions.
"""

from core.permissions import PermissionManager
from core.tools.apps import APP_TOOLS
from core.tools.base import MAX_OUTPUT_CHARS, Tool, ToolResult
from core.tools.execution import EXECUTION_TOOLS
from core.tools.filesystem_read import READ_TOOLS
from core.tools.filesystem_write import WRITE_TOOLS
from core.tools.registry import ToolRegistry
from core.tools.web import WEB_TOOLS

# Tous les outils d'ARGOS, dans l'ordre de leur sensibilité.
ALL_TOOLS = (
    READ_TOOLS
    + WRITE_TOOLS
    + EXECUTION_TOOLS
    + WEB_TOOLS
    + APP_TOOLS
)


def build_default_registry(
    permissions: PermissionManager = None,
) -> ToolRegistry:
    """Construit le registre complet d'ARGOS."""

    registry = ToolRegistry(permissions)

    registry.register_all(ALL_TOOLS)

    return registry


__all__ = [
    "ALL_TOOLS",
    "MAX_OUTPUT_CHARS",
    "Tool",
    "ToolRegistry",
    "ToolResult",
    "build_default_registry",
]
