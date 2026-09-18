"""Mémoire des procédures d'ARGOS.

Le README §11 décrit un objectif précis :

    Objectif
      ↓
    Étape 1
      ↓
    Étape 2
      ↓
    Vérification
      ↓
    Résultat

Puis, plus tard :

    « ARGOS, refais ce que je t'avais montré. »

Ce module conserve donc des procédures nommées : une suite
d'étapes ordonnées, associée à un objectif et éventuellement à un
logiciel.

C'est ce qui permet à ARGOS d'apprendre un geste une seule fois,
et de le rejouer sans le réapprendre.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from core.paths import PROCEDURE_FILE, ensure_directories
from core.text import overlap_score, preview, tokens
from memory.store import read_json, write_json


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clean_steps(steps) -> List[str]:
    """Normalise une suite d'étapes en liste de chaînes."""

    if steps is None:
        return []

    if isinstance(steps, str):
        raw: Sequence[Any] = steps.splitlines()

    elif isinstance(steps, (list, tuple)):
        raw = steps

    else:
        raw = [steps]

    cleaned = []

    for step in raw:

        text = str(step or "").strip()

        if text:
            cleaned.append(text)

    return cleaned


class ProcedureMemory:
    """Procédures connues d'ARGOS."""

    def __init__(self, file_path=None):

        ensure_directories()

        self.file_path = file_path or PROCEDURE_FILE

    # =========================================================
    # ACCES AU FICHIER
    # =========================================================

    def _load(self) -> Dict[str, Dict[str, Any]]:

        data = read_json(self.file_path, {})

        if not isinstance(data, dict):
            return {}

        entries = data.get("procedures")

        if not isinstance(entries, dict):
            return {}

        return {
            key: value
            for key, value in entries.items()
            if isinstance(value, dict)
        }

    def _save(self, entries: Dict[str, Dict[str, Any]]) -> None:

        write_json(self.file_path, {"procedures": entries})

    # =========================================================
    # ENREGISTREMENT
    # =========================================================

    def save(
        self,
        name: str,
        steps,
        goal: str = "",
        software: str = "",
        source: str = "utilisateur",
    ) -> Optional[Dict[str, Any]]:
        """Enregistre ou remplace une procédure."""

        label = str(name or "").strip()

        cleaned = _clean_steps(steps)

        if not label or not cleaned:
            return None

        entries = self._load()

        identifier = label.lower()

        existing = entries.get(identifier)

        record = {
            "name": label,
            "goal": str(goal or "").strip(),
            "software": str(software or "").strip(),
            "steps": cleaned,
            "source": str(source or "utilisateur"),
            "created": existing.get("created") if existing else _now(),
            "updated": _now(),
            "uses": int(existing.get("uses", 0)) if existing else 0,
        }

        entries[identifier] = record

        self._save(entries)

        return record

    def forget(self, name: str) -> bool:

        entries = self._load()

        identifier = str(name or "").strip().lower()

        if identifier not in entries:
            return False

        del entries[identifier]

        self._save(entries)

        return True

    def use(self, name: str) -> Optional[Dict[str, Any]]:
        """Marque une procédure comme rejouée."""

        entries = self._load()

        identifier = str(name or "").strip().lower()

        record = entries.get(identifier)

        if not record:
            return None

        record["uses"] = int(record.get("uses", 0)) + 1
        record["last_used"] = _now()

        self._save(entries)

        return record

    # =========================================================
    # LECTURE
    # =========================================================

    def get(self, name: str) -> Optional[Dict[str, Any]]:

        return self._load().get(str(name or "").strip().lower())

    def all(self) -> List[Dict[str, Any]]:

        entries = list(self._load().values())

        entries.sort(key=lambda item: item.get("updated", ""), reverse=True)

        return entries

    def count(self) -> int:

        return len(self._load())

    def find(
        self,
        query: str,
        limit: int = 3,
        minimum_score: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """Retrouve les procédures proches d'une demande.

        « refais ce que je t'avais montré » doit retrouver la
        dernière procédure apprise.
        """

        query_tokens = tokens(query)

        if not query_tokens:
            return []

        scored = []

        for procedure in self.all():

            haystack = " ".join(
                [
                    procedure.get("name", ""),
                    procedure.get("goal", ""),
                    procedure.get("software", ""),
                    " ".join(procedure.get("steps", [])),
                ]
            )

            score = overlap_score(query_tokens, tokens(haystack))

            if score < minimum_score:
                continue

            scored.append((score, procedure))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []

        for score, procedure in scored[: max(1, limit)]:

            enriched = dict(procedure)
            enriched["score"] = round(score, 3)

            results.append(enriched)

        return results

    def latest(self) -> Optional[Dict[str, Any]]:
        """La dernière procédure enregistrée."""

        entries = self.all()

        return entries[0] if entries else None

    # =========================================================
    # EXPORT
    # =========================================================

    @staticmethod
    def format(procedure: Dict[str, Any]) -> str:
        """Rend une procédure lisible pas à pas."""

        if not procedure:
            return ""

        lines = [f"Procédure : {procedure.get('name', '')}"]

        goal = procedure.get("goal")

        if goal:
            lines.append(f"Objectif : {goal}")

        software = procedure.get("software")

        if software:
            lines.append(f"Logiciel : {software}")

        lines.append("")

        for index, step in enumerate(procedure.get("steps", []), start=1):
            lines.append(f"{index}. {step}")

        uses = procedure.get("uses")

        if uses:
            lines.append(f"\n(rejouée {uses} fois)")

        return "\n".join(lines)

    def as_prompt_text(self, limit: int = 5) -> str:
        """Bloc de prompt résumant les procédures connues."""

        procedures = self.all()[:limit]

        if not procedures:
            return ""

        lines = []

        for procedure in procedures:

            steps = procedure.get("steps", [])

            lines.append(
                f"- {procedure.get('name')} "
                f"({len(steps)} étapes"
                + (
                    f", logiciel : {procedure.get('software')}"
                    if procedure.get("software")
                    else ""
                )
                + ") : "
                + preview(procedure.get("goal"), 120)
            )

        return "\n".join(lines)

    def summary(self) -> Dict[str, Any]:

        return {
            "count": self.count(),
            "names": [item.get("name") for item in self.all()],
            "file": str(self.file_path),
        }
