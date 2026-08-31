from core.task import Task


class Mission:
    """
    Représente une mission complète d'ARGOS.

    Une Mission regroupe plusieurs Tasks.

    Elle contient :

        - un objectif
        - une liste de tâches
        - un état
    """

    def __init__(
        self,
        objective,
        tasks=None
    ):

        if not isinstance(objective, str):

            raise TypeError(
                "L'objectif doit être une chaîne."
            )

        objective = objective.strip()

        if not objective:

            raise ValueError(
                "Une mission doit posséder un objectif."
            )

        self.objective = objective

        self.tasks = []

        self.status = "pending"

        if tasks:

            for task in tasks:

                self.add_task(task)

    # =========================================================
    # TACHES
    # =========================================================

    def add_task(self, task):

        if not isinstance(task, Task):

            raise TypeError(
                "Une mission ne peut contenir "
                "que des objets Task."
            )

        self.tasks.append(task)

    def remove_task(self, task):

        if task in self.tasks:

            self.tasks.remove(task)

    def clear_tasks(self):

        self.tasks.clear()

    # =========================================================
    # ETAT
    # =========================================================

    def start(self):

        self.status = "running"

    def complete(self):

        self.status = "completed"

    def failed(self):

        self.status = "failed"

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

            "objective": self.objective,

            "tasks": len(
                self.tasks
            ),

            "status": self.status,

            "completed_tasks": sum(

                task.is_completed()

                for task in self.tasks

            ),

            "failed_tasks": sum(

                task.is_failed()

                for task in self.tasks

            )

        }