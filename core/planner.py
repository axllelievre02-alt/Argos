class Planner:
    """
    Prépare une Mission avant son exécution.

    Le Planner ne choisit pas les moteurs.
    Il ne crée pas de nouvelles tâches.

    Son rôle est uniquement d'organiser
    la mission reçue.

    Pipeline :

        Prometheus
             ↓
        MissionBuilder
             ↓
        Planner
             ↓
        Executor
    """

    def __init__(self):

        self.last_plan = None

    # =========================================================
    # PREPARATION
    # =========================================================

    def prepare(self, mission):
        """
        Prépare une mission avant exécution.

        Le Planner :
            - vérifie la mission
            - trie les tâches
            - mémorise la mission
        """

        if mission is None:

            raise ValueError(
                "Impossible de préparer une mission vide."
            )

        # -----------------------------------------------------
        # Vérification de la structure
        # -----------------------------------------------------

        if not hasattr(
            mission,
            "tasks"
        ):

            raise TypeError(
                "L'objet fourni n'est pas une Mission valide."
            )

        if mission.tasks is None:

            mission.tasks = []

        # -----------------------------------------------------
        # Tri des tâches par priorité
        # -----------------------------------------------------

        mission.tasks.sort(
            key=lambda task: getattr(
                task,
                "priority",
                999
            )
        )

        # -----------------------------------------------------
        # Sauvegarde
        # -----------------------------------------------------

        self.last_plan = mission

        return mission

    # =========================================================
    # AFFICHAGE
    # =========================================================

    def display(self, mission):

        print(
            "\n===== PLAN D'ACTION ====="
        )

        print(
            f"Objectif : {mission.objective}\n"
        )

        if not mission.tasks:

            print(
                "Aucune tâche."
            )

        for task in mission.tasks:

            priority = getattr(
                task,
                "priority",
                "?"
            )

            engine = getattr(
                task,
                "engine",
                "inconnu"
            )

            description = getattr(
                task,
                "description",
                ""
            )

            print(
                f"{priority}. "
                f"{engine}"
            )

            if description:

                print(
                    f"   ↳ {description}"
                )

        print(
            "=========================\n"
        )

    # =========================================================
    # PIPELINE
    # =========================================================

    def execute(self, mission):
        """
        Prépare puis affiche la mission.
        """

        mission = self.prepare(
            mission
        )

        self.display(
            mission
        )

        return mission

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        if self.last_plan is None:

            return None

        return {

            "objective":
                self.last_plan.objective,

            "tasks":
                len(
                    self.last_plan.tasks
                ),

            "status":
                getattr(
                    self.last_plan,
                    "status",
                    None
                )

        }

