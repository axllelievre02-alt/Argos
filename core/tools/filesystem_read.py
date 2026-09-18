"""Outils de lecture du système de fichiers.

Ces outils ne modifient jamais rien : ils sont donc de niveau 0
(lecture). Leur exécution reste soumise à l'analyse de risque de
core.safety, qui relève le niveau pour les zones système.

Outils fournis :

    list_files    lister un dossier
    read_file     lire un fichier texte
    search_files  rechercher un texte dans un projet
    file_info     analyser un fichier ou un dossier
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from core.permissions import READ
from core.safety import path_risk
from core.tools.base import Tool, ToolResult, as_bool
from core.tools.filesystem_common import (
    MAX_SEARCH_FILE_BYTES,
    clamp_int,
    count_lines,
    format_size,
    format_time,
    is_probably_binary,
    read_text_lines,
    resolve_path,
    walk_files,
)

MAX_ENTRIES = 300
MAX_SEARCH_RESULTS = 50
DEFAULT_READ_LINES = 400
MAX_READ_LINES = 4000


class ListFilesTool(Tool):
    """Liste les fichiers et dossiers d'un répertoire."""

    name = "list_files"
    description = "Lister les fichiers et dossiers d'un répertoire."
    level = READ
    read_only = True
    parameters = {
        "path": "Répertoire à lister (vide = racine du projet).",
        "recursive": "true pour descendre dans les sous-dossiers.",
        "max_entries": "Nombre maximum d'entrées affichées.",
    }
    required = ()

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=False).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", recursive=False, max_entries=None, **_kwargs) -> ToolResult:

        try:
            directory = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not directory.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Répertoire introuvable : {directory}",
            )

        if not directory.is_dir():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Ce n'est pas un répertoire : {directory}",
            )

        limit = clamp_int(max_entries, MAX_ENTRIES, 1, MAX_ENTRIES)

        deep = as_bool(recursive)

        try:
            entries = sorted(directory.iterdir()) if not deep else None

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Lecture impossible : {error}",
            )

        lines: List[str] = []

        count = 0

        if deep:

            files = walk_files(directory, recursive=True, limit=limit)

            for file_path in files:

                count += 1

                lines.append(
                    f"[fichier] {file_path.relative_to(directory)} "
                    f"({format_size(self._size(file_path))})"
                )

                if count >= limit:
                    break

            lines.insert(0, f"Dossier : {directory} (récursif)")

        else:

            for entry in entries or []:

                if count >= limit:
                    break

                count += 1

                lines.append(self._describe(entry, directory))

            lines.insert(0, f"Dossier : {directory}")

        if count >= limit:
            lines.append(f"... liste tronquée à {limit} entrées.")

        return ToolResult(
            ok=True,
            tool=self.name,
            output="\n".join(lines),
            data={
                "path": str(directory),
                "entries": count,
                "recursive": deep,
            },
        )

    @staticmethod
    def _size(path: Path) -> int:

        try:
            return path.stat().st_size

        except OSError:
            return 0

    @classmethod
    def _describe(cls, entry: Path, base: Path) -> str:

        try:
            name = entry.relative_to(base)

        except ValueError:
            name = entry.name

        if entry.is_dir():
            return f"[dossier] {name}/"

        return f"[fichier] {name} ({format_size(cls._size(entry))})"


class ReadFileTool(Tool):
    """Lit le contenu texte d'un fichier."""

    name = "read_file"
    description = "Lire le contenu texte d'un fichier, par lignes."
    level = READ
    read_only = True
    parameters = {
        "path": "Fichier à lire.",
        "start_line": "Première ligne à lire (1 par défaut).",
        "max_lines": "Nombre de lignes à lire.",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=False).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, path="", start_line=1, max_lines=None, **_kwargs) -> ToolResult:

        try:
            target = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not target.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Fichier introuvable : {target}",
            )

        if not target.is_file():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Ce n'est pas un fichier : {target}",
            )

        if is_probably_binary(target):
            return ToolResult(
                ok=False,
                tool=self.name,
                error=(
                    f"{target.name} semble être un fichier binaire "
                    "et ne peut pas être lu comme du texte."
                ),
            )

        first_line = clamp_int(start_line, 1, 1, 10 ** 7)

        window = clamp_int(
            max_lines, DEFAULT_READ_LINES, 1, MAX_READ_LINES
        )

        try:
            lines, total = read_text_lines(target, first_line, window)

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Lecture impossible : {error}",
            )

        if not lines:
            return ToolResult(
                ok=True,
                tool=self.name,
                output=(
                    f"{target} ne contient aucune ligne "
                    f"à partir de la ligne {first_line} "
                    f"(total : {total} lignes)."
                ),
                data={"path": str(target), "total_lines": total},
            )

        width = len(str(first_line + len(lines) - 1))

        rendered = [
            f"{first_line + offset:>{width}} | {line}"
            for offset, line in enumerate(lines)
        ]

        header = (
            f"Fichier : {target}\n"
            f"Lignes {first_line} à {first_line + len(lines) - 1} "
            f"sur {total} :\n"
        )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=header + "\n".join(rendered),
            data={
                "path": str(target),
                "start_line": first_line,
                "lines": len(lines),
                "total_lines": total,
            },
        )


