"""Normalisation de texte partagée par ARGOS.

Plusieurs composants doivent comparer du texte écrit en français :
mémoire sémantique, recherche de connaissances, détection de
commandes.

Ce module centralise cette mécanique afin d'éviter des variantes
divergentes d'un module à l'autre.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

# Mots trop fréquents pour être discriminants lors d'une recherche.
STOPWORDS = frozenset({
    "le", "la", "les", "un", "une", "des", "de", "du", "da",
    "et", "ou", "a", "au", "aux", "en", "dans", "sur", "pour",
    "par", "avec", "sans", "que", "qui", "quoi", "dont", "est",
    "sont", "etre", "avoir", "ce", "cet", "cette", "ces", "son",
    "sa", "ses", "mon", "ma", "mes", "ton", "ta", "tes", "il",
    "elle", "ils", "elles", "je", "tu", "nous", "vous", "on",
    "the", "a", "an", "of", "to", "and", "or", "in", "on", "for",
    "is", "are", "was", "were", "it", "this", "that",
})

_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def normalize(text) -> str:
    """Minuscules, sans accents, espaces uniques."""

    if text is None:
        return ""

    lowered = unicodedata.normalize("NFD", str(text).lower())

    stripped = "".join(
        char for char in lowered if unicodedata.category(char) != "Mn"
    )

    return " ".join(stripped.split())


def tokens(text) -> List[str]:
    """Découpe un texte en mots significatifs.

    Les apostrophes et la ponctuation servent de séparateurs, ce qui
    transforme « j'adore son univers » en ["adore", "univers"].
    """

    normalized = normalize(text)

    words = _WORD_PATTERN.findall(normalized)

    return [word for word in words if word and word not in STOPWORDS]


def overlap_score(query_tokens, target_tokens) -> float:
    """Mesure la ressemblance entre deux ensembles de mots.

    Retourne un score entre 0 et 1 : proportion des mots de la
    requête réellement présents dans la cible.
    """

    if not query_tokens or not target_tokens:
        return 0.0

    target = set(target_tokens)

    matched = sum(1 for token in set(query_tokens) if token in target)

    return matched / len(set(query_tokens))


def preview(text, length: int = 160) -> str:
    """Retourne un extrait d'une ligne, sans retour à la ligne."""

    flat = " ".join(str(text or "").split())

    if len(flat) <= length:
        return flat

    return flat[: length - 3] + "..."
