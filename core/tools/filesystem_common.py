"""Helpers partagés par les outils de système de fichiers.

Ce module ne contient aucun outil : uniquement la résolution de
chemins, les conversions de taille et le parcours de dossiers,
afin que les outils de lecture et d'écriture restent courts et
cohérents.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from core.paths import PROJECT_ROOT
from core.tools.base import as_int, as_text

# Dossiers techniques ignorés lors des parcours.
SKIP_DIRECTORIES = frozenset({
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "build",
    "dist",
    ".tox",
})

# Taille maximale d'un fichier analysé par la recherche textuelle.
MAX_SEARCH_FILE_BYTES = 2 * 1024 * 1024

# Nombre d'octets examinés pour détecter un fichier binaire.
_BINARY_PROBE_BYTES = 8000


def resolve_path(raw: str = "", default: Optional[Path] = None) -> Path:
    """Convertit un chemin fourni par l'utilisateur en chemin absolu.

    Un chemin vide désigne la racine du projet ARGOS.
    """

    text = as_text(raw)

    if not text:
        return Path(default) if default is not None else PROJECT_ROOT

    try:
        return Path(text).expanduser().resolve()

    except (OSError, ValueError, RuntimeError) as error:
        raise ValueError(f"Chemin invalide : {text!r} ({error})") from error


def format_size(size) -> str:
    """Formate une taille en octets de façon lisible."""

    try:
        value = float(size)

    except (TypeError, ValueError):
        return "?"

    for unit in ("o", "Ko", "Mo", "Go", "To"):

        if value < 1024 or unit == "To":

            if unit == "o":
                return f"{value:.0f} {unit}"

            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} To"


def format_time(timestamp) -> str:
    """Formate une date de modification."""

    try:
        return datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M")

    except (OSError, OverflowError, TypeError, ValueError):
        return "?"


def is_probably_binary(path: Path, probe: int = _BINARY_PROBE_BYTES) -> bool:
    """Détecte un fichier binaire sans lire tout son contenu."""

    try:
        with open(path, "rb") as file:
            chunk = file.read(probe)

    except OSError:
        return True

    return b"\x00" in chunk


def read_text_lines(
    path: Path,
    start_line: int = 1,
    max_lines: int = 400,
) -> Tuple[List[str], int]:
    """Lit un intervalle de lignes d'un fichier texte.

    Retourne (lignes demandées, nombre total de lignes du fichier).
    """

    window_start = max(1, int(start_line))
    window_end = window_start + max(1, int(max_lines))

    selected: List[str] = []
    total = 0

    with open(path, "r", encoding="utf-8", errors="replace") as file:

        for index, line in enumerate(file, start=1):

            total = index

            if window_start <= index < window_end:
                selected.append(line.rstrip("\r\n"))

    return selected, total


def count_lines(path: Path) -> Optional[int]:
    """Compte les lignes d'un fichier texte, ou None si illisible."""

    if is_probably_binary(path):
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            return sum(1 for _ in file)

    except OSError:
        return None


def walk_files(
    directory: Path,
    recursive: bool = False,
    limit: Optional[int] = None,
) -> Iterator[Path]:
    """Parcourt les fichiers d'un dossier.

    Les dossiers techniques (.git, node_modules, __pycache__...)
    sont ignorés : ARGOS ne doit pas perdre de temps dans des
    dépendances.
    """

    count = 0

    if recursive:

        for root, directories, files in os.walk(
            directory,
            onerror=lambda _error: None,
        ):

            directories[:] = sorted(
                name for name in directories if name not in SKIP_DIRECTORIES
            )

            for name in sorted(files):

                count += 1

                if limit is not None and count > limit:
                    return

                yield Path(root) / name

        return

    try:
        entries = sorted(
            entry for entry in directory.iterdir() if entry.is_file()
        )

    except OSError:
        return

    for entry in entries:

        count += 1

        if limit is not None and count > limit:
            return

        yield entry


def clamp_int(value, default: int, minimum: int, maximum: int) -> int:
    """Borne une valeur entière demandée par le modèle."""

    result = as_int(value, default, minimum=minimum)

    if result is None:
        return default

    return min(result, maximum)
