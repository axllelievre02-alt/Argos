"""Persistance JSON commune aux mémoires d'ARGOS.

Toutes les mémoires avancées (faits persistants, connaissances
apprises, expériences, procédures) partagent la même mécanique :

    - lecture tolérante aux fichiers absents ou corrompus ;
    - écriture atomique, pour ne jamais laisser un fichier à moitié
      écrit si le processus est interrompu.

Les données restent locales (README §41) : aucun envoi vers un
service externe.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_json(path, default: Any = None) -> Any:
    """Lit un fichier JSON, ou retourne la valeur par défaut."""

    file_path = Path(path)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default

    return data if data is not None else default


def write_json(path, data: Any) -> None:
    """Ecrit un fichier JSON de façon atomique."""

    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    temporary = file_path.with_suffix(file_path.suffix + ".tmp")

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary.replace(file_path)


def read_jsonl(path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Lit un fichier JSON Lines.

    Une ligne corrompue est ignorée plutôt que de faire échouer
    tout le chargement.
    """

    file_path = Path(path)

    if not file_path.exists():
        return []

    records: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)

                except json.JSONDecodeError:
                    continue

                if isinstance(record, dict):
                    records.append(record)

    except OSError:
        return []

    if limit is not None and limit > 0:
        return records[-limit:]

    return records


def append_jsonl(path, record: Dict[str, Any]) -> None:
    """Ajoute une ligne à un fichier JSON Lines."""

    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def rewrite_jsonl(path, records: List[Dict[str, Any]]) -> None:
    """Réécrit entièrement un fichier JSON Lines."""

    file_path = Path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    temporary = file_path.with_suffix(file_path.suffix + ".tmp")

    with open(temporary, "w", encoding="utf-8") as file:

        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    temporary.replace(file_path)
