"""Outils de modification du système de fichiers.

Ces outils modifient réellement la machine. Leur niveau de base est
donc au minimum « actions sûres », et l'analyse de risque le relève
automatiquement :

    - écriture dans le projet          -> niveau 1
    - écriture hors du projet          -> niveau 2
    - écriture dans une zone système   -> niveau 3

Supprimer un dossier non vide est toujours traité comme critique :
c'est une action irréversible.
"""

from __future__ import annotations

import shutil

from core.permissions import CRITICAL, SAFE, SENSITIVE
from core.safety import RISK_NONE, path_risk
from core.tools.base import Tool, ToolResult, as_bool
from core.tools.filesystem_common import format_size, resolve_path


class WriteFileTool(Tool):
    """Ecrit (ou remplace) le contenu complet d'un fichier."""

    name = "write_file"
    description = (
        "Ecrire le contenu complet d'un fichier "
        "(remplace le contenu existant)."
    )
    level = SAFE
    parameters = {
        "path": "Fichier à écrire.",
        "content": "Contenu texte complet du fichier.",
    }
    required = ("path", "content")

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=True).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", content="", **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if target.exists() and target.is_dir():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Le chemin est un dossier : {target}",
            )

        existed = target.exists()

        previous_size = 0

        if existed:
            try:
                previous_size = target.stat().st_size

            except OSError:
                previous_size = 0

        text = "" if content is None else str(content)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(target, "w", encoding="utf-8", newline="\n") as file:
                file.write(text)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Ecriture impossible : {error}",
            )

        action = "remplacé" if existed else "créé"

        return ToolResult(
            ok=True,
            tool=self.name,
            output=(
                f"{target} {action} : {len(text)} caractères, "
                f"{format_size(target.stat().st_size)}"
                + (
                    f" (taille précédente : {format_size(previous_size)})"
                    if existed
                    else ""
                )
            ),
            data={
                "path": str(target),
                "created": not existed,
                "characters": len(text),
            },
        )


class CreateFileTool(Tool):
    """Crée un fichier neuf, sans écraser un fichier existant."""

    name = "create_file"
    description = "Créer un nouveau fichier, sans écraser un fichier existant."
    level = SAFE
    parameters = {
        "path": "Fichier à créer.",
        "content": "Contenu initial (facultatif).",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=True).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", content="", **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if target.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=(
                    f"{target} existe déjà. "
                    "Utilise write_file pour le modifier."
                ),
            )

        text = "" if content is None else str(content)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(target, "w", encoding="utf-8", newline="\n") as file:
                file.write(text)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Création impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=f"{target} créé ({len(text)} caractères).",
            data={"path": str(target), "created": True},
        )


class AppendFileTool(Tool):
    """Ajoute du texte à la fin d'un fichier."""

    name = "append_file"
    description = "Ajouter du texte à la fin d'un fichier."
    level = SAFE
    parameters = {
        "path": "Fichier à compléter.",
        "content": "Texte à ajouter.",
    }
    required = ("path", "content")

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=True).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", content="", **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if target.exists() and target.is_dir():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Le chemin est un dossier : {target}",
            )

        text = "" if content is None else str(content)

        if not text:
            return ToolResult(
                ok=False, tool=self.name, error="Rien à ajouter."
            )

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            with open(target, "a", encoding="utf-8", newline="\n") as file:
                file.write(text)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Ecriture impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=(
                f"{len(text)} caractères ajoutés à {target} "
                f"(taille : {format_size(target.stat().st_size)})."
            ),
            data={"path": str(target), "appended": len(text)},
        )


class MakeDirectoryTool(Tool):
    """Crée un dossier."""

    name = "make_directory"
    description = "Créer un dossier (avec ses parents si nécessaire)."
    level = SAFE
    parameters = {
        "path": "Dossier à créer.",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=True).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if target.exists():
            if target.is_dir():
                return ToolResult(
                    ok=True,
                    tool=self.name,
                    output=f"{target} existe déjà.",
                    data={"path": str(target), "created": False},
                )

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Un fichier porte déjà ce nom : {target}",
            )

        try:
            target.mkdir(parents=True, exist_ok=True)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Création impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=f"{target} créé.",
            data={"path": str(target), "created": True},
        )


