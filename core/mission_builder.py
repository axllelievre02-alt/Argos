from core.mission import Mission
from core.task import Task


class MissionBuilder:
    """
    Construit une Mission à partir d'un plan.

    Le MissionBuilder ne décide jamais quel moteur utiliser.
    Cette décision appartient à Prometheus.

    Son rôle est uniquement de transformer :

        Plan
          ↓
        Mission
          ↓
        Tasks

    Exemple de plan :

        [
            {
                "engine": "knowledge",
                "description": "Récupérer une information personnelle.",
                "priority": 1
            }
        ]

    devient :

        Mission
            └── Task("knowledge")
    """

    # =========================================================
    # CONSTRUCTION
    # =========================================================

    def build(self, plan):
        """
        Transforme un plan Prometheus en Mission.
        """

        # -----------------------------------------------------
        # Vérification du plan
        # -----------------------------------------------------

        if not isinstance(
            plan,
            list
        ):

            raise TypeError(
                "Le plan doit être une liste."
            )

        if not plan:

            raise ValueError(
                "Impossible de construire une mission vide."
            )

        # -----------------------------------------------------
        # Création de la mission
        # -----------------------------------------------------

        objective = (
            "Traiter la requête utilisateur."
        )

        mission = Mission(
            objective
        )

        # =====================================================
        # CREATION DES TACHES
        # =====================================================

        for index, item in enumerate(
            plan,
            start=1
        ):

            # -------------------------------------------------
            # Vérification de l'élément
            # -------------------------------------------------

            if not isinstance(
                item,
                dict
            ):

                raise TypeError(
                    "Chaque élément du plan doit être "
                    "un dictionnaire."
                )

            # -------------------------------------------------
            # Moteur
            # -------------------------------------------------

            engine = item.get(
                "engine"
            )

            if not isinstance(
                engine,
                str
            ) or not engine.strip():

                raise ValueError(
                    f"La tâche {index} ne possède "
                    "pas de moteur valide."
                )

            engine = engine.strip()

            # -------------------------------------------------
            # Description
            # -------------------------------------------------

            description = item.get(
                "description",
                ""
            )

            if description is None:

                description = ""

            if not isinstance(
                description,
                str
            ):

                description = str(
                    description
                )

            # -------------------------------------------------
            # Priorité
            # -------------------------------------------------

            priority = item.get(
                "priority",
                index
            )

            if not isinstance(
                priority,
                int
            ):

                priority = index

            # -------------------------------------------------
            # Création de la tâche
            # -------------------------------------------------

            task = Task(

                engine=engine,

                description=description,

                priority=priority

            )

            # -------------------------------------------------
            # Ajout à la mission
            # -------------------------------------------------

            mission.add_task(
                task
            )

        # =====================================================
        # RETOUR
        # =====================================================

        return mission

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(
        self,
        mission
    ):
        """
        Retourne un résumé de la mission.
        """

        if not isinstance(
            mission,
            Mission
        ):

            raise TypeError(
                "L'objet fourni doit être une Mission."
            )

        return mission.summary()

