from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

import re

from core.base_engine import BaseEngine


class InternetEngine(BaseEngine):
    """
    Recherche des sources web publiques pour ARGOS.

    Le moteur ne produit pas lui-même la réponse finale. Il renvoie
    des résultats structurés que ResponseManager peut faire
    synthétiser par le modèle.
    """

    def __init__(
        self,
        max_results=5,
        timeout=8,
        search_provider=None
    ):

        super().__init__(
            name="internet",
            priority=1,
            capabilities=[
                "internet",
                "web_search",
                "current_information"
            ]
        )

        self.max_results = max_results
        self.timeout = timeout
        self.search_provider = search_provider

    # =========================================================
    # RECHERCHE
    # =========================================================

    def search(self, query):
        """Retourne une liste de résultats web normalisés."""

        if self.search_provider is not None:

            results = self.search_provider(
                query,
                self.max_results
            )

            return self._normalize_results(
                results
            )

        url = (
            "https://html.duckduckgo.com/html/?q="
            + quote_plus(query)
        )

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; ARGOS/1.0)"
                )
            }
        )

        with urlopen(
            request,
            timeout=self.timeout
        ) as response:

            html = response.read().decode(
                "utf-8",
                errors="replace"
            )

        return self._parse_duckduckgo_results(
            html
        )

    def _parse_duckduckgo_results(self, html):

        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>'
            r'(.*?)</a>'
            r'.*?(?:class="result__snippet"[^>]*>(.*?)</(?:a|div)>|'
            r'class="result__snippet"[^>]*>(.*?)</div>)',
            re.DOTALL
        )

        results = []

        for match in pattern.finditer(html):

            href = self._extract_result_url(
                unescape(match.group(1))
            )

            title = self._clean_html(
                match.group(2)
            )

            snippet = self._clean_html(
                match.group(3) or match.group(4) or ""
            )

            if not href or not title:
                continue

            results.append(
                {
                    "title": title,
                    "url": href,
                    "snippet": snippet
                }
            )

            if len(results) >= self.max_results:
                break

        return results

    @staticmethod
    def _extract_result_url(href):

        parsed = urlparse(href)

        if parsed.path.startswith("/l/"):

            target = parse_qs(
                parsed.query
            ).get(
                "uddg",
                [""]
            )[0]

            return unquote(target)

        return href

    @staticmethod
    def _clean_html(value):

        value = re.sub(
            r"<[^>]+>",
            " ",
            value or ""
        )

        return " ".join(
            unescape(value).split()
        )

    def _normalize_results(self, results):

        if not isinstance(results, list):
            return []

        normalized = []

        for result in results:

            if not isinstance(result, dict):
                continue

            title = str(
                result.get("title", "")
            ).strip()

            url = str(
                result.get("url", "")
            ).strip()

            snippet = str(
                result.get("snippet", "")
            ).strip()

            if not title or not url:
                continue

            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet
                }
            )

            if len(normalized) >= self.max_results:
                break

        return normalized

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(
        self,
        message,
        context=None
    ):

        if not isinstance(message, str):
            return None

        query = message.strip()

        if not query:
            return None

        try:

            results = self.search(
                query
            )

        except Exception as error:

            result = {
                "mode": "internet",
                "query": query,
                "results": [],
                "error": str(error),
                "content": None,
                "prompt_context": (
                    "RECHERCHE WEB ARGOS\n\n"
                    f"Requête : {query}\n\n"
                    "La recherche web a échoué. "
                    "Ne prétends pas disposer de résultats."
                )
            }

            if context is not None:
                context.set("internet", result)

            return result

        result = {
            "mode": "internet",
            "query": query,
            "results": results,
            "error": None,
            "content": None,
            "prompt_context": self._build_prompt_context(
                query,
                results
            )
        }

        if context is not None:

            context.set("internet", result)
            context.set("internet_results", results)

        return result

    @staticmethod
    def _build_prompt_context(query, results):

        lines = [
            "RECHERCHE WEB ARGOS",
            "",
            f"Requête : {query}",
            ""
        ]

        if not results:

            lines.append(
                "Aucun résultat exploitable n'a été trouvé."
            )

            return "\n".join(lines)

        lines.append("SOURCES TROUVÉES :")
        lines.append("")

        for index, result in enumerate(
            results,
            start=1
        ):

            lines.append(
                f"{index}. {result['title']}"
            )

            lines.append(
                f"   URL : {result['url']}"
            )

            if result["snippet"]:

                lines.append(
                    f"   Extrait : {result['snippet']}"
                )

        lines.extend(
            [
                "",
                "Utilise uniquement ces résultats comme "
                "sources web. Signale clairement leurs limites."
            ]
        )

        return "\n".join(lines)
