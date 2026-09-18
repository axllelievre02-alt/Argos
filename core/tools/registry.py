"""Registre des outils d'ARGOS.

Le registre est le seul point d'entrée pour exécuter un outil.
Il garantit qu'aucune action ne contourne le système de permissions
(README §28 et §29) :

    executer()
        ↓
    outil trouvé ?
        ↓
    paramètres obligatoires ?
        ↓
    niveau de risque évalué
        ↓
    PermissionManager.require()
        ↓
    outil exécuté
        ↓
    résultat enregistré
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.permissions import (
    CRITICAL,
    PermissionDecision,
    PermissionDenied,
    PermissionManager,
    level_label,
)
from core.tools.base import Tool, ToolResult

# Nombre de résultats conservés pour l'interface.
HISTORY_LIMIT = 200


class ToolRegistry:
    """Catalogue des capacités exécutables d'ARGOS."""

    def __init__(self, permissions: Optional[PermissionManager] = None):

        self.permissions = permissions or PermissionManager()

        self._tools: Dict[str, Tool] = {}

        self.history: List[ToolResult] = []

    # =========================================================
    # GESTION DU CATALOGUE
    # =========================================================

    def register(self, tool: Tool) -> None:

        if not isinstance(tool, Tool):
            raise TypeError("Un outil doit hériter de Tool.")

        self._tools[tool.name] = tool

    def register_all(self, tools) -> None:

        for tool in tools:
            self.register(tool)

    def unregister(self, name: str) -> None:

        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:

        return self._tools.get(name)

    def exists(self, name: str) -> bool:

        return name in self._tools

    def names(self) -> List[str]:

        return sorted(self._tools)

    def all(self) -> List[Tool]:

        return [self._tools[name] for name in self.names()]

    def specs(self) -> List[Dict[str, Any]]:

        return [tool.spec() for tool in self.all()]

    # =========================================================
    # DESCRIPTION POUR LE MODELE
    # =========================================================

    def describe(self) -> str:
        """Liste des outils utilisable dans un prompt système."""

        if not self._tools:
            return "Aucun outil disponible."

        lines = []

        for tool in self.all():
            lines.append(
                f"- {tool.usage()} "
                f"[niveau {tool.level} — {level_label(tool.level)}] : "
                f"{tool.description}"
            )

        return "\n".join(lines)

    # =========================================================
    # PARAMETRES
    # =========================================================

    @staticmethod
    def select_parameters(tool: Tool, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Ne conserve que les paramètres déclarés par l'outil.

        Un paramètre inconnu est ignoré plutôt que transmis : cela
        évite qu'un appel malformé fasse échouer l'outil avec une
        TypeError obscure.
        """

        if not tool.parameters:
            return {}

        return {
            key: kwargs[key]
            for key in tool.parameters
            if key in kwargs
        }

    @staticmethod
    def missing_parameters(tool: Tool, kwargs: Dict[str, Any]) -> List[str]:
        """Retourne les paramètres obligatoires manquants."""

        missing = []

        for key in tool.required:

            value = kwargs.get(key)

            if value is None:
                missing.append(key)
                continue

            if isinstance(value, str) and not value.strip():
                missing.append(key)

        return missing

    # =========================================================
    # EVALUATION
    # =========================================================

    def effective_level(self, tool: Tool, kwargs: Dict[str, Any]) -> int:
        """Niveau réellement appliqué à un appel d'outil."""

        try:
            assessed = tool.assess_level(**kwargs)

        except Exception:
            # Une évaluation impossible est traitée comme critique :
            # en cas de doute, ARGOS demande l'autorisation.
            assessed = CRITICAL

        if assessed is None:
            assessed = CRITICAL

        return self.permissions.effective_level(tool.level, assessed)

    def action_name(self, tool: Tool, level: int) -> str:
        """Identifie une action pour la mémoire des autorisations.

        Le niveau fait partie du nom : approuver une modification de
        niveau 2 n'autorise jamais une suppression de niveau 3.
        """

        return f"{tool.name}:{level}"

    def target_of(self, tool: Tool, kwargs: Dict[str, Any]) -> str:

        try:
            return str(tool.target(**kwargs) or "")

        except Exception:
            return ""

    def check(self, name: str, **kwargs: Any) -> Optional[PermissionDecision]:
        """Evalue un appel d'outil sans l'exécuter.

        Retourne None si l'outil n'existe pas.
        """

        tool = self.get(name)

        if tool is None:
            return None

        selected = self.select_parameters(tool, kwargs)

        level = self.effective_level(tool, selected)

        return self.permissions.check(
            self.action_name(tool, level),
            level,
            target=self.target_of(tool, selected),
            description=tool.description,
        )

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Exécute un outil après vérification des permissions."""

        tool = self.get(name)

        if tool is None:
            return ToolResult(
                ok=False,
                tool=str(name),
                error=(
                    f"Outil inconnu : {name}. "
                    f"Outils disponibles : {', '.join(self.names()) or 'aucun'}."
                ),
            )

        selected = self.select_parameters(tool, kwargs)

        missing = self.missing_parameters(tool, selected)

        if missing:
            return ToolResult(
                ok=False,
                tool=tool.name,
                error=(
                    "Paramètre(s) obligatoire(s) manquant(s) : "
                    + ", ".join(missing)
                ),
            )

        level = self.effective_level(tool, selected)

        try:
            self.permissions.require(
                self.action_name(tool, level),
                level,
                target=self.target_of(tool, selected),
                description=tool.description,
            )

        except PermissionDenied as denied:
            result = ToolResult(
                ok=False,
                tool=tool.name,
                error=denied.decision.reason,
                data={
                    "denied": True,
                    "level": denied.decision.level,
                    "target": denied.decision.request.target,
                },
            )

            self._record(result)

            return result

        try:
            result = tool.run(**selected)

        except Exception as error:
            result = ToolResult(
                ok=False,
                tool=tool.name,
                error=f"{type(error).__name__} : {error}",
            )

        if not isinstance(result, ToolResult):
            result = ToolResult(
                ok=True,
                tool=tool.name,
                output=str(result),
            )

        self._record(result)

        return result

    def _record(self, result: ToolResult) -> None:

        self.history.append(result)

        if len(self.history) > HISTORY_LIMIT:
            del self.history[:-HISTORY_LIMIT]

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def summary(self) -> Dict[str, Any]:

        return {
            "tools": self.names(),
            "count": len(self._tools),
            "permissions": self.permissions.summary(),
        }
