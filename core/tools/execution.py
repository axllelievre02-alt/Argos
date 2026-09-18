"""Outils d'exécution : terminal et Python.

Ces deux outils permettent à ARGOS d'agir réellement sur la machine
(README §13 et §14). Ils sont donc les plus sensibles du système.

Deux protections se combinent :

    1. le niveau de base de l'outil ;
    2. l'analyse de risque de core.safety appliquée au texte
       réellement exécuté.

Une commande destructrice atteint donc toujours le niveau critique,
même si l'outil est appelé sans intention malveillante.

Les commandes sont lancées sans entrée standard : aucune ne peut
bloquer ARGOS en attendant une saisie.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from core.paths import PROJECT_ROOT
from core.permissions import SAFE, SENSITIVE
from core.safety import command_risk, path_risk
from core.tools.base import Tool, ToolResult
from core.tools.filesystem_common import clamp_int, resolve_path

DEFAULT_TIMEOUT = 60
MAX_TIMEOUT = 900

# Taille maximale d'une sortie renvoyée au modèle.
MAX_OUTPUT_CHARS = 6000


def _startup_flags() -> int:
    """Evite l'ouverture d'une fenêtre de console sous Windows."""

    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    return 0


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    """Tronque une sortie trop longue."""

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + f"\n... [sortie tronquée, {len(text)} caractères au total]"
    )


def _format_result(returncode: int, stdout: str, stderr: str) -> str:
    """Met en forme le résultat d'un processus."""

    parts = [f"Code de retour : {returncode}"]

    if stdout.strip():
        parts.append(f"--- sortie standard ---\n{stdout.strip()}")

    if stderr.strip():
        parts.append(f"--- erreurs ---\n{stderr.strip()}")

    if not stdout.strip() and not stderr.strip():
        parts.append("(aucune sortie)")

    return _truncate("\n\n".join(parts))


class RunCommandTool(Tool):
    """Exécute une commande dans le terminal du système."""

    name = "run_command"
    description = "Exécuter une commande système et récupérer sa sortie."
    level = SAFE
    parameters = {
        "command": "Commande à exécuter.",
        "cwd": "Répertoire d'exécution (vide = racine du projet).",
        "timeout": "Durée maximale en secondes.",
    }
    required = ("command",)

    def assess_level(self, command="", cwd="", **_kwargs) -> int:

        risk = command_risk(str(command or ""))

        level = max(risk.level, SAFE)

        if cwd:
            try:
                level = max(
                    level,
                    path_risk(resolve_path(cwd), write=True).level,
                )

            except ValueError:
                level = max(level, SENSITIVE)

        return level

    def target(self, command="", cwd="", **_kwargs) -> str:

        workdir = str(resolve_path(cwd)) if cwd else str(PROJECT_ROOT)

        return f"{command} (dans {workdir})"

    def run(self, command="", cwd="", timeout=None, **_kwargs) -> ToolResult:

        text = str(command or "").strip()

        if not text:
            return ToolResult(
                ok=False, tool=self.name, error="Commande vide."
            )

        try:
            workdir = resolve_path(cwd) if str(cwd or "").strip() else PROJECT_ROOT

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not workdir.is_dir():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Répertoire de travail introuvable : {workdir}",
            )

        limit = clamp_int(timeout, DEFAULT_TIMEOUT, 1, MAX_TIMEOUT)

        try:
            completed = subprocess.run(
                text,
                shell=True,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=limit,
                stdin=subprocess.DEVNULL,
                creationflags=_startup_flags(),
            )

        except subprocess.TimeoutExpired:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Commande interrompue après {limit} secondes.",
                data={"command": text, "timeout": limit},
            )

        except OSError as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Lancement impossible : {error}",
            )

        return ToolResult(
            ok=completed.returncode == 0,
            tool=self.name,
            output=(
                f"Commande : {text}\n"
                f"Répertoire : {workdir}\n\n"
                f"{_format_result(completed.returncode, completed.stdout or '', completed.stderr or '')}"
            ),
            error=(
                ""
                if completed.returncode == 0
                else f"Code de retour {completed.returncode}."
            ),
            data={
                "command": text,
                "returncode": completed.returncode,
                "cwd": str(workdir),
            },
        )


class RunPythonTool(Tool):
    """Exécute un script Python."""

    name = "run_python"
    description = (
        "Exécuter du code Python et récupérer sa sortie. "
        "Le script est lancé depuis la racine du projet, "
        "ce qui permet d'importer les modules d'ARGOS."
    )
    level = SENSITIVE
    parameters = {
        "code": "Code Python à exécuter.",
        "timeout": "Durée maximale en secondes.",
    }
    required = ("code",)

    def assess_level(self, code="", **_kwargs) -> int:

        risk = command_risk(str(code or ""))

        return max(SENSITIVE, risk.level)

    def target(self, code="", **_kwargs) -> str:

        preview = " ".join(str(code or "").split())[:120]

        return f"python : {preview}"

    def run(self, code="", timeout=None, **_kwargs) -> ToolResult:

        source = str(code or "")

        if not source.strip():
            return ToolResult(
                ok=False, tool=self.name, error="Code Python vide."
            )

        limit = clamp_int(timeout, DEFAULT_TIMEOUT, 1, MAX_TIMEOUT)

        # Le fichier temporaire est créé dans la racine du projet afin
        # que le script puisse importer les modules d'ARGOS.
        handle, script_path = tempfile.mkstemp(
            prefix="argos_run_",
            suffix=".py",
            dir=str(PROJECT_ROOT),
        )

        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as file:
                file.write(source)

            completed = subprocess.run(
                [sys.executable, script_path],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=limit,
                stdin=subprocess.DEVNULL,
                creationflags=_startup_flags(),
            )

        except subprocess.TimeoutExpired:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Script interrompu après {limit} secondes.",
            )

        except OSError as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Exécution impossible : {error}",
            )

        finally:

            try:
                Path(script_path).unlink(missing_ok=True)

            except OSError:
                pass

        return ToolResult(
            ok=completed.returncode == 0,
            tool=self.name,
            output=(
                "Script Python exécuté.\n\n"
                f"{_format_result(completed.returncode, completed.stdout or '', completed.stderr or '')}"
            ),
            error=(
                ""
                if completed.returncode == 0
                else f"Code de retour {completed.returncode}."
            ),
            data={"returncode": completed.returncode},
        )


EXECUTION_TOOLS = (
    RunCommandTool(),
    RunPythonTool(),
)
