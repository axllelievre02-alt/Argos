"""Outils Web d'ARGOS.

Ces outils donnent accès à Internet, mais ARGOS ne les considère
jamais comme son intelligence (README §27) : ce sont des capacités
externes, et une panne de réseau ne doit pas faire tomber ARGOS.

Les deux outils sont en lecture seule : ils ne modifient rien.
"""

from __future__ import annotations

from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from core.permissions import READ
from core.tools.base import Tool, ToolResult
from core.tools.filesystem_common import format_size
from core.web_search import DEFAULT_MAX_RESULTS, WebSearchError, search_web

# Durée maximale d'une requête HTTP.
HTTP_TIMEOUT = 20

# Taille maximale téléchargée.
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024

# Taille maximale du texte renvoyé au modèle.
MAX_TEXT_CHARS = 6000

# Schémas autorisés : aucun accès fichier ni pseudo-protocole.
ALLOWED_SCHEMES = ("http", "https")

USER_AGENT = "ARGOS/1.0 (assistant personnel local)"


class SearchWebTool(Tool):
    """Recherche des informations sur Internet."""

    name = "search_web"
    description = "Rechercher des informations sur Internet."
    level = READ
    read_only = True
    parameters = {
        "query": "Requête de recherche.",
        "max_results": "Nombre de résultats souhaités.",
    }
    required = ("query",)

    def target(self, query="", **_kwargs) -> str:

        return str(query or "")

    def run(self, query="", max_results=None, **_kwargs) -> ToolResult:

        text = str(query or "").strip()

        if not text:
            return ToolResult(
                ok=False, tool=self.name, error="Requête de recherche vide."
            )

        try:
            limit = int(max_results) if max_results else DEFAULT_MAX_RESULTS

        except (TypeError, ValueError):
            limit = DEFAULT_MAX_RESULTS

        limit = max(1, min(limit, 10))

        try:
            results = search_web(text, max_results=limit)

        except WebSearchError as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=str(error),
                data={"query": text},
            )

        if not results:
            return ToolResult(
                ok=True,
                tool=self.name,
                output=f"Aucun résultat pour : {text}",
                data={"query": text, "results": 0},
            )

        blocks: List[str] = []

        for index, result in enumerate(results, start=1):

            blocks.append(
                f"{index}. {result['title']}\n"
                f"   {result['url']}\n"
                f"   {result['snippet']}"
            )

        return ToolResult(
            ok=True,
            tool=self.name,
            output=(
                f"Résultats Internet pour {text!r} :\n\n"
                + "\n\n".join(blocks)
            ),
            data={"query": text, "results": results},
        )


class FetchUrlTool(Tool):
    """Lit le contenu texte d'une page Web."""

    name = "fetch_url"
    description = "Lire le contenu texte d'une page Web."
    level = READ
    read_only = True
    parameters = {
        "url": "Adresse de la page (http ou https).",
    }
    required = ("url",)

    def target(self, url="", **_kwargs) -> str:

        return str(url or "")

    def run(self, url="", **_kwargs) -> ToolResult:

        address = str(url or "").strip()

        if not address:
            return ToolResult(
                ok=False, tool=self.name, error="Adresse vide."
            )

        parsed = urlparse(address)

        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=(
                    f"Schéma non autorisé : {parsed.scheme or '(aucun)'}. "
                    "Seules les adresses http et https sont acceptées."
                ),
            )

        if not parsed.netloc:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Adresse invalide : {address}",
            )

        try:
            response = requests.get(
                address,
                timeout=HTTP_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
                stream=True,
            )

        except requests.RequestException as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Téléchargement impossible : {error}",
            )

        try:
            content = response.raw.read(
                MAX_DOWNLOAD_BYTES + 1,
                decode_content=True,
            )

        except Exception as error:

            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Lecture impossible : {error}",
            )

        finally:

            response.close()

        if not response.ok:
            return ToolResult(
                ok=False,
                tool=self.name,
                error=f"Le serveur a répondu {response.status_code}.",
                data={"status": response.status_code, "url": address},
            )

        truncated = len(content) > MAX_DOWNLOAD_BYTES

        text = self._to_text(content)

        if not text:
            return ToolResult(
                ok=True,
                tool=self.name,
                output=f"{address} ne contient pas de texte exploitable.",
                data={"url": address, "characters": 0},
            )

        header = (
            f"Page : {address}\n"
            f"Taille téléchargée : {format_size(len(content))}\n"
        )

        if truncated:
            header += "(contenu partiellement téléchargé)\n"

        return ToolResult(
            ok=True,
            tool=self.name,
            output=header + "\n" + text,
            data={
                "url": address,
                "characters": len(text),
                "truncated": truncated,
            },
        )

    @staticmethod
    def _to_text(content: bytes) -> str:
        """Convertit du HTML brut en texte lisible."""

        soup = BeautifulSoup(content, "html.parser")

        for tag in soup(["script", "style", "noscript", "template", "svg"]):
            tag.decompose()

        raw = soup.get_text(separator="\n")

        lines = [line.strip() for line in raw.splitlines()]

        cleaned: List[str] = []
        previous_blank = False

        for line in lines:

            if not line:
                if previous_blank:
                    continue

                previous_blank = True

                continue

            previous_blank = False

            cleaned.append(line)

        text = "\n".join(cleaned).strip()

        if len(text) > MAX_TEXT_CHARS:
            text = (
                text[:MAX_TEXT_CHARS]
                + f"\n... [texte tronqué, {len(text)} caractères au total]"
            )

        return text


WEB_TOOLS = (
    SearchWebTool(),
    FetchUrlTool(),
)
