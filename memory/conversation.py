class ConversationMemory:
    """
    Gère l'historique de la conversation actuelle d'ARGOS.

    Cette classe conserve les messages de la session
    et fournit des méthodes permettant aux autres systèmes
    d'exploiter le contexte conversationnel.
    """

    def __init__(self, max_messages=50):

        self.max_messages = max_messages

        self._messages = []

    # =========================================================
    # AJOUT DE MESSAGES
    # =========================================================

    def add_user_message(self, message):
        """
        Ajoute un message utilisateur.
        """

        self._messages.append(
            {
                "role": "user",
                "content": str(message)
            }
        )

        self._limit_history()

    def add_assistant_message(self, message):
        """
        Ajoute une réponse d'ARGOS.
        """

        self._messages.append(
            {
                "role": "assistant",
                "content": str(message)
            }
        )

        self._limit_history()

    # =========================================================
    # LECTURE
    # =========================================================

    def get_messages(self):
        """
        Retourne une copie complète de l'historique.
        """

        return list(
            self._messages
        )

    def get_last_message(self):
        """
        Retourne le dernier message.
        """

        if not self._messages:

            return None

        return self._messages[-1]

    def get_last_user_message(self):
        """
        Retourne le dernier message envoyé par l'utilisateur.
        """

        for message in reversed(
            self._messages
        ):

            if message["role"] == "user":

                return message

        return None

    def get_last_assistant_message(self):
        """
        Retourne la dernière réponse d'ARGOS.
        """

        for message in reversed(
            self._messages
        ):

            if message["role"] == "assistant":

                return message

        return None

    # =========================================================
    # PAIRES DE CONVERSATION
    # =========================================================

    def get_last_exchange(self):
        """
        Retourne le dernier échange complet :

            {
                "user": "...",
                "assistant": "..."
            }

        Retourne None si aucun échange complet n'existe.
        """

        assistant = self.get_last_assistant_message()

        if assistant is None:

            return None

        assistant_index = None

        for index in range(
            len(self._messages) - 1,
            -1,
            -1
        ):

            if self._messages[index] is assistant:

                assistant_index = index

                break

        if assistant_index is None:

            return None

        for index in range(
            assistant_index - 1,
            -1,
            -1
        ):

            message = self._messages[index]

            if message["role"] == "user":

                return {
                    "user": message["content"],
                    "assistant": assistant["content"]
                }

        return None

    # =========================================================
    # CONTEXTE RECENT
    # =========================================================

    def get_recent_messages(self, count=6):
        """
        Retourne les derniers messages de la conversation.

        Permet aux moteurs de ne pas devoir traiter
        toute la conversation.
        """

        if count <= 0:

            return []

        return list(
            self._messages[-count:]
        )

    def get_recent_context(self, count=6):
        """
        Transforme les derniers messages en texte exploitable
        par un moteur ou un modèle.
        """

        messages = self.get_recent_messages(
            count
        )

        if not messages:

            return ""

        lines = []

        for message in messages:

            role = message["role"]

            content = message["content"]

            if role == "user":

                lines.append(
                    f"Ikaris : {content}"
                )

            elif role == "assistant":

                lines.append(
                    f"ARGOS : {content}"
                )

        return "\n".join(
            lines
        )

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def count(self):

        return len(
            self._messages
        )

    def is_empty(self):

        return len(
            self._messages
        ) == 0

    # =========================================================
    # RECHERCHE
    # =========================================================

    def contains(self, text):
        """
        Vérifie si un texte apparaît dans l'historique.
        """

        if not isinstance(
            text,
            str
        ):

            return False

        text = text.lower()

        for message in self._messages:

            content = message["content"].lower()

            if text in content:

                return True

        return False

    def find_messages(self, text):
        """
        Retourne les messages contenant un texte donné.
        """

        if not isinstance(
            text,
            str
        ):

            return []

        text = text.lower()

        results = []

        for message in self._messages:

            if text in message["content"].lower():

                results.append(
                    dict(message)
                )

        return results

    # =========================================================
    # GESTION DE L'HISTORIQUE
    # =========================================================

    def clear(self):

        self._messages.clear()

    def _limit_history(self):

        if self.max_messages <= 0:

            self._messages.clear()

            return

        if len(self._messages) > self.max_messages:

            self._messages = (
                self._messages[
                    -self.max_messages:
                ]
            )

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {
            "messages": self.count(),
            "max_messages": self.max_messages,
            "empty": self.is_empty(),
            "last_message":
                self.get_last_message(),
            "last_exchange":
                self.get_last_exchange()
        }