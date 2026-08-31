from core.base_engine import BaseEngine


class EngineManager:
    """
    Gestionnaire central des moteurs d'ARGOS.

    Le Brain ne communique pas directement avec les moteurs.
    Il passe par cette classe.

    Responsabilités :

        - enregistrer un moteur
        - supprimer un moteur
        - récupérer un moteur
        - exécuter un moteur
        - activer / désactiver un moteur
        - rechercher des moteurs par capacité
    """

    def __init__(self):

        self.engines = {}

    # =========================================================
    # ENREGISTREMENT
    # =========================================================

    def register(self, engine):

        if not isinstance(engine, BaseEngine):

            raise TypeError(
                "Un moteur doit hériter de BaseEngine."
            )

        self.engines[engine.name] = engine

    def unregister(self, name):

        self.engines.pop(
            name,
            None
        )

    # =========================================================
    # RECUPERATION
    # =========================================================

    def get(self, name):

        return self.engines.get(
            name
        )

    def exists(self, name):

        return name in self.engines

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(
        self,
        name,
        message,
        context
    ):

        engine = self.get(name)

        if engine is None:

            context.log(
                f"Moteur inconnu : {name}"
            )

            return None

        if not engine.enabled:

            context.log(
                f"Moteur désactivé : {name}"
            )

            return None

        try:

            result = engine.execute(
                message,
                context
            )

            return result

        except Exception as error:

            context.add_error(
                f"{name} : {error}"
            )

            context.log(
                f"Erreur dans {name} : {error}"
            )

            return None

    # =========================================================
    # ACTIVATION
    # =========================================================

    def enable(self, name):

        engine = self.get(
            name
        )

        if engine:

            engine.enable()

            return True

        return False

    def disable(self, name):

        engine = self.get(
            name
        )

        if engine:

            engine.disable()

            return True

        return False

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def names(self):

        return list(
            self.engines.keys()
        )

    def all(self):

        return dict(
            self.engines
        )

    def capabilities(self):

        return {

            name: list(
                engine.capabilities
            )

            for name, engine
            in self.engines.items()

        }

    # =========================================================
    # RECHERCHE
    # =========================================================

    def find_engines(self, capability):

        return [

            engine

            for engine
            in self.engines.values()

            if capability
            in engine.capabilities

        ]

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            name: engine.summary()

            for name, engine
            in self.engines.items()

        }