class DeleteFileTool(Tool):
    """Supprime un fichier ou un dossier.

    Un dossier non vide est traité comme une action critique :
    la suppression est irréversible.
    """

    name = "delete_file"
    description = "Supprimer un fichier ou un dossier."
    level = SENSITIVE
    parameters = {
        "path": "Fichier ou dossier à supprimer.",
        "recursive": "true pour supprimer un dossier non vide.",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        target = resolve_path(path)

        assessed = path_risk(target, write=True).level

        if assessed == RISK_NONE:
            assessed = SENSITIVE

        try:
            if target.is_dir() and any(target.iterdir()):
                return CRITICAL

        except OSError:
            return CRITICAL

        return max(assessed, SENSITIVE)

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", recursive=False, **_kwargs) -> ToolResult:

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
            if target.is_dir():

                children = list(target.iterdir())

                if children and not as_bool(recursive):

                    return ToolResult(
                        ok=False,
                        tool=self.name,
                        error=(
                            f"{target} n'est pas vide. "
                            "Relance avec recursive=true pour confirmer."
                        ),
                    )

                count = sum(1 for _ in target.rglob("*")) + 1

                shutil.rmtree(target)

                return ToolResult(
                    ok=True,
                    tool=self.name,
                    output=f"Dossier {target} supprimé ({count} entrées).",
                    data={"path": str(target), "removed": count},
                )

            size = target.stat().st_size

            target.unlink()

            return ToolResult(
                ok=True,
                tool=self.name,
                output=(
                    f"Fichier {target} supprimé ({format_size(size)})."
                ),
                data={"path": str(target), "removed": 1},
            )

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Suppression impossible : {error}",
            )


class MoveFileTool(Tool):
    """Déplace ou renomme un fichier."""

    name = "move_file"
    description = "Déplacer ou renommer un fichier ou un dossier."
    level = SENSITIVE
    parameters = {
        "source": "Chemin d'origine.",
        "destination": "Chemin de destination.",
        "overwrite": "true pour écraser la destination existante.",
    }
    required = ("source", "destination")

    def assess_level(self, source="", destination="", **_kwargs) -> int:

        source_risk = path_risk(resolve_path(source), write=True).level
        destination_risk = path_risk(
            resolve_path(destination), write=True
        ).level

        return max(source_risk, destination_risk, SENSITIVE)

    def target(self, source="", destination="", **_kwargs) -> str:

        return f"{resolve_path(source)} -> {resolve_path(destination)}"

    def run(
        self,
        source="",
        destination="",
        overwrite=False,
        **_kwargs
    ) -> ToolResult:

        try:
            origin = resolve_path(source)
            destination_path = resolve_path(destination)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not origin.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Source introuvable : {origin}",
            )

        if destination_path.exists() and not as_bool(overwrite):

            return ToolResult(
                ok=False,
                tool=self.name,
                error=(
                    f"{destination_path} existe déjà. "
                    "Relance avec overwrite=true pour confirmer."
                ),
            )

        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            if destination_path.exists():

                if destination_path.is_dir():
                    shutil.rmtree(destination_path)
                else:
                    destination_path.unlink()

            shutil.move(str(origin), str(destination_path))

        except (OSError, shutil.Error) as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Déplacement impossible : {error}",
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=f"{origin} déplacé vers {destination_path}.",
            data={
                "source": str(origin),
                "destination": str(destination_path),
            },
        )


WRITE_TOOLS = (
    WriteFileTool(),
    CreateFileTool(),
    AppendFileTool(),
    MakeDirectoryTool(),
    DeleteFileTool(),
    MoveFileTool(),
)
