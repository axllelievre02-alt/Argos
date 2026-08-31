class BaseEngine:
    """
    Classe de base de tous les moteurs d'ARGOS.

    Tous les moteurs doivent hériter de cette classe.

    Le BaseEngine fournit les propriétés communes :

        - nom
        - capacités
        - priorité
        - activation / désactivation

    Il ne contient aucune logique spécifique à un moteur.
    """

    def __init__(
        self,
        name,
        capabilities=None,
        priority=10
    ):

        # =====================================================
        # IDENTITE
        # =====================================================

        self.name = name

        # =====================================================
        # CAPACITES
        # =====================================================

        if capabilities is None:

            capabilities = []

        self.capabilities = list(
            capabilities
        )

        # =====================================================
        # PRIORITE
        # =====================================================

        self.priority = priority

        # =====================================================
        # ACTIVATION
        # =====================================================

        self.enabled = True

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(self, message, context):
        """
        Méthode que chaque moteur doit implémenter.
        """

        raise NotImplementedError(
            f"Le moteur '{self.name}' "
            "doit implémenter execute()."
        )

    # =========================================================
    # ACTIVATION
    # =========================================================

    def enable(self):

        self.enabled = True

    def disable(self):

        self.enabled = False

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def is_enabled(self):

        return self.enabled

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "name": self.name,

            "capabilities": list(
                self.capabilities
            ),

            "priority": self.priority,

            "enabled": self.enabled

        }