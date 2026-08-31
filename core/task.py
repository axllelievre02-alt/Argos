class Task:
    """
    Représente une tâche individuelle d'ARGOS.

    Une Task indique :

        - quel moteur doit être utilisé
        - pourquoi il doit être utilisé
        - sa priorité
        - son état
        - son résultat
    """

    # =========================================================
    # INITIALISATION
    # =========================================================

    def __init__(
        self,
        engine,
        description="",
        priority=1
    ):

        if not isinstance(engine, str):

            raise TypeError(
                "Le nom du moteur doit être une chaîne."
            )

        engine = engine.strip()

        if not engine:

            raise ValueError(
                "Une tâche doit posséder un moteur."
            )

        self.engine = engine

        self.description = description

        self.priority = priority

        # -----------------------------------------------------
        # Etat
        # -----------------------------------------------------

        self.status = "pending"

        # -----------------------------------------------------
        # Résultat
        # -----------------------------------------------------

        self.result = None

    # =========================================================
    # ETATS
    # =========================================================

    def start(self):

        self.status = "running"

    def finish(self, result=None):

        self.status = "completed"

        self.result = result

    def failed(self, result=None):

        self.status = "failed"

        self.result = result

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def is_pending(self):

        return self.status == "pending"

    def is_running(self):

        return self.status == "running"

    def is_completed(self):

        return self.status == "completed"

    def is_failed(self):

        return self.status == "failed"

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "engine": self.engine,

            "description": self.description,

            "priority": self.priority,

            "status": self.status,

            "has_result": (
                self.result is not None
            )

        }