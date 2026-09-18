"""Système de permissions d'ARGOS.

ARGOS ne dispose pas d'une autonomie illimitée (README §29).
Il agit seul dans un cadre autorisé et demande une confirmation
lorsqu'une action dépasse ce cadre.

Quatre niveaux (README §28) :

    Niveau 0 — Lecture
        lire un fichier, lire un dossier, rechercher, analyser

    Niveau 1 — Actions sûres
        créer un fichier, ouvrir un logiciel, lancer une commande

    Niveau 2 — Actions sensibles
        modifier des fichiers importants, installer un logiciel,
        modifier la configuration

    Niveau 3 — Actions critiques
        suppression massive, modification système,
        action administrateur

Politique appliquée par check() :

    1. une lecture est toujours permise ;
    2. une action déjà approuvée dans la session est permise ;
    3. une action dont le niveau atteint le seuil de confirmation
       exige une confirmation explicite ;
    4. une action au-dessus du niveau accordé est refusée ;
    5. sinon l'action est permise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from core.config import ArgosConfig
from core.safety import RISK_NONE

# =============================================================
# NIVEAUX
# =============================================================

READ = 0
SAFE = 1
SENSITIVE = 2
CRITICAL = 3

MAX_LEVEL = CRITICAL

LEVEL_LABELS: Dict[int, str] = {
    READ: "Lecture",
    SAFE: "Actions sûres",
    SENSITIVE: "Actions sensibles",
    CRITICAL: "Actions critiques",
}

LEVEL_DESCRIPTIONS: Dict[int, str] = {
    READ: "Lire un fichier ou un dossier, rechercher, analyser.",
    SAFE: "Créer un fichier, ouvrir un logiciel, lancer une commande.",
    SENSITIVE: (
        "Modifier des fichiers importants, installer un logiciel, "
        "modifier la configuration."
    ),
    CRITICAL: (
        "Suppression massive, modification système, "
        "action administrateur."
    ),
}

# Nombre de décisions conservées pour l'interface.
HISTORY_LIMIT = 200

ConfirmationHandler = Callable[["PermissionRequest"], bool]


def level_label(level: int) -> str:
    """Retourne le libellé français d'un niveau de permission."""

    return LEVEL_LABELS.get(level, f"Niveau {level}")


# =============================================================
# OBJETS
# =============================================================

@dataclass(frozen=True)
class PermissionRequest:
    """Action soumise au système de permissions."""

    action: str
    level: int
    target: str = ""
    description: str = ""

    @property
    def label(self) -> str:
        return level_label(self.level)

    def as_text(self) -> str:
        """Message présenté à l'utilisateur lors d'une confirmation."""

        lines = [
            f"Action : {self.action}",
            f"Niveau : {self.level} — {self.label}",
        ]

        if self.target:
            lines.append(f"Cible : {self.target}")

        if self.description:
            lines.append(f"Détail : {self.description}")

        return "\n".join(lines)


@dataclass
class PermissionDecision:
    """Résultat d'une vérification de permission."""

    request: PermissionRequest
    allowed: bool = False
    requires_confirmation: bool = False
    granted: bool = False
    reason: str = ""
    answers: List[str] = field(default_factory=list)

    @property
    def level(self) -> int:
        return self.request.level

    def as_dict(self) -> Dict[str, Any]:

        return {
            "action": self.request.action,
            "level": self.request.level,
            "target": self.request.target,
            "allowed": self.allowed,
            "requires_confirmation": self.requires_confirmation,
            "granted": self.granted,
            "reason": self.reason,
        }


class PermissionDenied(PermissionError):
    """Erreur levée lorsqu'une action n'est pas autorisée."""

    def __init__(self, decision: PermissionDecision):

        super().__init__(
            f"Action refusée : {decision.request.action} "
            f"({decision.reason})"
        )

        self.decision = decision


# =============================================================
# GESTIONNAIRE
# =============================================================

