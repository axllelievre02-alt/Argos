class Prometheus:
    """
    Centre de décision d'ARGOS.

    Prometheus reçoit l'analyse produite par TaskAnalyzer
    et décide quels moteurs sont nécessaires.

    Prometheus ne fait PAS exécuter les moteurs.

    Pipeline :

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

    def __init__(self, available_engines=None):

        self.available_engines = list(
            available_engines or []
        )

        self.last_plan = None

    # =========================================================
    # DECISION
    # =========================================================

    def decide(
        self,
        analysis,
        conversation=None
    ):
        """
        Détermine les moteurs nécessaires à partir
        de l'analyse produite par TaskAnalyzer.

        Paramètres :

            analysis :
                dictionnaire produit par TaskAnalyzer.

            conversation :
                historique conversationnel éventuel.

        Retourne :

            une liste de tâches destinée au MissionBuilder.
        """

        # -----------------------------------------------------
        # Vérification
        # -----------------------------------------------------

        if not isinstance(
            analysis,
            dict
        ):

            raise TypeError(
                "L'analyse doit être un dictionnaire."
            )

        # -----------------------------------------------------
        # Récupération des informations
        # -----------------------------------------------------

        intent = analysis.get(
            "intent",
            "general"
        )

        goal = analysis.get(
            "goal",
            ""
        )

        message = analysis.get(
            "normalized_message",
            ""
        )

        signals = analysis.get(
            "signals",
            {}
        )

        has_conversation = bool(
            conversation
        )

        # -----------------------------------------------------
        # Liste des tâches
        # -----------------------------------------------------

        tasks = []

        # =====================================================
        # CONNAISSANCE PERSONNELLE
        # =====================================================

        if intent == "knowledge":

            if self._engine_available(
                "knowledge"
            ):

                tasks.append(
                    {
                        "engine": "knowledge",

                        "description": (
                            "Récupérer les informations "
                            "pertinentes dans la mémoire "
                            "d'ARGOS."
                        ),

                        "priority": 1
                    }
                )

        # =====================================================
        # INTERNET
        # =====================================================

        elif intent == "internet":

            if self._engine_available(
                "internet"
            ):

                tasks.append(
                    {
                        "engine": "internet",

                        "description": (
                            "Rechercher sur Internet "
                            "les informations actuelles "
                            "nécessaires pour répondre."
                        ),

                        "priority": 1
                    }
                )

        # =====================================================
        # CODE
        # =====================================================

        elif intent == "code":

            if self._engine_available(
                "code"
            ):

                tasks.append(
                    {
                        "engine": "code",

                        "description": (
                            "Analyser ou produire "
                            "du code selon la demande."
                        ),

                        "priority": 1
                    }
                )

        # =====================================================
        # ACADEMIE
        # =====================================================

        elif intent == "academy":

            # -------------------------------------------------
            # Demande contextuelle avec historique
            # -------------------------------------------------

            if (
                signals.get("contextual", False)
                and has_conversation
            ):

                # -------------------------------------------------
                # Vérifie si le contexte précédent est personnel.
                #
                # Exemple personnel :
                #
                #   Quel est mon jeu préféré ?
                #   Et pourquoi ?
                #
                # Dans ce cas :
                #
                #   knowledge
                #        ↓
                #   academy
                #
                # -------------------------------------------------

                personal_context = (
                    self._conversation_is_personal(
                        conversation
                    )
                )

                # -------------------------------------------------
                # CONTEXTE PERSONNEL
                # -------------------------------------------------

                if personal_context:

                    if self._engine_available(
                        "knowledge"
                    ):

                        tasks.append(
                            {
                                "engine": "knowledge",

                                "description": (
                                    "Récupérer les informations "
                                    "personnelles nécessaires "
                                    "à partir de la mémoire."
                                ),

                                "priority": 1
                            }
                        )

                    if self._engine_available(
                        "academy"
                    ):

                        tasks.append(
                            {
                                "engine": "academy",

                                "description": (
                                    "Interpréter et expliquer "
                                    "la demande à partir du "
                                    "contexte conversationnel "
                                    "et des résultats précédents."
                                ),

                                "priority": 2
                            }
                        )

                # -------------------------------------------------
                # CONTEXTE GENERAL
                #
                # Exemple :
                #
                #   Explique-moi ce qu'est Unreal Engine.
                #   Et pourquoi ?
                #
                # Dans ce cas, aucun KnowledgeEngine.
                # -------------------------------------------------

                else:

                    if self._engine_available(
                        "academy"
                    ):

                        tasks.append(
                            {
                                "engine": "academy",

                                "description": (
                                    "Interpréter la demande "
                                    "à partir du contexte "
                                    "conversationnel et "
                                    "produire une explication."
                                ),

                                "priority": 1
                            }
                        )

            # -------------------------------------------------
            # Demande d'explication normale
            # -------------------------------------------------

            else:

                if self._engine_available(
                    "academy"
                ):

                    tasks.append(
                        {
                            "engine": "academy",

                            "description": (
                                "Expliquer, enseigner ou "
                                "analyser la demande "
                                "de manière pédagogique."
                            ),

                            "priority": 1
                        }
                    )

        # =====================================================
        # DEMANDE CONTEXTUELLE
        # =====================================================

        elif intent == "contextual":

            if has_conversation:

                # -------------------------------------------------
                # Détermine si le contexte est personnel.
                # -------------------------------------------------

                personal_context = (
                    self._conversation_is_personal(
                        conversation
                    )
                )

                # -------------------------------------------------
                # CONTEXTE PERSONNEL
                # -------------------------------------------------

                if personal_context:

                    if self._engine_available(
                        "knowledge"
                    ):

                        tasks.append(
                            {
                                "engine": "knowledge",

                                "description": (
                                    "Récupérer les informations "
                                    "pertinentes dans la mémoire "
                                    "d'ARGOS."
                                ),

                                "priority": 1
                            }
                        )

                    if self._engine_available(
                        "academy"
                    ):

                        tasks.append(
                            {
                                "engine": "academy",

                                "description": (
                                    "Interpréter la demande "
                                    "à partir du contexte "
                                    "conversationnel."
                                ),

                                "priority": 2
                            }
                        )

                # -------------------------------------------------
                # CONTEXTE GENERAL
                # -------------------------------------------------

                else:

                    if self._engine_available(
                        "academy"
                    ):

                        tasks.append(
                            {
                                "engine": "academy",

                                "description": (
                                    "Interpréter la demande "
                                    "à partir du contexte "
                                    "conversationnel."
                                ),

                                "priority": 1
                            }
                        )

        # =====================================================
        # DEMANDE GENERALE
        # =====================================================

        elif intent == "general":

            # -------------------------------------------------
            # Une demande générale ne force aucun moteur.
            #
            # Le ResponseManager pourra répondre directement.
            # -------------------------------------------------

            pass

        # =====================================================
        # PLAN
        # =====================================================

        self.last_plan = {
            "goal": goal,
            "message": message,
            "tasks": tasks
        }

        # =====================================================
        # DEBUG
        # =====================================================

        print(
            "\n===== PLAN D'ACTION ====="
        )

        print(
            "Objectif :",
            goal or "Traiter la requête utilisateur."
        )

        if not tasks:

            print(
                "Aucun moteur spécialisé sélectionné."
            )

        else:

            for index, task in enumerate(
                tasks,
                start=1
            ):

                print(
                    f"{index}. "
                    f"{task['engine']}"
                )

                print(
                    f"   ↳ "
                    f"{task['description']}"
                )

                print(
                    f"   Priorité : "
                    f"{task['priority']}"
                )

        print(
            "=========================\n"
        )

        return tasks

    # =========================================================
    # ANALYSE DU CONTEXTE CONVERSATIONNEL
    # =========================================================

    def _conversation_is_personal(
        self,
        conversation
    ):
        """
        Détermine si le contexte récent concerne
        une information personnelle mémorisable.

        Cette méthode ne décide pas du moteur.
        Elle sert uniquement à savoir si KnowledgeEngine
        est nécessaire lorsqu'une demande est contextuelle.

        Exemples personnels :

            Quel est mon jeu préféré ?
            Quel est mon moteur préféré ?
            Quel est mon projet ?
            Quel est mon nom ?

        Exemples non personnels :

            Explique-moi Unreal Engine.
            Quelle est la dernière version d'Unreal Engine ?
            Pourquoi Unreal Engine est-il utilisé ?
        """

        if not isinstance(
            conversation,
            list
        ):

            return False

        if not conversation:

            return False

        # -----------------------------------------------------
        # On examine les derniers messages utilisateur.
        # -----------------------------------------------------

        recent_messages = conversation[-8:]

        personal_patterns = [

            # Identité
            "quel est mon nom",
            "quel est mon prénom",
            "quel est mon prenom",
            "comment je m'appelle",
            "comment je m appelle",
            "qui suis-je",
            "qui suis je",

            # Jeu préféré
            "quel est mon jeu préféré",
            "quel est mon jeu prefere",
            "quel est mon jeu favori",
            "quel est mon jeu favoris",
            "mon jeu préféré",
            "mon jeu prefere",
            "mon jeu favori",

            # Moteur préféré
            "quel est mon moteur préféré",
            "quel est mon moteur prefere",
            "quel est mon moteur favori",
            "mon moteur préféré",
            "mon moteur prefere",
            "mon moteur favori",

            # Projet
            "quel est mon projet",
            "quel est mon projet actuel",
            "mon projet",
            "mon projet actuel",
            "sur quel projet je travaille",
            "sur quoi je travaille",

            # Informations personnelles
            "mes informations",
            "mes préférences",
            "mes preferences",
            "sur moi",

        ]

        # -----------------------------------------------------
        # Parcours inverse :
        # on cherche d'abord le dernier sujet personnel.
        # -----------------------------------------------------

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

            text = content.lower().strip()

            # -------------------------------------------------
            # Question contextuelle elle-même
            #
            # "Et pourquoi ?" ne permet pas de déterminer
            # le sujet. On continue donc vers le message
            # utilisateur précédent.
            # -------------------------------------------------

            if self._is_contextual_message(
                text
            ):

                continue

            # -------------------------------------------------
            # Vérification sujet personnel
            # -------------------------------------------------

            for pattern in personal_patterns:

                if pattern in text:

                    return True

            # -------------------------------------------------
            # Si le dernier vrai message utilisateur n'est
            # pas personnel, le contexte n'est pas considéré
            # comme personnel.
            # -------------------------------------------------

            return False

        return False

    # =========================================================
    # MESSAGE CONTEXTUEL
    # =========================================================

    def _is_contextual_message(
        self,
        text
    ):
        """
        Détermine si un message est une courte demande
        dépendant probablement du message précédent.
        """

        if not isinstance(
            text,
            str
        ):

            return False

        text = text.strip().lower()

        contextual_patterns = [

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
            "cette derniere",
            "pourquoi ?",
            "pourquoi?",
            "comment ?",
            "comment?"

        ]

        for pattern in contextual_patterns:

            if pattern in text:

                return True

        return False

    # =========================================================
    # MOTEUR DISPONIBLE
    # =========================================================

    def _engine_available(
        self,
        name
    ):
        """
        Vérifie qu'un moteur est disponible.
        """

        return name in self.available_engines

    # =========================================================
    # MISE A JOUR DES MOTEURS
    # =========================================================

    def set_available_engines(
        self,
        engines
    ):
        """
        Remplace la liste des moteurs disponibles.
        """

        if engines is None:

            self.available_engines = []

            return

        self.available_engines = list(
            engines
        )

    # =========================================================
    # AJOUT D'UN MOTEUR
    # =========================================================

    def add_engine(
        self,
        name
    ):
        """
        Ajoute un moteur disponible.
        """

        if name not in self.available_engines:

            self.available_engines.append(
                name
            )

    # =========================================================
    # SUPPRESSION D'UN MOTEUR
    # =========================================================

    def remove_engine(
        self,
        name
    ):
        """
        Retire un moteur disponible.
        """

        if name in self.available_engines:

            self.available_engines.remove(
                name
            )

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def summary(self):

        return {
            "available_engines":
                list(
                    self.available_engines
                ),

            "last_plan":
                self.last_plan
        }