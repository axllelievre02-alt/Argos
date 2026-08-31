class Prometheus:
    """
    Système de décision d'ARGOS.

    Prometheus analyse la requête utilisateur et détermine
    quels moteurs doivent intervenir.

    Il ne répond jamais à l'utilisateur.

    Il produit uniquement un plan d'exécution.

    Principe :

        - requête simple -> un moteur
        - requête complexe -> plusieurs moteurs
        - requête dépendant de la mémoire -> Knowledge
        - requête nécessitant une explication -> Academy
        - requête contextuelle -> analyse de la conversation

    Prometheus ne génère jamais la réponse finale.
    """

    def __init__(
        self,
        available_engines=None
    ):

        self.available_engines = (
            set(available_engines)
            if available_engines is not None
            else None
        )

        self.rules = [

            # =================================================
            # INTERNET
            # =================================================

            {
                "engine": "internet",

                "keywords": [
                    "internet",
                    "web",
                    "google",
                    "cherche",
                    "recherche",
                    "actualité",
                    "actualités",
                    "news",
                    "site",
                    "en ligne"
                ]
            },

            # =================================================
            # CODE
            # =================================================

            {
                "engine": "code",

                "keywords": [
                    "python",
                    "code",
                    "bug",
                    "erreur",
                    "corrige",
                    "corriger",
                    "fonction",
                    "classe",
                    "algorithme",
                    "programmation",
                    "programme",
                    "script",
                    "développer",
                    "développement"
                ]
            },

            # =================================================
            # ACADEMY
            # =================================================

            {
                "engine": "academy",

                "keywords": [
                    "explique",
                    "pourquoi",
                    "comment",
                    "cours",
                    "définition",
                    "definition",
                    "c'est quoi",
                    "apprends",
                    "apprendre",
                    "comprends",
                    "comprendre"
                ]
            },

            # =================================================
            # KNOWLEDGE
            # =================================================

            {
                "engine": "knowledge",

                "keywords": [
                    "je m'appelle",
                    "je m appelle",
                    "mon nom",
                    "qui suis-je",
                    "qui suis je",
                    "mon jeu préféré",
                    "mon jeu prefere",
                    "mon jeux préféré",
                    "mon jeux prefere",
                    "mon moteur préféré",
                    "mon moteur prefere",
                    "mon projet",
                    "mon projet actuel",
                    "sur quoi je travaille",
                    "que sais-tu sur moi",
                    "que sais tu sur moi",
                    "qu'est-ce que tu sais sur moi",
                    "qu est ce que tu sais sur moi",
                    "mes informations"
                ]
            }
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

        text = text.replace(
            "'",
            " "
        )

        return " ".join(
            text.split()
        )

    # =========================================================
    # DETECTION KNOWLEDGE
    # =========================================================

    def _is_knowledge_request(self, text):

        text = self.normalize(
            text
        )

        # -----------------------------------------------------
        # Expressions directes
        # -----------------------------------------------------

        knowledge_patterns = [

            "quel est mon",
            "quelle est mon",
            "quels sont mes",
            "quelles sont mes",

            "quel est ma",
            "quelle est ma",

            "mon jeu prefere",
            "mon jeu préféré",

            "mon jeux prefere",
            "mon jeux préféré",

            "mon moteur prefere",
            "mon moteur préféré",

            "mon projet",
            "mon projet actuel",

            "sur quoi je travaille",

            "que sais tu sur moi",
            "que sais-tu sur moi",

            "qu est ce que tu sais sur moi",
            "qu'est ce que tu sais sur moi",

            "mes informations",

            "comment je m appelle",
            "comment je m'appelle",

            "qui suis je",
            "qui suis-je"
        ]

        if any(
            pattern in text
            for pattern in knowledge_patterns
        ):
            return True

        # -----------------------------------------------------
        # Détection de questions personnelles avec
        # tolérance légère aux formulations différentes.
        # -----------------------------------------------------

        personal_words = [
            "mon",
            "ma",
            "mes"
        ]

        personal_subjects = [
            "jeu",
            "jeux",
            "moteur",
            "projet",
            "nom",
            "prenom",
            "prénom",
            "information",
            "informations"
        ]

        has_personal = any(
            word in text.split()
            for word in personal_words
        )

        has_subject = any(
            word in text.split()
            for word in personal_subjects
        )

        if has_personal and has_subject:
            return True

        return False

    # =========================================================
    # DETECTION ACADEMY
    # =========================================================

    def _is_academy_request(self, text):

        text = self.normalize(
            text
        )

        academy_patterns = [

            "explique",
            "pourquoi",
            "comment",
            "cours",
            "definition",
            "définition",
            "c est quoi",
            "c'est quoi",
            "apprends",
            "apprendre",
            "comprends",
            "comprendre"

        ]

        return any(
            pattern in text
            for pattern in academy_patterns
        )

    # =========================================================
    # ANALYSE INTERNET / CODE
    # =========================================================

    def _get_standard_engines(self, text):

        plan = []

        for rule in self.rules:

            engine = rule["engine"]

            if engine in [
                "knowledge",
                "academy"
            ]:
                continue

            if (
                self.available_engines is not None
                and engine not in self.available_engines
            ):
                continue

            matched = any(

                keyword in text

                for keyword in rule["keywords"]

            )

            if matched:

                plan.append(
                    {
                        "engine": engine,

                        "description":
                            f"Utiliser {engine}",

                        "priority":
                            len(plan) + 1
                    }
                )

        return plan

    # =========================================================
    # ANALYSE CONTEXTUELLE
    # =========================================================

    def _conversation_text(
        self,
        conversation
    ):

        if not conversation:
            return ""

        result = ""

        for item in conversation:

            if not isinstance(
                item,
                dict
            ):
                continue

            role = item.get(
                "role",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            if not content:
                continue

            result += (
                f"{role}: {content}\n"
            )

        return self.normalize(
            result
        )

    # =========================================================
    # QUESTION CONTEXTUELLE
    # =========================================================

    def _is_contextual_reference(
        self,
        text
    ):

        contextual_patterns = [

            "et pourquoi",
            "et comment",
            "pourquoi alors",
            "et c est pourquoi",
            "et pourquoi ca",
            "et pourquoi cela",
            "pourquoi ca",
            "pourquoi cela",

            "et ca",
            "et cela",

            "et lui",
            "et elle",

            "et ce dernier",
            "et cette derniere",

            "lequel",
            "laquelle",

            "et alors",
            "et donc",
            "pourquoi donc",

            "et toi pourquoi",
            "et pourquoi ca"
        ]

        return any(
            pattern in text
            for pattern in contextual_patterns
        )

    # =========================================================
    # CONTEXTE KNOWLEDGE
    # =========================================================

    def _context_contains_personal_topic(
        self,
        conversation_text
    ):

        personal_topics = [

            "jeu prefere",
            "jeu préféré",

            "jeux prefere",
            "jeux préféré",

            "jeu favori",

            "moteur prefere",
            "moteur préféré",

            "projet",

            "mon nom",

            "mon prenom",
            "mon prénom",

            "je m appelle",
            "je m'appelle"
        ]

        return any(
            topic in conversation_text
            for topic in personal_topics
        )

    # =========================================================
    # DECISION
    # =========================================================

    def decide(
        self,
        message,
        conversation=None
    ):

        if not isinstance(
            message,
            str
        ):

            raise TypeError(
                "Le message doit être une chaîne."
            )

        text = self.normalize(
            message
        )

        if not text:
            return []

        conversation = (
            conversation or []
        )

        conversation_text = (
            self._conversation_text(
                conversation
            )
        )

        # =====================================================
        # DETECTION PRINCIPALE
        # =====================================================

        is_knowledge = (
            self._is_knowledge_request(
                text
            )
        )

        is_academy = (
            self._is_academy_request(
                text
            )
        )

        is_contextual = (
            self._is_contextual_reference(
                text
            )
        )

        # =====================================================
        # CAS 1
        # QUESTION CONTEXTUELLE
        #
        # "Quel est mon jeu préféré ?"
        # "Et pourquoi ?"
        #
        # => Knowledge doit récupérer la mémoire.
        # =====================================================

        if is_contextual:

            if self._context_contains_personal_topic(
                conversation_text
            ):

                plan = [

                    {
                        "engine": "knowledge",

                        "description":
                            "Récupérer les informations "
                            "personnelles pertinentes "
                            "dans la mémoire d'ARGOS.",

                        "priority": 1
                    }

                ]

                if is_academy:

                    plan.append(
                        {
                            "engine": "academy",

                            "description":
                                "Expliquer la référence personnelle "
                                "à partir du contexte d'ARGOS.",

                            "priority": 2
                        }
                    )

                return plan

        # =====================================================
        # CAS 2
        # KNOWLEDGE + ACADEMY
        #
        # IMPORTANT :
        #
        # Une question comme :
        #
        # "Pourquoi j'aime mon jeu préféré ?"
        #
        # est d'abord une question de mémoire.
        #
        # On ne doit PAS automatiquement envoyer la
        # requête vers Academy simplement parce qu'elle
        # contient "pourquoi".
        # =====================================================

        if is_knowledge:

            plan = [

                {
                    "engine": "knowledge",

                    "description":
                        "Récupérer les informations pertinentes "
                        "dans la mémoire d'ARGOS.",

                    "priority": 1
                }

            ]

            if is_academy:

                plan.append(
                    {
                        "engine": "academy",

                        "description":
                            "Synthétiser l'information personnelle "
                            "dans une réponse pédagogique.",

                        "priority": 2
                    }
                )

            return plan

        # =====================================================
        # CAS 3
        # ACADEMY
        # =====================================================

        plan = self._get_standard_engines(
            text
        )

        # =====================================================
        # CAS 3
        # ACADEMY, SEUL OU APRES UN AUTRE MOTEUR
        # =====================================================

        if is_academy:

            plan.append(
                {
                    "engine": "academy",

                    "description":
                        "Expliquer, enseigner ou analyser "
                        "la demande de l'utilisateur.",

                    "priority": len(plan) + 1
                }
            )

        if plan:
            return plan

        # =====================================================
        # CAS 4
        # DEFAULT
        # =====================================================

        return [

            {
                "engine": "knowledge",

                "description":
                    "Vérifier si la requête peut être "
                    "résolue à partir des connaissances "
                    "et du contexte d'ARGOS.",

                "priority": 1
            }

        ]

    # =========================================================
    # CAPACITES
    # =========================================================

    def capabilities(self):

        return [

            rule["engine"]

            for rule in self.rules

        ]

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "rules":
                len(self.rules),

            "capabilities":
                self.capabilities()

        }

