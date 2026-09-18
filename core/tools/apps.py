"""Outils d'interaction avec les applications du PC.

Ces outils répondent à un usage concret du README §13 :

    « ARGOS, ouvre VS Code. »
    « Lance mon projet. »

Ouvrir un document avec son application par défaut est une action
sûre. Lancer un programme ou un script exécutable est traité plus
prudemment : un fichier exécutable arbitraire ne doit pas être
lancé sans que l'utilisateur l'ait autorisé.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from core.permissions import SAFE, SENSITIVE
from core.safety import command_risk, path_risk
from core.tools.base import Tool, ToolResult
from core.tools.filesystem_common import resolve_path

# Extensions considérées comme exécutables.
EXECUTABLE_SUFFIXES = frozenset({
    ".exe",
    ".com",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".jse",
    ".wsf",
    ".msi",
    ".scr",
    ".jar",
    ".reg",
    ".lnk",
    ".sh",
    ".py",
})


def _detached_flags() -> int:
    """Détache l'application lancée de la console d'ARGOS."""

    if os.name != "nt":
        return 0

    flags = 0

    for attribute in ("CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS"):
        flags |= getattr(subprocess, attribute, 0)

    return flags


def _open_with_system(path: Path) -> None:
    """Ouvre un chemin avec l'application associée du système."""

    if os.name == "nt":
        os.startfile(str(path))
        return

    opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"

    subprocess.Popen(
        [opener, str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


class OpenPathTool(Tool):
    """Ouvre un fichier ou un dossier avec l'application par défaut."""

    name = "open_path"
    description = (
        "Ouvrir un fichier ou un dossier avec l'application "
        "associée du système."
    )
    level = SAFE
    parameters = {
        "path": "Fichier ou dossier à ouvrir.",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        target = resolve_path(path)

        level = SAFE

        if target.is_file() and target.suffix.lower() in EXECUTABLE_SUFFIXES:
            level = SENSITIVE

        return max(level, path_risk(target, write=False).level)

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not target.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Chemin introuvable : {target}",
            )

        try:
            _open_with_system(target)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Ouverture impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=f"{target} ouvert avec l'application par défaut.",
            data={"path": str(target)},
        )


class OpenApplicationTool(Tool):
    """Lance une application installée sur la machine."""

    name = "open_application"
    description = "Lancer une application ou un programme installé."
    level = SAFE
    parameters = {
        "application": "Nom ou chemin du programme à lancer.",
        "arguments": "Arguments éventuels, séparés par des espaces.",
        "cwd": "Répertoire de travail (facultatif).",
    }
    required = ("application",)

    def assess_level(self, application="", arguments="", cwd="", **_kwargs) -> int:

        full_command = f"{application} {arguments or ''}".strip()

        level = max(command_risk(full_command).level, SAFE)

        if cwd:
            try:
                level = max(
                    level,
                    path_risk(resolve_path(cwd), write=False).level,
                )

            except ValueError:
                level = max(level, SENSITIVE)

        return level

    def target(self, application="", arguments="", **_kwargs) -> str:

        return f"{application} {arguments or ''}".strip()

    def run(
        self,
        application="",
        arguments="",
        cwd="",
        **_kwargs
    ) -> ToolResult:

        name = str(application or "").strip()

        if not name:
            return ToolResult(
                ok=False, tool=self.name, error="Aucune application indiquée."
            )

        workdir = None

        if str(cwd or "").strip():

            try:
                candidate = resolve_path(cwd)

            except ValueError as error:
                return ToolResult(ok=False, tool=self.name, error=str(error))

            if not candidate.is_dir():
                return ToolResult(
                    ok=False,
                    tool=self.name,
                    error=f"Répertoire introuvable : {candidate}",
                )

            workdir = str(candidate)

        command = [name]

        if str(arguments or "").strip():
            command.extend(
                shlex.split(str(arguments), posix=(os.name != "nt"))
            )

        try:
            process = subprocess.Popen(
                command,
                cwd=workdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=_detached_flags(),
            )

        except (OSError, ValueError) as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Lancement impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=(
                f"Application lancée : {' '.join(command)} "
                f"(pid {process.pid})."
            ),
            data={"application": name, "pid": process.pid},
        )


APP_TOOLS = (
    OpenPathTool(),
    OpenApplicationTool(),
)