class PermissionManager:
    """Applique la politique de permissions d'ARGOS."""

    def __init__(self, config: Optional[ArgosConfig] = None):

        self.config = config or ArgosConfig()

        # Fonction fournie par l'interface pour demander confirmation.
        self._handler: Optional[ConfirmationHandler] = None

        # Actions approuvées pour la durée de la session.
        self._session_grants: set[str] = set()

        # Journal des décisions.
        self.history: List[PermissionDecision] = []

    # =========================================================
    # NIVEAU ACCORDE
    # =========================================================

    @property
    def granted_level(self) -> int:
        """Niveau maximum accordé à ARGOS."""

        try:
            level = int(self.config.get("permissions.level", SAFE))

        except (TypeError, ValueError):
            return SAFE

        return max(READ, min(MAX_LEVEL, level))

    @property
    def confirm_from(self) -> int:
        """Niveau à partir duquel ARGOS demande confirmation.

        Une valeur supérieure à 3 désactive toute confirmation :
        ARGOS agit alors seul jusqu'au niveau accordé.
        """

        try:
            threshold = int(self.config.get("permissions.confirm_from", SENSITIVE))

        except (TypeError, ValueError):
            return SENSITIVE

        return max(READ, threshold)

    def set_level(self, level: int) -> None:
        """Modifie le niveau accordé et l'enregistre."""

        if not isinstance(level, int) or not READ <= level <= MAX_LEVEL:
            raise ValueError(
                f"Niveau invalide : {level!r}. "
                f"Valeurs attendues : {READ} à {MAX_LEVEL}."
            )

        self.config.set("permissions.level", level)

    def set_confirm_from(self, level: int) -> None:

        if not isinstance(level, int) or level < READ:
            raise ValueError(f"Seuil invalide : {level!r}")

        self.config.set("permissions.confirm_from", level)

    # =========================================================
    # CONFIRMATION
    # =========================================================

    def set_confirmation_handler(self, handler: Optional[ConfirmationHandler]) -> None:
        """Installe la fonction chargée de demander confirmation.

        Sans fonction installée, ARGOS refuse par défaut tout ce qui
        dépasse son cadre autorisé : il ne décide jamais seul de
        franchir ses permissions.
        """

        if handler is not None and not callable(handler):
            raise TypeError("Le gestionnaire de confirmation doit être appelable.")

        self._handler = handler

    def has_confirmation_handler(self) -> bool:

        return self._handler is not None

    # =========================================================
    # AUTORISATIONS PONCTUELLES
    # =========================================================

    def grant(self, action: str) -> None:
        """Autorise une action pour le reste de la session."""

        if action:
            self._session_grants.add(str(action))

    def revoke(self, action: str) -> None:

        self._session_grants.discard(str(action))

    def granted_actions(self) -> List[str]:

        return sorted(self._session_grants)

    def clear_grants(self) -> None:

        self._session_grants.clear()

    # =========================================================
    # VERIFICATION
    # =========================================================

    def effective_level(self, base_level: int, assessed_level: int = RISK_NONE) -> int:
        """Combine le niveau déclaré par un outil et le risque mesuré.

        Le niveau le plus élevé des deux l'emporte : un outil ne peut
        pas se déclarer inoffensif si l'analyse de risque conclut
        l'inverse.
        """

        try:
            base = int(base_level)

        except (TypeError, ValueError):
            base = CRITICAL

        try:
            assessed = int(assessed_level)

        except (TypeError, ValueError):
            assessed = RISK_NONE

        return max(READ, base, assessed)

    def check(
        self,
        action: str,
        level: int = SAFE,
        target: str = "",
        description: str = "",
    ) -> PermissionDecision:
        """Evalue une action sans lever d'exception."""

        request = PermissionRequest(
            action=str(action),
            level=int(level),
            target=str(target or ""),
            description=str(description or ""),
        )

        decision = PermissionDecision(request=request)

        # 1. Une lecture est toujours permise.
        if request.level <= READ:
            decision.allowed = True
            decision.reason = "Niveau lecture autorisé."

            return decision

        # 2. Action déjà approuvée dans cette session.
        if request.action in self._session_grants:
            decision.allowed = True
            decision.reason = "Action déjà approuvée pour cette session."

            return decision

        # 3. Seuil de confirmation atteint.
        if request.level >= self.confirm_from:
            decision.requires_confirmation = True
            decision.reason = (
                f"Niveau {request.level} ({request.label}) : "
                "confirmation nécessaire."
            )

            return decision

        # 4. Au-dessus du niveau accordé.
        if request.level > self.granted_level:
            decision.reason = (
                f"Niveau {request.level} ({request.label}) supérieur "
                f"au niveau accordé ({self.granted_level})."
            )

            return decision

        # 5. Autorisé.
        decision.allowed = True
        decision.reason = (
            f"Niveau {request.level} ({request.label}) dans le cadre accordé."
        )

        return decision

    def is_allowed(
        self,
        action: str,
        level: int = SAFE,
        target: str = "",
    ) -> bool:
        """Version booléenne de check(), sans confirmation."""

        return self.check(action, level, target).allowed

    # =========================================================
    # APPLICATION
    # =========================================================

    def require(
        self,
        action: str,
        level: int = SAFE,
        target: str = "",
        description: str = "",
    ) -> PermissionDecision:
        """Autorise une action ou lève PermissionDenied.

        Demande confirmation à l'interface lorsque la politique
        l'exige.
        """

        decision = self.check(action, level, target, description)

        if decision.allowed:
            self._record(decision)

            return decision

        if not decision.requires_confirmation:
            self._record(decision)

            raise PermissionDenied(decision)

        # -----------------------------------------------------
        # Confirmation utilisateur
        # -----------------------------------------------------

        if self._handler is None:
            decision.reason = (
                "Confirmation impossible : aucune interface n'est "
                "connectée au système de permissions."
            )

            self._record(decision)

            raise PermissionDenied(decision)

        try:
            approved = bool(self._handler(decision.request))

        except Exception as error:
            decision.reason = f"Echec de la confirmation : {error}"

            self._record(decision)

            raise PermissionDenied(decision) from error

        if approved:
            decision.allowed = True
            decision.granted = True
            decision.reason = "Action approuvée par l'utilisateur."

            # Une action critique n'est jamais mémorisée : ARGOS doit
            # redemander confirmation à chaque nouvel appel.
            if decision.request.level < CRITICAL:
                self.grant(action)

        else:
            decision.reason = "Action refusée par l'utilisateur."

        self._record(decision)

        if not decision.allowed:
            raise PermissionDenied(decision)

        return decision

    def _record(self, decision: PermissionDecision) -> None:

        self.history.append(decision)

        if len(self.history) > HISTORY_LIMIT:
            del self.history[:-HISTORY_LIMIT]

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def pending_requests(self) -> List[PermissionRequest]:
        """Actions refusées faute de confirmation, pour l'interface."""

        return [
            decision.request
            for decision in self.history
            if decision.requires_confirmation and not decision.allowed
        ][-20:]

    def levels(self) -> List[Dict[str, Any]]:
        """Description des niveaux, destinée à l'interface."""

        return [
            {
                "level": level,
                "label": LEVEL_LABELS[level],
                "description": LEVEL_DESCRIPTIONS[level],
                "active": level == self.granted_level,
            }
            for level in range(READ, MAX_LEVEL + 1)
        ]

    def summary(self) -> Dict[str, Any]:

        return {
            "granted_level": self.granted_level,
            "granted_label": level_label(self.granted_level),
            "confirm_from": self.confirm_from,
            "confirmation_handler": self.has_confirmation_handler(),
            "session_grants": self.granted_actions(),
            "decisions": len(self.history),
        }
