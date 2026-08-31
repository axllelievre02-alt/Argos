from ollama import chat

from core.prompt_builder import PromptBuilder


class ResponseManager:
    """
    Gère la génération des réponses d'ARGOS.

    Responsabilités :

        - communiquer avec le modèle Ollama
        - construire le prompt système
        - utiliser la mémoire de conversation
        - intégrer les résultats des moteurs ARGOS
        - permettre aux moteurs de fournir un contexte précis
        - sauvegarder les échanges dans ConversationMemory

    Le modèle n'est qu'un outil utilisé par ARGOS.
    """

    def __init__(
        self,
        profile,
        conversation,
        model="qwen3:4b"
    ):

        # =====================================================
        # MEMOIRES
        # =====================================================

        self.profile = profile
        self.conversation = conversation

        # =====================================================
        # MODELE
        # =====================================================

        self.model = model

        # =====================================================
        # PROMPT
        # =====================================================

        self.prompt_builder = PromptBuilder(
            self.profile
        )

    # =========================================================
    # GENERATION GENERALE
    # =========================================================

    def generate(self, message):
        """
        Génère une réponse classique avec Qwen.
        """

        if not isinstance(message, str):

            raise TypeError(
                "Le message doit être une chaîne de caractères."
            )

        message = message.strip()

        if not message:
            return ""

        # =====================================================
        # MESSAGE UTILISATEUR
        # =====================================================

        self.conversation.add_user_message(
            message
        )

        # =====================================================
        # PROMPT SYSTEME
        # =====================================================

        system_prompt = (
            self.prompt_builder.build()
        )

        # =====================================================
        # MESSAGES
        # =====================================================

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(
            self.conversation.get_messages()
        )

        # =====================================================
        # MODELE
        # =====================================================

        try:

            response = chat(
                model=self.model,
                messages=messages
            )

        except Exception as error:

            self._remove_last_user_message()

            raise RuntimeError(
                f"Impossible de contacter le modèle "
                f"'{self.model}' : {error}"
            ) from error

        # =====================================================
        # REPONSE
        # =====================================================

        answer = self._extract_answer(
            response
        )

        # =====================================================
        # MEMOIRE
        # =====================================================

        self.conversation.add_assistant_message(
            answer
        )

        return answer

    # =========================================================
    # GENERATION AVEC CONTEXTE ARGOS
    # =========================================================

    def generate_with_context(
        self,
        message,
        context
    ):
        """
        Génère une réponse avec le contexte fourni
        par les moteurs ARGOS.

        Le contexte peut être :

            - un dictionnaire
            - une chaîne de caractères
            - un résultat de moteur
            - plusieurs résultats de moteurs
        """

        if not isinstance(message, str):

            raise TypeError(
                "Le message doit être une chaîne de caractères."
            )

        message = message.strip()

        if not message:
            return ""

        # =====================================================
        # MESSAGE UTILISATEUR
        # =====================================================

        self.conversation.add_user_message(
            message
        )

        # =====================================================
        # PROMPT SYSTEME
        # =====================================================

        system_prompt = (
            self.prompt_builder.build()
        )

        # =====================================================
        # CONTEXTE ARGOS
        # =====================================================

        if context:

            context_text = self._format_context(
                context
            )

            system_prompt += (

                "\n\n"
                "================================================\n"
                "CONTEXTE FOURNI PAR ARGOS\n"
                "================================================\n\n"

                f"{context_text}\n\n"

                "IMPORTANT :\n"
                "Les informations fournies par ARGOS sont "
                "prioritaires pour répondre à la demande.\n"
                "Utilise-les lorsque cela est pertinent.\n"
                "N'invente pas de faits personnels absents "
                "du contexte.\n"

            )

        # =====================================================
        # MESSAGES
        # =====================================================

        messages = [

            {
                "role": "system",
                "content": system_prompt
            }

        ]

        messages.extend(
            self.conversation.get_messages()
        )

        # =====================================================
        # MODELE
        # =====================================================

        try:

            response = chat(

                model=self.model,

                messages=messages

            )

        except Exception as error:

            self._remove_last_user_message()

            raise RuntimeError(
                f"Impossible de contacter le modèle "
                f"'{self.model}' : {error}"
            ) from error

        # =====================================================
        # REPONSE
        # =====================================================

        answer = self._extract_answer(
            response
        )

        # =====================================================
        # MEMOIRE
        # =====================================================

        self.conversation.add_assistant_message(
            answer
        )

        return answer

    # =========================================================
    # EXTRACTION REPONSE MODELE
    # =========================================================

    def _extract_answer(self, response):
        """
        Extrait proprement le texte retourné par Ollama.
        """

        try:

            answer = response["message"]["content"]

        except (
            KeyError,
            TypeError
        ) as error:

            raise RuntimeError(
                "Le modèle a renvoyé une réponse invalide."
            ) from error

        answer = str(answer).strip()

        if not answer:

            raise RuntimeError(
                "Le modèle a renvoyé une réponse vide."
            )

        return answer

    # =========================================================
    # FORMATAGE DU CONTEXTE
    # =========================================================

    def _format_context(self, context):
        """
        Transforme différents types de contexte en texte
        exploitable par le modèle.
        """

        # -----------------------------------------------------
        # Context ARGOS
        # -----------------------------------------------------

        # On utilise l'interface publique de Context plutôt que
        # sa représentation Python par défaut.

        if hasattr(context, "to_dict"):

            return self._format_context(
                context.to_dict()
            )

        # -----------------------------------------------------
        # Chaîne
        # -----------------------------------------------------

        if isinstance(context, str):

            return context

        # -----------------------------------------------------
        # Dictionnaire
        # -----------------------------------------------------

        if isinstance(context, dict):

            lines = []

            for key, value in context.items():

                lines.append(
                    f"{key} :\n{self._format_context(value)}"
                )

            return "\n".join(lines)

        # -----------------------------------------------------
        # Liste / tuple
        # -----------------------------------------------------

        if isinstance(
            context,
            (list, tuple)
        ):

            return "\n".join(
                str(item)
                for item in context
            )

        # -----------------------------------------------------
        # Objet
        # -----------------------------------------------------

        return str(context)

    # =========================================================
    # SUPPRESSION DERNIER MESSAGE UTILISATEUR
    # =========================================================

    def _remove_last_user_message(self):
        """
        Supprime le dernier message utilisateur ajouté
        lorsqu'une génération échoue.

        Cette méthode reste volontairement compatible
        avec l'implémentation actuelle de ConversationMemory.
        """

        try:

            history = self.conversation._messages

        except AttributeError:

            return

        if not history:

            return

        last = history[-1]

        if (
            isinstance(last, dict)
            and last.get("role") == "user"
        ):

            history.pop()

    # =========================================================
    # MODELE
    # =========================================================

    def set_model(self, model):

        if not isinstance(model, str):

            raise TypeError(
                "Le nom du modèle doit être une chaîne."
            )

        model = model.strip()

        if not model:

            raise ValueError(
                "Le nom du modèle ne peut pas être vide."
            )

        self.model = model

    def get_model(self):

        return self.model

    # =========================================================
    # PROMPT
    # =========================================================

    def get_system_prompt(self):

        return self.prompt_builder.build()

    # =========================================================
    # MEMOIRE
    # =========================================================

    def clear_conversation(self):

        self.conversation.clear()

    def get_conversation(self):

        return self.conversation.get_messages()

    # =========================================================
    # PROFIL
    # =========================================================

    def get_profile(self):

        return self.profile

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "model": self.model,

            "messages": self.conversation.count(),

            "profile": self.profile.summary()

        }