"""Recherche Web d'ARGOS.

Point d'entrée unique pour toute recherche Internet du projet :
l'InternetEngine et l'outil search_web partagent ce module afin
d'éviter deux implémentations divergentes.

Les API externes ne sont qu'une capacité d'ARGOS, jamais son
intelligence (README §27) : si la recherche échoue, ARGOS reste
ARGOS et le signale.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from ddgs import DDGS

DEFAULT_MAX_RESULTS = 5

# Signature d'un fournisseur de recherche injectable.
SearchProvider = Callable[[str, int], List[Dict[str, str]]]


class WebSearchError(RuntimeError):
    """Erreur levée lorsqu'une recherche Web échoue."""


def _clean_result(item) -> Dict[str, str]:
    """Normalise un résultat brut de DDGS."""

    if not isinstance(item, dict):
        return {}

    return {
        "title": str(item.get("title", "") or "").strip(),
        "url": str(item.get("href") or item.get("url") or "").strip(),
        "snippet": str(item.get("body") or item.get("snippet") or "").strip(),
    }


def search_web(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict[str, str]]:
    """Effectue une recherche Web et retourne des résultats normalisés.

    Chaque résultat contient les clés title, url et snippet.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    try:
        raw_results = DDGS().text(
            query.strip(),
            max_results=max_results,
        )

    except Exception as error:
        raise WebSearchError(f"Recherche Web impossible : {error}") from error

    results: List[Dict[str, str]] = []

    for item in raw_results or []:

        result = _clean_result(item)

        if not result:
            continue

        if not (result["title"] or result["url"] or result["snippet"]):
            continue

        results.append(result)

    return results
