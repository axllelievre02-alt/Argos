"""Mémoire des expériences d'ARGOS.

Le README (§22, §35 et §36) insiste sur un point précis :

    ARGOS doit vérifier le résultat.
    « commande exécutée » n'est pas « tâche réussie ».

Ce module conserve donc, pour chaque action réellement tentée :

    - ce qui était visé ;
    - ce qui a été fait ;
    - si cela a réussi ou échoué ;
    - pourquoi.

Cette mémoire permet à ARGOS :

    - d'éviter de répéter une action déjà connue comme échouée ;
    - de reconnaître les situations déjà rencontrées ;
    - de mesurer sa propre réussite sur un type de tâche.

C'est la boucle d'apprentissage du README §36 :

    utilisation → expérience → résultat → analyse → amélioration
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.paths import EXPERIENCE_FILE, ensure_directories
from core.text import overlap_score, preview, tokens
from memory.store import append_jsonl, read_jsonl, rewrite_jsonl

# Nombre maximum d'expériences conservées sur disque.
MAX_RECORDS = 2000


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ExperienceMemory:
    """Journal des réussites et des échecs d'ARGOS."""

    def __init__(self, file_path=None):

        ensure_directories()

        self.file_path = file_path or EXPERIENCE_FILE

    # =========================================================
    # ENREGISTREMENT
    # =========================================================

    def record(
        self,
        task: str,
        action: str,
        ok: bool,
        detail: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enregistre une expérience et retourne l'entrée créée."""

        entry = {
            "task": str(task or "").strip(),
            "action": str(action or "").strip(),
            "ok": bool(ok),
            "detail": preview(detail, 500),
            "context": context if isinstance(context, dict) else {},
            "created": _now(),
        }

        append_jsonl(self.file_path, entry)

        self._trim()

        return entry

    def _trim(self) -> None:
        """Garde le fichier dans une taille raisonnable."""

        records = read_jsonl(self.file_path)

        if len(records) <= MAX_RECORDS:
            return

        rewrite_jsonl(self.file_path, records[-MAX_RECORDS:])

    # =========================================================
    # LECTURE
    # =========================================================

    def all(self) -> List[Dict[str, Any]]:

        return read_jsonl(self.file_path)

    def count(self) -> int:

        return len(read_jsonl(self.file_path))

    def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Les expériences les plus récentes, de la plus récente à
        la plus ancienne."""

        return list(
            reversed(read_jsonl(self.file_path, limit=max(1, limit)))
        )

    def failures_for(self, task: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Les derniers échecs liés à une tâche."""

        needle = str(task or "").strip().lower()

        if not needle:
            return []

        failures = [
            entry for entry in self.all()
            if not entry.get("ok") and needle in entry.get("task", "").lower()
        ]

        return list(reversed(failures))[: max(1, limit)]

    def similar(
        self,
        query: str,
        limit: int = 5,
        minimum_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Retrouve les expériences proches d'une situation."""

        query_tokens = tokens(query)

        if not query_tokens:
            return []

        scored = []

        for entry in self.all():

            haystack = " ".join(
                [
                    entry.get("task", ""),
                    entry.get("action", ""),
                    entry.get("detail", ""),
                ]
            )

            score = overlap_score(query_tokens, tokens(haystack))

            if score < minimum_score:
                continue

            scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []

        for score, entry in scored[: max(1, limit)]:

            enriched = dict(entry)
            enriched["score"] = round(score, 3)

            results.append(enriched)

        return results

    # =========================================================
    # MESURE
    # =========================================================

    def success_rate(self, task: Optional[str] = None) -> Dict[str, Any]:
        """Taux de réussite global ou pour un type de tâche."""

        needle = str(task or "").strip().lower()

        entries = self.all()

        if needle:
            entries = [
                entry for entry in entries
                if needle in entry.get("task", "").lower()
            ]

        total = len(entries)

        successes = sum(1 for entry in entries if entry.get("ok"))

        rate = (successes / total) if total else 0.0

        return {
            "task": task or "",
            "total": total,
            "successes": successes,
            "failures": total - successes,
            "rate": round(rate, 3),
        }

    def lessons(self, limit: int = 5) -> List[str]:
        """Leçons tirées des échecs répétés.

        Une action échouée au moins deux fois, et plus souvent
        qu'elle n'a réussi, est considérée comme une leçon.
        """

        counts: Dict[str, Dict[str, int]] = {}

        for entry in self.all():

            key = entry.get("action", "").strip()

            if not key:
                continue

            bucket = counts.setdefault(key, {"ok": 0, "ko": 0})

            bucket["ok" if entry.get("ok") else "ko"] += 1

        lessons = []

        for action, bucket in counts.items():

            if bucket["ko"] >= 2 and bucket["ko"] > bucket["ok"]:

                lessons.append(
                    f"L'action « {action} » a échoué "
                    f"{bucket['ko']} fois sur {bucket['ko'] + bucket['ok']}."
                )

        return lessons[: max(1, limit)]

    # =========================================================
    # EXPORT
    # =========================================================

    def as_prompt_text(self, limit: int = 6) -> str:
        """Bloc de prompt résumant l'expérience récente."""

        entries = self.recent(limit)

        lessons = self.lessons(3)

        if not entries and not lessons:
            return ""

        lines = []

        for entry in entries:

            status = "réussi" if entry.get("ok") else "échoué"

            detail = (
                f" ({preview(entry.get('detail'), 120)})"
                if entry.get("detail")
                else ""
            )

            lines.append(
                f"- {entry.get('task')} / {entry.get('action')} "
                f"→ {status}{detail}"
            )

        if lessons:
            lines.append("Leçons retenues :")
            lines.extend(f"  {lesson}" for lesson in lessons)

        return "\n".join(lines)

    def summary(self) -> Dict[str, Any]:

        return {
            "count": self.count(),
            "success_rate": self.success_rate(),
            "lessons": self.lessons(5),
            "file": str(self.file_path),
        }
