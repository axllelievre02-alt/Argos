class MemoryExtractor:
    """
    Détecte les informations importantes dans les messages
    de l'utilisateur.

    MemoryExtractor ne sauvegarde rien lui-même.
    Il détecte uniquement les informations.

    Il peut également utiliser l'historique de conversation
    afin de comprendre certaines réponses contextuelles.
    """

    def __init__(self):

        self.rules = [

            # =================================================
            # JEU PREFERE
            # =================================================

            {
                "key": "favorite_game",
                "patterns": [
                    "mon jeu préféré est",
                    "mon jeu prefere est",
                    "mon jeu préféré c'est",
                    "mon jeu prefere c'est"
                ]
            },

            # =================================================
            # RAISON DU JEU PREFERE
            # =================================================

            {
                "key": "favorite_game_reason",
                "patterns": [
                    "parce que",
                    "car",
                    "je l'aime parce que",
                    "je l'adore parce que",
                    "j'aime ce jeu parce que",
                    "j'adore ce jeu parce que",
                    "je préfère ce jeu parce que"
                ]
            },

            # =================================================
            # MOTEUR PREFERE
            # =================================================

            {
                "key": "favorite_engine",
                "patterns": [
                    "mon moteur préféré est",
                    "mon moteur prefere est",
                    "mon moteur préféré c'est",
                    "mon moteur prefere c'est"
                ]
            },

            # =================================================
            # PROJET ACTUEL
            # =================================================

            {
                "key": "current_project",
                "patterns": [
                    "mon projet est",
                    "mon projet actuel est",
                    "je travaille sur",
                    "je travaille actuellement sur"
                ]
            }
        ]

    # =========================================================
    # EXTRACTION
    # =========================================================

    def extract(
        self,
        message,
        conversation=None
    ):

        if not isinstance(message, str):

            return None

        message = message.strip()

        if not message:

            return None

        if conversation is None:

            conversation = []

        text = message.lower()

        # =====================================================
        # QUESTIONS
        # =====================================================

        question_markers = [

            "?",
            "quel est",
            "quelle est",
            "quels sont",
            "quelles sont",
            "c'est quoi",
            "qui est",
            "pourquoi",
            "comment",
            "que sais-tu",
            "que sais tu",
            "est-ce que"

        ]

        for marker in question_markers:

            if marker in text:

                return None

        # =====================================================
        # JEU PREFERE
        # =====================================================

        patterns = [

            "mon jeu préféré est",
            "mon jeu prefere est",
            "mon jeu préféré c'est",
            "mon jeu prefere c'est"

        ]

        result = self._extract_after_patterns(
            message,
            text,
            patterns
        )

        if result:

            return {

                "type": "profile",

                "key": "favorite_game",

                "value": result

            }

        # =====================================================
        # MOTEUR PREFERE
        # =====================================================

        patterns = [

            "mon moteur préféré est",
            "mon moteur prefere est",
            "mon moteur préféré c'est",
            "mon moteur prefere c'est"

        ]

        result = self._extract_after_patterns(
            message,
            text,
            patterns
        )

        if result:

            return {

                "type": "profile",

                "key": "favorite_engine",

                "value": result

            }

        # =====================================================
        # PROJET
        # =====================================================

        patterns = [

            "mon projet est",
            "mon projet actuel est",
            "je travaille sur",
            "je travaille actuellement sur"

        ]

        result = self._extract_after_patterns(
            message,
            text,
            patterns
        )

        if result:

            return {

                "type": "profile",

                "key": "current_project",

                "value": result

            }

        # =====================================================
        # RAISON DU JEU
        # =====================================================

        patterns = [

            "je l'aime parce que",
            "je l'adore parce que",
            "j'aime ce jeu parce que",
            "j'adore ce jeu parce que",
            "je préfère ce jeu parce que"

        ]

        result = self._extract_after_patterns(
            message,
            text,
            patterns
        )

        if result:

            return {

                "type": "profile",

                "key": "favorite_game_reason",

                "value": result

            }

        # =====================================================
        # REPONSE CONTEXTUELLE
        # =====================================================

        contextual_result = self._extract_contextual_reason(
            message,
            conversation
        )

        if contextual_result:

            return contextual_result

        # =====================================================
        # AUCUNE INFORMATION
        # =====================================================

        return None

    # =========================================================
    # RAISON CONTEXTUELLE
    # =========================================================

    def _extract_contextual_reason(
        self,
        message,
        conversation
    ):
        """
        Détermine si le message actuel est probablement
        une réponse à une question précédente concernant
        le jeu préféré.

        Exemple :

            ARGOS :
            Pourquoi aimes-tu ton jeu préféré ?

            Ikaris :
            Parce que j'adore son univers.

        devient :

            favorite_game_reason =
            "j'adore son univers"
        """

        if not isinstance(
            conversation,
            list
        ):

            return None

        if not conversation:

            return None

        text = message.lower().strip()

        # -----------------------------------------------------
        # Réponse commençant par une formulation contextuelle
        # -----------------------------------------------------

        contextual_patterns = [

            "parce que",
            "car",
            "j'aime",
            "j'adore",
            "je préfère",
            "je l'aime",
            "je l'adore"

        ]

        starts_contextually = False

        for pattern in contextual_patterns:

            if text.startswith(pattern):

                starts_contextually = True

                break

        if not starts_contextually:

            return None

        # -----------------------------------------------------
        # Recherche de la dernière question pertinente
        # -----------------------------------------------------

        recent_messages = conversation[-6:]

        for item in reversed(
            recent_messages
        ):

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

            if role != "user":

                continue

            if not isinstance(
                content,
                str
            ):

                continue

            previous_text = (
                content.lower().strip()
            )

            # -------------------------------------------------
            # Question sur le jeu préféré
            # -------------------------------------------------

            game_question_patterns = [

                "pourquoi j'aime mon jeu préféré",
                "pourquoi j'aime mon jeu prefere",
                "pourquoi j aime mon jeu préféré",
                "pourquoi j aime mon jeu prefere",
                "pourquoi j'adore mon jeu préféré",
                "pourquoi j'adore mon jeu prefere",
                "pourquoi j adore mon jeu préféré",
                "pourquoi j adore mon jeu prefere",
                "pourquoi j'aime ce jeu",
                "pourquoi j aime ce jeu",
                "pourquoi j'adore ce jeu",
                "pourquoi j adore ce jeu",
                "pourquoi j'aime",
                "pourquoi j aime",
                "pourquoi j'adore",
                "pourquoi j adore"

            ]

            relevant_question = any(

                pattern in previous_text

                for pattern
                in game_question_patterns

            )

            if relevant_question:

                return {

                    "type": "profile",

                    "key":
                        "favorite_game_reason",

                    "value":
                        self._clean(message)

                }

        return None

    # =========================================================
    # EXTRACTION APRES UN PATTERN
    # =========================================================

    def _extract_after_patterns(
        self,
        original,
        text,
        patterns
    ):

        for pattern in patterns:

            index = text.find(
                pattern
            )

            if index == -1:

                continue

            value = original[
                index + len(pattern):
            ].strip()

            value = self._clean(
                value
            )

            if value:

                return value

        return None

    # =========================================================
    # NETTOYAGE
    # =========================================================

    def _clean(
        self,
        value
    ):

        value = value.strip()

        value = value.rstrip(
            ".!?"
        )

        value = value.strip()

        return value

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "rules":
                len(self.rules),

            "contextual_memory":
                True

        }