class SearchFilesTool(Tool):
    """Recherche un texte dans les fichiers d'un projet."""

    name = "search_files"
    description = (
        "Rechercher un texte dans les fichiers d'un dossier "
        "(insensible à la casse)."
    )
    level = READ
    read_only = True
    parameters = {
        "query": "Texte recherché.",
        "path": "Dossier de recherche (vide = racine du projet).",
        "max_results": "Nombre maximum de résultats.",
    }
    required = ("query",)

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=False).level

    def target(self, path="", **_kwargs) -> str:

        return str(resolve_path(path))

    def run(self, query="", path="", max_results=None, **_kwargs) -> ToolResult:

        needle = str(query or "").strip()

        if not needle:
            return ToolResult(
                ok=False, tool=self.name, error="Recherche vide."
            )

        try:
            directory = resolve_path(path)

        except ValueError as error:
            return ToolResult(ok=False, tool=self.name, error=str(error))

        if not directory.exists():
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Dossier introuvable : {directory}",
            )

        limit = clamp_int(max_results, 20, 1, MAX_SEARCH_RESULTS)

        lowered = needle.lower()

        matches: List[str] = []

        scanned = 0

        for file_path in walk_files(directory, recursive=True):

            if len(matches) >= limit:
                break

            try:
                size = file_path.stat().st_size

            except OSError:
                continue

            if size == 0 or size > MAX_SEARCH_FILE_BYTES:
                continue

            if is_probably_binary(file_path):
                continue

            scanned += 1

            try:
                with open(
                    file_path, "r", encoding="utf-8", errors="replace"
                ) as file:

                    for number, line in enumerate(file, start=1):

                        if lowered in line.lower():

                            display = line.strip()[:200]

                            try:
                                shown = file_path.relative_to(directory)

                            except ValueError:
                                shown = file_path

                            matches.append(f"{shown}:{number}: {display}")

                            if len(matches) >= limit:
                                break

            except OSError:
                continue

        if not matches:
            return ToolResult(
                ok=True,
                tool=self.name,
                output=(
                    f"Aucune occurrence de {needle!r} "
                    f"dans {directory} ({scanned} fichiers analysés)."
                ),
                data={"matches": 0, "scanned": scanned},
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=(
                f"{len(matches)} occurrence(s) de {needle!r} "
                f"dans {directory} :\n" + "\n".join(matches)
            ),
            data={
                "matches": len(matches),
                "scanned": scanned,
                "truncated": len(matches) >= limit,
            },
        )


class FileInfoTool(Tool):
    """Analyse un fichier ou un dossier."""

    name = "file_info"
    description = "Donner la taille, le type et la date d'un fichier ou dossier."
    level = READ
    read_only = True
    parameters = {
        "path": "Fichier ou dossier à analyser.",
    }
    required = ("path",)

    def assess_level(self, path="", **_kwargs) -> int:

        return path_risk(resolve_path(path), write=False).level

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
            stat = target.stat()

        except OSError as error:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Analyse impossible : {error}",
            )

        lines = [
            f"Chemin : {target}",
            f"Type : {'dossier' if target.is_dir() else 'fichier'}",
            f"Extension : {target.suffix or '(aucune)'}",
            f"Taille : {format_size(stat.st_size)}",
            f"Modifié : {format_time(stat.st_mtime)}",
        ]

        if target.is_file():

            total_lines = count_lines(target)

            if total_lines is None:
                lines.append("Contenu : binaire ou illisible en texte.")

            else:
                lines.append(f"Lignes : {total_lines}")

        else:

            try:
                children = len(list(target.iterdir()))

            except OSError:
                children = 0

            lines.append(f"Entrées directes : {children}")

        return ToolResult(
            ok=True,
            tool=self.name,
            output="\n".join(lines),
            data={
                "path": str(target),
                "is_dir": target.is_dir(),
                "size": stat.st_size,
            },
        )


READ_TOOLS = (
    ListFilesTool(),
    ReadFileTool(),
    SearchFilesTool(),
    FileInfoTool(),
)
