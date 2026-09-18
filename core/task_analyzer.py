class TaskAnalyzer:
    """
    Analyse la requête utilisateur avant la prise de décision
    de Prometheus.

    TaskAnalyzer ne choisit pas les moteurs.

    Son rôle est uniquement de transformer une requête brute
    en informations structurées pouvant aider Prometheus.

    Pipeline :

        Utilisateur
             ↓
        TaskAnalyzer
             ↓
        Prometheus
             ↓
        MissionBuilder
             ↓
        Planner
             ↓
        Executor
    """

    def __init__(self):

        self.last_analysis = None

        # =====================================================
        # MOTS-CLES
        # =====================================================

        self.internet_keywords = [
            "internet",
            "web",
            "google",
            "cherche",
            "chercher",
            "recherche",
            "rechercher",
            "actualité",
            "actualités",
            "actualite",
            "actualites",
            "news",
            "site",
            "en ligne",
            "enligne",
            "dernière version",
            "derniere version",
            "aujourd'hui",
            "aujourd hui",
            "récent",
            "recente",
            "récents",
            "recentes",
            "nouveau",
            "nouveauté",
            "nouveautés",
            "nouveaute",
            "nouveautes"
        ]

        self.code_keywords = [
            "python",
            "code",
            "bug",
            "erreur",
            "corrige",
            "corriger",
            "correction",
            "fonction",
            "classe",
            "algorithme",
            "programmation",
            "programme",
            "script",
            "développer",
            "developper",
            "développement",
            "developpement"
        ]

        self.academy_keywords = [
            "explique",
            "expliquer",
            "pourquoi",
            "comment",
            "cours",
            "définition",
            "definition",
            "c est quoi",
            "c'est quoi",
            "apprends",
            "apprendre",
            "comprends",
            "comprendre",
            "apprentissage"
        ]

        self.knowledge_keywords = [
            "mon",
            "ma",
            "mes",
            "m'appelle",
            "m appelle",
            "nom",
            "prénom",
            "prenom",
            "jeu préféré",
            "jeu prefere",
            "jeux préféré",
            "jeux prefere",
            "jeu favori",
            "moteur préféré",
            "moteur prefere",
            "projet",
            "mes informations",
            "sur moi",
            "qui suis-je",
            "qui suis je"
        ]

        self.contextual_keywords = [
            "et pourquoi",
            "et comment",
            "et alors",
            "et donc",
            "et ça",
            "et ca",
            "et cela",
            "et lui",
            "et elle",
            "lequel",
            "laquelle",
            "ce dernier",
            "cette dernière",
            "cette derniere"
        ]

    # =========================================================
    # NORMALISATION
    # =========================================================

    @staticmethod
    def normalize(text):

        if not isinstance(text, str):
            return ""

        text = text.lower().strip()

        text = (
            text
            .replace("’", "'")
            .replace("`", "'")
        )

        text = " ".join(
            text.split()
        )

        return text

    # =========================================================
    # DETECTION
    # =========================================================

    @staticmethod
    def _contains_any(
        text,
        keywords
    ):

        return any(
            keyword in text
            for keyword in keywords
        )

    # =========================================================
    # ANALYSE
    # =========================================================

    def analyze(
        self,
        message,
        conversation=None
    ):
        """
        Analyse une requête utilisateur.

        Retourne uniquement des informations structurées.

        TaskAnalyzer ne décide pas du plan d'exécution.
        """

        if not isinstance(
            message,
            str
        ):

            raise TypeError(
                "Le message doit être une chaîne."
            )

        message = message.strip()

        if not message:

            analysis = {
                "intent": "unknown",
                "goal": "",
                "normalized_message": "",
                "keywords": [],
                "signals": {
                    "internet": False,
                    "code": False,
                    "academy": False,
                    "knowledge": False,
                    "contextual": False
                }
            }

            self.last_analysis = analysis

            return analysis

        text = self.normalize(
            message
        )

        # =====================================================
        # SIGNAUX
        # =====================================================

        internet = self._contains_any(
            text,
            self.internet_keywords
        )

        code = self._contains_any(
            text,
            self.code_keywords
        )

        academy = self._contains_any(
            text,
            self.academy_keywords
        )

        knowledge = self._contains_any(
            text,
            self.knowledge_keywords
        )

        contextual = self._contains_any(
            text,
            self.contextual_keywords
        )

        # =====================================================
        # CONVERSATION
        # =====================================================

        has_conversation = bool(
            conversation
        )

        # =====================================================
        # INTENTION PRINCIPALE
        # =====================================================

        if knowledge:

            intent = "knowledge"

        elif internet:

            intent = "internet"

        elif code:

            intent = "code"

        elif academy:

            intent = "academy"

        elif contextual and has_conversation:

            intent = "contextual"

        else:

            intent = "general"

        # =====================================================
        # OBJECTIF
        # =====================================================

        goals = {

            "knowledge":
                "Récupérer ou utiliser des informations "
                "personnelles ou mémorisées.",

            "internet":
                "Rechercher des informations actuelles "
                "ou disponibles sur Internet.",

            "code":
                "Analyser, corriger ou produire du code.",

            "academy":
                "Expliquer ou enseigner un concept.",

            "contextual":
                "Comprendre la demande à partir du contexte "
                "de la conversation.",

            "general":
                "Comprendre et traiter la demande "
                "de l'utilisateur.",

            "unknown":
                ""
        }

        goal = goals.get(
            intent,
            goals["general"]
        )

        # =====================================================
        # MOTS-CLES DETECTES
        # =====================================================

        keywords = []

        keyword_groups = [

            self.internet_keywords,
            self.code_keywords,
            self.academy_keywords,
            self.knowledge_keywords,
            self.contextual_keywords

        ]

        for group in keyword_groups:

            for keyword in group:

                if keyword in text:

                    if keyword not in keywords:

                        keywords.append(
                            keyword
                        )

        # =====================================================
        # ANALYSE
        # =====================================================

        analysis = {

            "intent":
                intent,

            "goal":
                goal,

            "normalized_message":
                text,

            "keywords":
                keywords,

            "signals": {

                "internet":
                    internet,

                "code":
                    code,

                "academy":
                    academy,

                "knowledge":
                    knowledge,

                "contextual":
                    contextual,

                "conversation":
                    has_conversation
            }

        }

        self.last_analysis = analysis

        return analysis

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "last_analysis":
                self.last_analysis

        }