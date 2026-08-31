from datetime import datetime


class Context:
    """
    Contexte temporaire d'une requête ARGOS.

    Le Context existe uniquement pendant l'exécution
    d'une requête.

    Il permet aux moteurs de partager :

        - leurs résultats
        - des données temporaires
        - l'historique conversationnel
        - des logs
        - les erreurs rencontrées
    """

    def __init__(self, conversation=None):

        # =====================================================
        # RESULTATS DES MOTEURS
        # =====================================================

        self._engines = {}

        # =====================================================
        # DONNEES PARTAGEES
        # =====================================================

        self._shared = {}

        # =====================================================
        # CONVERSATION
        # =====================================================

        self._conversation = []

        if conversation is not None:

            try:

                self._conversation = list(
                    conversation
                )

            except Exception:

                self._conversation = []

        # =====================================================
        # LOGS
        # =====================================================

        self._logs = []

        # =====================================================
        # ERREURS
        # =====================================================

        self._errors = []

        # =====================================================
        # TEMPS
        # =====================================================

        self.started_at = datetime.now()

    # =========================================================
    # RESULTATS DES MOTEURS
    # =========================================================

    def set_engine(self, engine_name, result):

        self._engines[engine_name] = result

    def get_engine(self, engine_name):

        return self._engines.get(
            engine_name
        )

    def has_engine(self, engine_name):

        return engine_name in self._engines

    def all_engines(self):

        return dict(
            self._engines
        )

    def first_result(self):

        if not self._engines:

            return None

        return next(
            iter(
                self._engines.values()
            )
        )

    def last_result(self):

        if not self._engines:

            return None

        return list(
            self._engines.values()
        )[-1]

    # =========================================================
    # CONVERSATION
    # =========================================================

    def set_conversation(self, conversation):

        if conversation is None:

            self._conversation = []

            return

        try:

            self._conversation = list(
                conversation
            )

        except Exception:

            self._conversation = []

    def get_conversation(self):

        return list(
            self._conversation
        )

    def conversation_count(self):

        return len(
            self._conversation
        )

    def has_conversation(self):

        return len(
            self._conversation
        ) > 0

    def last_conversation_message(self):

        if not self._conversation:

            return None

        return self._conversation[-1]

    # =========================================================
    # DONNEES PARTAGEES
    # =========================================================

    def set(self, key, value):

        self._shared[key] = value

    def get(self, key, default=None):

        return self._shared.get(
            key,
            default
        )

    def has(self, key):

        return key in self._shared

    def remove(self, key):

        self._shared.pop(
            key,
            None
        )

    def clear_shared(self):

        self._shared.clear()

    # =========================================================
    # LOGS
    # =========================================================

    def log(self, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self._logs.append(
            f"[{timestamp}] {message}"
        )

    def get_logs(self):

        return list(
            self._logs
        )

    # =========================================================
    # ERREURS
    # =========================================================

    def add_error(self, error):

        self._errors.append(
            str(error)
        )

    def has_errors(self):

        return len(
            self._errors
        ) > 0

    def get_errors(self):

        return list(
            self._errors
        )

    # =========================================================
    # TEMPS D'EXECUTION
    # =========================================================

    def execution_time(self):

        return datetime.now() - self.started_at

    # =========================================================
    # RESET
    # =========================================================

    def clear(self):

        self._engines.clear()
        self._shared.clear()
        self._conversation.clear()
        self._logs.clear()
        self._errors.clear()

        self.started_at = datetime.now()

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "engines": list(
                self._engines.keys()
            ),

            "shared": list(
                self._shared.keys()
            ),

            "conversation_messages":
                len(self._conversation),

            "logs": len(
                self._logs
            ),

            "errors": len(
                self._errors
            ),

            "execution_time": str(
                self.execution_time()
            )

        }

    # =========================================================
    # EXPORT
    # =========================================================

    def to_dict(self):
        """Exporte le contexte sous une forme sérialisable."""

        return {
            "engine_results": self.all_engines(),
            "shared": dict(self._shared),
            "conversation": self.get_conversation(),
            "logs": self.get_logs(),
            "errors": self.get_errors()
        }