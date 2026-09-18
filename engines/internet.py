from typing import Any, Dict, List

from ddgs import DDGS

from core.base_engine import BaseEngine


class InternetEngine(BaseEngine):
    """
    Moteur Internet d'ARGOS.

    Effectue des recherches Web avec DDGS et fournit
    les résultats au Context utilisé par ARGOS.
    """

    def __init__(self, max_results: int = 5):

        super().__init__(
            name="internet",
            capabilities=[
                "web_search",
                "internet",
                "search",
                "recherche_web",
            ],
            priority=10,
        )

        self.max_results = max_results

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(
        self,
        message,
        context
    ):
        """
        Méthode appelée par EngineManager.

        Pipeline :

            Executor
                ↓
            EngineManager
                ↓
            InternetEngine.execute()
                ↓
            DDGS
        """

        query = self._extract_query(
            message
        )

        if not query:

            return {
                "mode": "internet",
                "query": "",
                "results": [],
                "error": (
                    "Aucune requête Internet fournie."
                ),
                "content": None,
                "prompt_context": (
                    "RECHERCHE WEB ARGOS\n\n"
                    "Aucune requête de recherche "
                    "n'a été fournie."
                ),
            }

        try:

            results = self._search(
                query
            )

            # -------------------------------------------------
            # Aucun résultat
            # -------------------------------------------------

            if not results:

                return {
                    "mode": "internet",
                    "query": query,
                    "results": [],
                    "error": None,
                    "content": None,
                    "prompt_context": (
                        "RECHERCHE WEB ARGOS\n\n"
                        f"Requête : {query}\n\n"
                        "Aucun résultat exploitable "
                        "n'a été trouvé."
                    ),
                }

            # -------------------------------------------------
            # Résultats trouvés
            # -------------------------------------------------

            content = self._build_content(
                results
            )

            prompt_context = (
                self._build_prompt_context(
                    query,
                    results
                )
            )

            return {
                "mode": "internet",
                "query": query,
                "results": results,
                "error": None,
                "content": None,
                "prompt_context": prompt_context,
            }

        except Exception as error:

            try:

                context.add_error(
                    f"internet : {error}"
                )

            except Exception:

                pass

            try:

                context.log(
                    f"Erreur InternetEngine : {error}"
                )

            except Exception:

                pass

            return {
                "mode": "internet",
                "query": query,
                "results": [],
                "error": str(error),
                "content": None,
                "prompt_context": (
                    "RECHERCHE WEB ARGOS\n\n"
                    f"Requête : {query}\n\n"
                    "Une erreur est survenue pendant "
                    f"la recherche Internet : {error}"
                ),
            }

    # =========================================================
    # EXTRACTION DE LA REQUETE
    # =========================================================

    def _extract_query(
        self,
        message: Any
    ) -> str:
        """
        Récupère la requête utilisateur.
        """

        if message is None:

            return ""

        if isinstance(
            message,
            dict
        ):

            query = (
                message.get("query")
                or message.get("message")
                or message.get("text")
                or message.get("content")
                or message.get("input")
                or ""
            )

            return str(
                query
            ).strip()

        query = getattr(
            message,
            "query",
            None
        )

        if query:

            return str(
                query
            ).strip()

        text = getattr(
            message,
            "text",
            None
        )

        if text:

            return str(
                text
            ).strip()

        return str(
            message
        ).strip()

    # =========================================================
    # RECHERCHE INTERNET
    # =========================================================

    def _search(
        self,
        query: str
    ) -> List[Dict[str, str]]:
        """
        Effectue une recherche Web via DDGS.
        """

        raw_results = DDGS().text(
            query,
            max_results=self.max_results,
        )

        results = []

        for item in (
            raw_results or []
        ):

            if not isinstance(
                item,
                dict
            ):

                continue

            title = str(
                item.get(
                    "title",
                    ""
                )
            ).strip()

            url = str(
                item.get(
                    "href",
                    ""
                )
            ).strip()

            snippet = str(
                item.get(
                    "body",
                    ""
                )
            ).strip()

            # Résultat totalement vide
            if (
                not title
                and not url
                and not snippet
            ):

                continue

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        return results

    # =========================================================
    # CONTENU
    # =========================================================

    def _build_content(
        self,
        results: List[Dict[str, str]]
    ) -> str:
        """
        Transforme les résultats en texte lisible.
        """

        blocks = []

        for index, result in enumerate(
            results,
            start=1
        ):

            title = result.get(
                "title",
                ""
            )

            url = result.get(
                "url",
                ""
            )

            snippet = result.get(
                "snippet",
                ""
            )

            block = (
                f"{index}. {title}\n"
                f"URL : {url}\n"
                f"{snippet}"
            )

            blocks.append(
                block
            )

        return "\n\n".join(
            blocks
        )

    # =========================================================
    # CONTEXTE POUR QWEN
    # =========================================================

    def _build_prompt_context(
        self,
        query: str,
        results: List[Dict[str, str]]
    ) -> str:
        """
        Construit les informations qui pourront être
        transmises au ResponseManager / modèle local.
        """

        content = self._build_content(
            results
        )

        return (
            "RECHERCHE WEB ARGOS\n\n"
            f"Requête utilisateur : {query}\n\n"
            "Résultats Internet disponibles :\n\n"
            f"{content}\n\n"
            "Utilise prioritairement les informations "
            "ci-dessus pour répondre à la requête. "
            "N'invente pas de résultat absent de "
            "la recherche."
        )
