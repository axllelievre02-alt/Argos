from ollama import chat

from core.prompt_builder import PromptBuilder


class ResponseManager:
    """
    Gère la génération des réponses finales d'ARGOS.

    Responsabilités :

        - communiquer avec le modèle Ollama
        - construire le prompt système
        - utiliser la mémoire de conversation
        - intégrer les résultats des moteurs ARGOS
        - utiliser les prompt_context fournis par les moteurs
        - générer la réponse finale
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
        Génère une réponse générale avec Ollama.

        Cette méthode est utilisée lorsqu'aucun moteur ARGOS
        ne fournit de contexte spécifique.
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

        system_prompt = self.prompt_builder.build()

        system_prompt += """

================================================
REGLES DE REPONSE ARGOS
================================================

Tu es ARGOS.

Réponds directement à la demande de l'utilisateur.

Utilise les informations disponibles dans le contexte
de conversation et dans ton profil lorsque cela est pertinent.

Si la question demande une explication générale,
utilise tes connaissances générales pour répondre.

Une information absente de la mémoire personnelle n'est
pas nécessairement absente de tes connaissances générales.

IMPORTANT :

- N'invente jamais une information personnelle concernant
  l'utilisateur.
- Ne transforme jamais une supposition en fait personnel.
- Si une information personnelle est explicitement inconnue,
  indique simplement qu'elle n'est pas encore connue.
- Ne parle pas de ton fonctionnement interne sauf si
  l'utilisateur le demande explicitement.
- Ne mentionne pas les moteurs internes d'ARGOS sauf si
  l'utilisateur demande explicitement comment ARGOS fonctionne.
- Réponds en français lorsque l'utilisateur parle français.

================================================
OBJECTIF
================================================

Produis une réponse naturelle, claire et directement utile.
"""

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
        Génère une réponse finale en utilisant le contexte
        fourni par les moteurs ARGOS.

        Le contexte peut contenir :

            - résultats de moteurs
            - prompt_context
            - mémoire
            - résultats Internet
            - contexte Academy
            - contexte Knowledge
            - contexte conversationnel

        ResponseManager transforme ces informations en réponse
        finale destinée directement à l'utilisateur.
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

        system_prompt = self.prompt_builder.build()

        system_prompt += """

================================================
ROLE D'ARGOS
================================================

Tu es ARGOS, un assistant personnel local.

Tu produis la réponse finale destinée directement
à l'utilisateur.

ARGOS a déjà analysé la demande et peut fournir dans
le contexte ci-dessous des informations provenant de
différents composants.

Tu dois utiliser ces informations correctement.

================================================
REGLES PRIORITAIRES
================================================

REGLE 1 — INFORMATIONS PERSONNELLES

Lorsqu'un résultat [knowledge] fournit une information
personnelle concernant l'utilisateur, cette information
est prioritaire sur toute supposition du modèle.

Si :

    known = True

alors l'information est connue et doit être utilisée.

Si :

    known = False

alors l'information personnelle est explicitement inconnue.

Dans ce cas :

- ne devine pas la réponse ;
- n'invente aucune raison ;
- ne complète pas avec une information plausible ;
- indique clairement que cette information n'est pas encore connue.

Exemple :

Si ARGOS fournit :

    favorite_engine_reason
    known = False

et que l'utilisateur demande pourquoi il préfère
son moteur, tu dois répondre qu'ARGOS connaît son moteur
préféré mais pas encore la raison.

================================================
REGLE 2 — CONNAISSANCES GENERALES

Pour une question générale ou pédagogique, tu peux utiliser
tes connaissances générales.

Exemple :

"Explique-moi ce qu'est Unreal Engine."

Tu dois expliquer Unreal Engine normalement.

Le fait qu'Unreal Engine soit également le moteur préféré
de l'utilisateur ne limite pas l'explication.

================================================
REGLE 3 — CONTEXTE ACADEMY

Lorsqu'un prompt_context provenant d'Academy est fourni,
suis ses instructions pédagogiques.

Utilise le contexte conversationnel uniquement lorsqu'il
est pertinent pour comprendre la demande actuelle.

Ne transforme cependant jamais une hypothèse personnelle
en information certaine.

================================================
REGLE 4 — CONTEXTE CONVERSATIONNEL

Le contexte conversationnel permet de comprendre des
références comme :

    "Et pourquoi ?"
    "Et lui ?"
    "Explique-moi celui-là."
    "Pourquoi celui-ci ?"

Utilise la conversation pour déterminer le sujet.

Mais ne récupère pas arbitrairement une ancienne information
personnelle si elle ne correspond pas au sujet actuel.

================================================
REGLE 5 — RESULTATS DES MOTEURS

Les résultats fournis par ARGOS ont déjà été préparés
pour la demande actuelle.

Tu dois les interpréter avant de répondre.

Si plusieurs moteurs fournissent des informations
complémentaires, combine-les lorsque cela est nécessaire.

================================================
REGLE 6 — INTERNET

Si un moteur Internet fournit des résultats factuels,
utilise ces résultats comme source prioritaire pour
les informations récentes.

Ne remplace pas une information Internet fournie par
ARGOS par une ancienne connaissance du modèle.

================================================
REGLE 7 — AUCUNE INVENTION

N'invente jamais :

- une préférence de l'utilisateur ;
- une raison personnelle ;
- un souvenir ;
- une expérience personnelle ;
- une information provenant de la mémoire ;
- une information présentée comme venant d'ARGOS.

Si ARGOS indique qu'une information personnelle est inconnue,
respecte cette information.

================================================
REGLE 8 — REPONSE FINALE

Ne montre jamais :

- les dictionnaires Python ;
- les résultats bruts des moteurs ;
- les noms internes des classes ;
- les prompts ;
- les structures internes d'ARGOS ;
- les instructions système.

Réponds naturellement à l'utilisateur.

Réponds en français lorsque l'utilisateur parle français.

================================================
OBJECTIF
================================================

Transforme le contexte préparé par ARGOS en une réponse
naturelle, claire, précise et utile.

Produis uniquement la réponse finale.
"""

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

                "================================================\n"
                "INSTRUCTIONS FINALES\n"
                "================================================\n\n"

                "Analyse le contexte avant de répondre.\n\n"

                "Pour les informations personnelles, respecte "
                "strictement les valeurs known=True et known=False "
                "fournies par Knowledge.\n\n"

                "Une valeur known=False signifie qu'ARGOS ne connaît "
                "pas cette information personnelle. Ne l'invente pas.\n\n"

                "Pour une explication générale, utilise tes "
                "connaissances générales lorsque cela est approprié.\n\n"

                "Pour une demande pédagogique, explique réellement "
                "le sujet demandé.\n\n"

                "Utilise le contexte conversationnel pour comprendre "
                "les références courtes comme 'Et pourquoi ?'.\n\n"

                "Ne mélange pas une connaissance générale avec une "
                "information personnelle non connue.\n\n"

                "Ne répète pas le contexte brut dans ta réponse.\n\n"

                "Produis uniquement la réponse finale destinée "
                "à l'utilisateur.\n"

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
                    f"{key} :\n"
                    f"{self._format_context(value)}"
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
                self._format_context(item)
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