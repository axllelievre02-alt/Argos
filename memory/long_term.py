"""Mémoire persistante de long terme d'ARGOS.

Le README (§5 et §7) distingue plusieurs natures d'information :

    - information temporaire   « je vais faire du café »
    - information importante   « mon projet actuel est ARGOS »
    - décision de projet       « ARGOS doit rester indépendant du modèle »
    - préférence               « je veux être appelé Ikaris »
    - règle comportementale    « demande confirmation avant une
                                 action dangereuse »

ProfileMemory contient l'identité stable de l'utilisateur.
LongTermMemory contient tout le reste : faits, décisions, règles et
préférences durables, avec leur origine et leur date.

C'est cette mémoire qui donne à ARGOS une continuité entre deux
sessions séparées de plusieurs mois (README §1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.paths import LONG_TERM_FILE, ensure_directories
from core.text import overlap_score, preview, tokens
from memory.store import read_json, write_json

# Catégories reconnues.
CATEGORY_NOTE = "note"
CATEGORY_FACT = "fait"
CATEGORY_DECISION = "decision"
CATEGORY_PREFERENCE = "preference"
CATEGORY_PROJECT = "projet"
CATEGORY_RULE = "regle"

CATEGORIES = (
    CATEGORY_NOTE,
    CATEGORY_FACT,
    CATEGORY_DECISION,
    CATEGORY_PREFERENCE,
    CATEGORY_PROJECT,
    CATEGORY_RULE,
)

CATEGORY_LABELS: Dict[str, str] = {
    CATEGORY_NOTE: "Note",
    CATEGORY_FACT: "Fait",
    CATEGORY_DECISION: "Décision",
    CATEGORY_PREFERENCE: "Préférence",
    CATEGORY_PROJECT: "Projet",
    CATEGORY_RULE: "Règle",
}


def _now() -> str:
    """Horodatage lisible."""

    return datetime.now().isoformat(timespec="seconds")


class LongTermMemory:
    """Faits durables d'ARGOS, persistés entre les sessions."""

    def __init__(self, file_path=None):

        ensure_directories()

        self.file_path = file_path or LONG_TERM_FILE

    # =========================================================
    # ACCES AU FICHIER
    # =========================================================

    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Charge les faits enregistrés."""

        data = read_json(self.file_path, {})

        if not isinstance(data, dict):
            return {}

        facts = data.get("facts")

        if not isinstance(facts, dict):
            return {}

        return {
            key: value
            for key, value in facts.items()
            if isinstance(value, dict)
        }

    def _save(self, facts: Dict[str, Dict[str, Any]]) -> None:

        write_json(self.file_path, {"facts": facts})

    # =========================================================
    # ECRITURE
    # =========================================================

    def remember(
        self,
        key: str,
        value: str,
        category: str = CATEGORY_NOTE,
        source: str = "utilisateur",
    ) -> Optional[Dict[str, Any]]:
        """Enregistre ou met à jour un fait durable."""

        label = str(key or "").strip()
        content = str(value or "").strip()

        if not label or not content:
            return None

        if category not in CATEGORIES:
            category = CATEGORY_NOTE

        facts = self._load()

        identifier = label.lower()

        existing = facts.get(identifier)

        record: Dict[str, Any] = {
            "key": label,
            "value": content,
            "category": category,
            "source": str(source or "utilisateur"),
            "created": existing.get("created") if existing else _now(),
            "updated": _now(),
            "uses": int(existing.get("uses", 0)) if existing else 0,
        }

        facts[identifier] = record

        self._save(facts)

        return record

    def forget(self, key: str) -> bool:
        """Supprime un fait. Retourne True s'il existait."""

        facts = self._load()

        identifier = str(key or "").strip().lower()

        if identifier not in facts:
            return False

        del facts[identifier]

        self._save(facts)

        return True

    def touch(self, key: str) -> None:
        """Compte une utilisation d'un fait."""

        facts = self._load()

        identifier = str(key or "").strip().lower()

        record = facts.get(identifier)

        if not record:
            return

        record["uses"] = int(record.get("uses", 0)) + 1
        record["last_used"] = _now()

        self._save(facts)

    # =========================================================
    # LECTURE
    # =========================================================

    def get(self, key: str) -> Optional[Dict[str, Any]]:

        return self._load().get(str(key or "").strip().lower())

    def all(self) -> List[Dict[str, Any]]:
        """Tous les faits, du plus récent au plus ancien."""

        facts = list(self._load().values())

        facts.sort(key=lambda item: item.get("updated", ""), reverse=True)

        return facts

    def by_category(self, category: str) -> List[Dict[str, Any]]:

        return [
            fact for fact in self.all()
            if fact.get("category") == category
        ]

    def count(self) -> int:

        return len(self._load())

    # =========================================================
    # RECHERCHE SEMANTIQUE
    # =========================================================

    def recall(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        minimum_score: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Retrouve les faits les plus proches d'une question.

        Une correspondance sur la clé pèse plus lourd qu'une
        correspondance perdue dans un long texte.
        """

        query_tokens = tokens(query)

        if not query_tokens:
            return []

        scored = []

        for fact in self.all():

            if category and fact.get("category") != category:
                continue

            key_score = overlap_score(query_tokens, tokens(fact.get("key", "")))
            value_score = overlap_score(
                query_tokens, tokens(fact.get("value", ""))
            )

            score = key_score * 0.6 + value_score * 0.4

            if score < minimum_score:
                continue

            scored.append((score, fact))

        scored.sort(key=lambda item: item[0], reverse=True)

        results = []

        for score, fact in scored[: max(1, limit)]:

            enriched = dict(fact)
            enriched["score"] = round(score, 3)

            self.touch(fact.get("key", ""))

            results.append(enriched)

        return results

    # =========================================================
    # EXPORT
    # =========================================================

    def as_prompt_text(self, limit: int = 12) -> str:
        """Bloc de prompt résumant la mémoire durable."""

        facts = self.all()[:limit]

        if not facts:
            return ""

        lines = []

        for fact in facts:

            label = CATEGORY_LABELS.get(fact.get("category", ""), "Note")

            lines.append(
                f"- [{label}] {fact.get('key')} : "
                f"{preview(fact.get('value'), 200)}"
            )

        return "\n".join(lines)

    def summary(self) -> Dict[str, Any]:

        facts = self.all()

        by_category: Dict[str, int] = {}

        for fact in facts:

            name = fact.get("category", CATEGORY_NOTE)

            by_category[name] = by_category.get(name, 0) + 1

        return {
            "count": len(facts),
            "by_category": by_category,
            "file": str(self.file_path),
        }
