"""Analyse de risque des actions d'ARGOS.

Ce module répond à une contrainte explicite du projet (README §28) :

    ARGOS ne doit pas pouvoir faire quelque chose qui pourrait
    détruire le PC.

Il ne décide pas si une action est autorisée : cette décision
appartient à PermissionManager. Il se contente d'évaluer le
niveau de risque d'une commande ou d'un chemin.

Limite importante : cette analyse est un filet de sécurité,
pas une garantie absolue. Aucun filtre textuel ne remplace un
niveau de permission prudent.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import NamedTuple

from core.paths import PROJECT_ROOT

# Niveaux de risque (voir core/permissions.py).
RISK_NONE = 0
RISK_SAFE = 1
RISK_SENSITIVE = 2
RISK_CRITICAL = 3


class Risk(NamedTuple):
    """Résultat d'une analyse de risque."""

    level: int
    reason: str

    @property
    def is_dangerous(self) -> bool:
        return self.level >= RISK_CRITICAL


SAFE_RISK = Risk(RISK_NONE, "")


# =============================================================
# COMMANDES
# =============================================================

# Commandes capables de détruire des données ou le système.
CRITICAL_COMMAND_PATTERNS = (
    r"\bformat\s+[a-z]:",
    r"\bdiskpart\b",
    r"\bmkfs(\.\w+)?\b",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\bstop-computer\b",
    r"\brestart-computer\b",
    r"\bbcdedit\b",
    r"\bvssadmin\s+delete",
    r"\bwbadmin\s+delete",
    r"\bcipher\s+/w",
    r"\breg\s+delete\b",
    r"\brm\s+-rf?\s+/",
    r"\brd\s+/s\s+/q\s+[a-z]:\\?$",
    r"\brmdir\s+/s\s+/q\s+[a-z]:\\?$",
    r"\bdel\s+/[fsq]+\s+[a-z]:\\",
    r"\bremove-item\b[^\n]*-recurse[^\n]*-force[^\n]*[a-z]:\\?$",
    r"\bsc\s+delete\b",
    r"\bnet\s+user\s+\S+\s+/delete",
    r"\bschtasks\s+/delete",
    r"\btakeown\b",
    r"\bicacls\b[^\n]*/grant",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-z]*f",
    r"\bmklink\b",
    r"\bsubst\b",
    r"\bfsutil\b",
)

# Commandes qui modifient l'environnement de façon significative.
SENSITIVE_COMMAND_PATTERNS = (
    r"\bpip\s+(install|uninstall)\b",
    r"\bpython\s+-m\s+pip\s+(install|uninstall)\b",
    r"\bnpm\s+(install|uninstall|i)\b",
    r"\bwinget\s+(install|uninstall|upgrade)\b",
    r"\bchoco\s+(install|uninstall)\b",
    r"\bscoop\s+(install|uninstall)\b",
    r"\breg\s+add\b",
    r"\bnetsh\b",
    r"\btaskkill\b",
    r"\bnet\s+start\b",
    r"\bnet\s+stop\b",
    r"\bsetx\b",
    r"\bgit\s+push\b",
    r"\bgit\s+branch\s+-[dD]\b",
    r"\bmove-item\b",
    r"\bremove-item\b",
    r"\bdel\b",
    r"\brm\b",
    r"\bschtasks\s+/create",
)

_CRITICAL_COMMAND = tuple(
    re.compile(pattern, re.IGNORECASE) for pattern in CRITICAL_COMMAND_PATTERNS
)
_SENSITIVE_COMMAND = tuple(
    re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_COMMAND_PATTERNS
)


def command_risk(command: str) -> Risk:
    """Evalue le risque d'une commande destinée au terminal."""

    if not isinstance(command, str) or not command.strip():
        return SAFE_RISK

    text = command.strip()

    for pattern in _CRITICAL_COMMAND:
        if pattern.search(text):
            return Risk(
                RISK_CRITICAL,
                "Commande jugée destructrice ou touchant au système.",
            )

    for pattern in _SENSITIVE_COMMAND:
        if pattern.search(text):
            return Risk(
                RISK_SENSITIVE,
                "Commande modifiant la machine, les paquets ou des fichiers.",
            )

    return SAFE_RISK


# =============================================================
# CHEMINS
# =============================================================

def _protected_roots():
    """Retourne les dossiers système à considérer comme intouchables."""

    roots = set()

    variables = (
        "SystemRoot",
        "windir",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "ProgramData",
        "ProgramW6432",
    )

    for variable in variables:
        value = os.environ.get(variable)

        if value:
            roots.add(Path(value))

    # Sous Windows uniquement : dossiers système classiques.
    for fallback in ("C:/Windows", "C:/Program Files", "C:/Program Files (x86)"):
        candidate = Path(fallback)

        if candidate.exists():
            roots.add(candidate)

    return tuple(sorted(roots))


_PROTECTED_ROOTS = _protected_roots()


def _is_drive_root(path: Path) -> bool:
    """Indique si le chemin est la racine d'un disque."""

    return path.parent == path


def is_protected_path(path) -> bool:
    """Indique si un chemin appartient au système d'exploitation."""

    try:
        resolved = Path(path).expanduser().resolve()
    except (OSError, ValueError, RuntimeError):
        return False

    if _is_drive_root(resolved):
        return True

    for root in _PROTECTED_ROOTS:
        try:
            resolved.relative_to(root)
        except (ValueError, OSError):
            continue

        return True

    return False


def path_risk(path, write: bool = False) -> Risk:
    """Evalue le risque d'un accès au système de fichiers.

    Args:
        path: chemin visé.
        write: True si l'opération modifie ou supprime.
    """

    try:
        resolved = Path(path).expanduser().resolve()
    except (OSError, ValueError, RuntimeError) as error:
        return Risk(RISK_SENSITIVE, f"Chemin non résolvable : {error}")

    if is_protected_path(resolved):

        if write:
            return Risk(
                RISK_CRITICAL,
                f"Ecriture dans une zone système protégée : {resolved}",
            )

        return Risk(
            RISK_SENSITIVE,
            f"Lecture dans une zone système protégée : {resolved}",
        )

    if not write:
        return SAFE_RISK

    try:
        resolved.relative_to(PROJECT_ROOT)

    except ValueError:
        return Risk(
            RISK_SENSITIVE,
            f"Ecriture en dehors du projet ARGOS : {resolved}",
        )

    return Risk(RISK_SAFE, "")
