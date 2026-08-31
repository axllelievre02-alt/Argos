class Executor:
    """
    Exécute les tâches préparées par ARGOS.

    L'Executor ne choisit pas les moteurs.
    Il exécute uniquement les tâches qui lui sont données.

    Le Context est l'espace de travail partagé
    entre les différents moteurs.

    Pipeline :

        Mission
           ↓
        Executor
           ↓
        EngineManager
           ↓
        Engine
           ↓
        Context
    """

    def __init__(self, engine_manager):

        self.engine_manager = engine_manager

    # =========================================================
    # EXECUTION D'UNE MISSION
    # =========================================================

    def execute(
        self,
        mission,
        message,
        conversation=None
    ):
        """
        Exécute toutes les tâches d'une mission.

        Chaque moteur reçoit :

            - message
            - context

        Le résultat est ensuite stocké dans Context.
        """

        from core.context import Context

        # -----------------------------------------------------
        # Création du contexte
        # -----------------------------------------------------

        context = Context(
            conversation=conversation
        )

        # -----------------------------------------------------
        # Message actuel
        # -----------------------------------------------------

        context.set(
            "current_message",
            message
        )

        # -----------------------------------------------------
        # Contexte conversationnel
        # -----------------------------------------------------

        if conversation:

            conversation_context = ""

            for item in conversation:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                role = item.get(
                    "role"
                )

                content = item.get(
                    "content"
                )

                if not content:
                    continue

                if role == "user":

                    conversation_context += (
                        f"Ikaris : {content}\n"
                    )

                elif role == "assistant":

                    conversation_context += (
                        f"ARGOS : {content}\n"
                    )

            context.set(
                "conversation_context",
                conversation_context
            )

        else:

            context.set(
                "conversation_context",
                ""
            )

        # -----------------------------------------------------
        # Debug
        # -----------------------------------------------------

        print(
            "\n===== EXECUTION ARGOS ====="
        )

        # =====================================================
        # EXECUTION DES TACHES
        # =====================================================

        if not hasattr(
            mission,
            "tasks"
        ):

            context.log(
                "Mission invalide : aucune tâche."
            )

            print(
                "❌ Mission invalide."
            )

            print(
                "===========================\n"
            )

            return context

        for task in mission.tasks:

            print(
                f"▶ {task.engine}"
            )

            result = self.execute_task(
                task,
                message,
                context
            )

            if result is None:

                print(
                    f"❌ {task.engine} "
                    "n'a rien retourné."
                )

                continue

            # -------------------------------------------------
            # Sauvegarde du résultat dans Context
            # -------------------------------------------------

            context.set_engine(
                task.engine,
                result
            )

            print(
                f"✅ {task.engine} terminé."
            )

        print(
            "===========================\n"
        )

        return context

    # =========================================================
    # EXECUTION D'UNE TACHE
    # =========================================================

    def execute_task(
        self,
        task,
        message,
        context
    ):
        """
        Exécute une seule tâche.

        L'Executor délègue entièrement l'exécution
        à EngineManager.
        """

        # -----------------------------------------------------
        # Vérification
        # -----------------------------------------------------

        if task is None:

            context.log(
                "Tâche invalide."
            )

            return None

        engine_name = getattr(
            task,
            "engine",
            None
        )

        if not engine_name:

            context.log(
                "Tâche sans moteur."
            )

            return None

        # -----------------------------------------------------
        # Exécution via EngineManager
        # -----------------------------------------------------

        result = self.engine_manager.execute(
            engine_name,
            message,
            context
        )

        # -----------------------------------------------------
        # Échec
        # -----------------------------------------------------

        if result is None:

            try:

                task.failed()

            except Exception as error:

                context.log(
                    f"Impossible de marquer la tâche "
                    f"comme échouée : {error}"
                )

            return None

        # -----------------------------------------------------
        # Succès
        # -----------------------------------------------------

        try:

            task.finish(
                result
            )

        except Exception as error:

            context.log(
                f"Impossible de terminer la tâche "
                f"{engine_name} : {error}"
            )

        return result

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "engine_manager": (
                self.engine_manager.summary()
            )

        }

