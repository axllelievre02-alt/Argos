"""Connaissances apprises par ARGOS.

Le README §9 décrit le cycle d'apprentissage suivant :

    Question
      ↓
    Recherche
      ↓
    Information
      ↓
    Validation
      ↓
    Connaissance
      ↓
    Mémoire

Ce module est l'étape « Connaissance ». Il conserve ce qu'ARGOS a
appris, avec :

    - la source d'origine ;
    - un niveau de confiance ;
    - les sources qui corroborent l'information.

Une information corroborée par plusieurs sources voit sa confiance
augmenter. C'est ce qui distingue une information vérifiée d'une
simple rumeur.

ARGOS n'a donc plus besoin de refaire exactement la même recherche
à chaque fois.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.paths import KNOWLEDGE_FILE, ensure_directories
from core.text import overlap_score, preview, tokens
from memory.store import read_json, write_json

# Confiance par défaut d'une information venant d'une seule source.
DEFAULT_CONFIDENCE = 0.5

# Gain de confiance lorsqu'une source supplémentaire corrobore.
CORROBORATION_GAIN = 0.15

MAX_CONFIDENCE = 1.0


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class KnowledgeStore:
    """Connaissances durables acquises par ARGOS."""

    def __init__(self, file_path=None):

        ensure_directories()

        self.file_path = file_path or KNOWLEDGE_FILE

    # =========================================================
    # ACCES AU FICHIER
    # =========================================================

    def _load(self) -> Dict[str, Dict[str, Any]]:

        data = read_json(self.file_path, {})

        if not isinstance(data, dict):
            return {}

        entries = data.get("knowledge")

        if not isinstance(entries, dict):
            return {}

        return {
            key: value
            for key, value in entries.items()
            if isinstance(value, dict)
        }

    def _save(self, entries: Dict[str, Dict[str, Any]]) -> None:

        write_json(self.file_path, {"knowledge": entries})

    # =========================================================
    # APPRENTISSAGE
    # =========================================================

    def learn(
        self,
        topic: str,
        content: str,
        source: str = "recherche",
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> Optional[Dict[str, Any]]:
        """Enregistre une connaissance.

        Si le sujet est déjà connu, la connaissance est mise à jour :

            - le contenu est remplacé par le plus récent ;
            - la source est ajoutée à la liste des sources ;
            - la confiance progresse, sans jamais dépasser 1.0.
        """

        label = str(topic or "").strip()
        body = str(content or "").strip()

        if not label or not body:
            return None

        entries = self._load()

        identifier = label.lower()

        existing = entries.get(identifier)

        try:
            level = float(confidence)

        except (TypeError, ValueError):
            level = DEFAULT_CONFIDENCE

        level = max(0.0, min(MAX_CONFIDENCE, level))

        if existing:

            sources = list(existing.get("sources", []))

            if source and source not in sources:
                sources.append(source)

                level = min(
                    MAX_CONFIDENCE,
                    float(existing.get("confidence", level))
                    + CORROBORATION_GAIN,
                )

            record = {
                "topic": existing.get("topic", label),
                "content": body,
                "source": source or existing.get("source", ""),
                "sources": sources,
                "confidence": round(level, 2),
                "created": existing.get("created", _now()),
                "updated": _now(),
                "uses": int(existing.get("uses", 0)),
            }

        else:

            record = {
                "topic": label,
                "content": body,
                "source": str(source or ""),
                "sources": [source] if source else [],
                "confidence": round(level, 2),
                "created": _now(),
                "updated": _now(),
                "uses": 0,
            }

        entries[identifier] = record

        self._save(entries)

        return record

    def forget(self, topic: str) -> bool:

        entries = self._load()

        identifier = str(topic or "").strip().lower()

        if identifier not in entries:
            return False

        del entries[identifier]

        self._save(entries)

        return True

    def touch(self, topic: str) -> None:

        entries = self._load()

        identifier = str(topic or "").strip().lower()

        record = entries.get(identifier)

        if not record:
            return

        record["uses"] = int(record.get("uses", 0)) + 1
        record["last_used"] = _now()

        self._save(entries)

    # =========================================================
    # LECTURE
    # =========================================================

    def get(self, topic: str) -> Optional[Dict[str, Any]]:

        return self._load().get(str(topic or "").strip().lower())

    def knows(self, topic: str) -> bool:

        record = self.get(topic)

        if not record:
            return False

        return float(record.get("confidence", 0)) >= 0.5

    def all(self) -> List[Dict[str, Any]]:

        entries = list(self._load().values())

        entries.sort(
            key=lambda item: (
                float(item.get("confidence", 0)),
                item.get("updated", ""),
            ),
            reverse=True,
        )

        return entries

    def count(self) -> int:

        return len(self._load())

    def search(
        self,
        query: str,
        limit: int = 5,
        minimum_score: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Retrouve les connaissances proches d'une question."""

        query_tokens = tokens(query)

        if not query_tokens:
            return []

        scored = []

        for entry in self.all():

            topic_score = overlap_score(
                query_tokens, tokens(entry.get("topic", ""))
            )
            content_score = overlap_score(
                query_tokens, tokens(entry.get("content", ""))
            )

            score = topic_score * 0.7 + content_score * 0.3

            if score < minimum_score:
                continue

            scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []

        for score, entry in scored[: max(1, limit)]:

            enriched = dict(entry)
            enriched["score"] = round(score, 3)

            self.touch(entry.get("topic", ""))

            results.append(enriched)

        return results

    # =========================================================
    # EXPORT
    # =========================================================

    def as_prompt_text(self, limit: int = 8, minimum_confidence: float = 0.5) -> str:
        """Bloc de prompt résumant les connaissances fiables."""

        entries = [
            entry for entry in self.all()
            if float(entry.get("confidence", 0)) >= minimum_confidence
        ][:limit]

        if not entries:
            return ""

        lines = []

        for entry in entries:

            lines.append(
                f"- {entry.get('topic')} "
                f"(confiance {entry.get('confidence')}) : "
                f"{preview(entry.get('content'), 240)}"
            )

        return "\n".join(lines)

    def summary(self) -> Dict[str, Any]:

        entries = self.all()

        confident = [
            entry for entry in entries
            if float(entry.get("confidence", 0)) >= 0.65
        ]

        return {
            "count": len(entries),
            "confident": len(confident),
            "topics": [entry.get("topic") for entry in entries[:10]],
            "file": str(self.file_path),
        }
