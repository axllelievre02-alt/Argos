from memory.profile import ProfileMemory
from memory.conversation import ConversationMemory
from memory.extractor import MemoryExtractor

from core.response_manager import ResponseManager
from core.engine_manager import EngineManager
from core.mission_builder import MissionBuilder
from core.planner import Planner
from core.executor import Executor
from core.prometheus import Prometheus

from engines.knowledge import KnowledgeEngine
from engines.academy import AcademyEngine
from engines.internet import InternetEngine


class Brain:
    """
    Cerveau principal d'ARGOS.

    Le Brain orchestre les différents composants
    du système sans contenir leur logique interne.

    Pipeline :

        Utilisateur
             ↓
        MemoryExtractor
             ↓
        Prometheus
             ↓
        MissionBuilder
             ↓
        Planner
             ↓
        Executor
             ↓
        Context
             ↓
        ResponseManager
             ↓
        Modèle
             ↓
        Réponse
    """

    def __init__(self):

        # =====================================================
        # MEMOIRE DE PROFIL
        # =====================================================

        self.profile = ProfileMemory()

        # =====================================================
        # MEMOIRE DE CONVERSATION
        # =====================================================

        self.conversation = ConversationMemory()

        # =====================================================
        # EXTRACTION DE MEMOIRE
        # =====================================================

        self.memory_extractor = MemoryExtractor()

        # =====================================================
        # GESTIONNAIRE DES MOTEURS
        # =====================================================

        self.engine_manager = EngineManager()

        # =====================================================
        # KNOWLEDGE
        # =====================================================

        self.knowledge_engine = KnowledgeEngine(
            profile_memory=self.profile,
            conversation_memory=self.conversation
        )

        self.engine_manager.register(
            self.knowledge_engine
        )

        # =====================================================
        # ACADEMY
        # =====================================================

        self.academy_engine = AcademyEngine()

        self.engine_manager.register(
            self.academy_engine
        )

        # =====================================================
        # INTERNET
        # =====================================================

        self.internet_engine = InternetEngine()

        self.engine_manager.register(
            self.internet_engine
        )

        # =====================================================
        # PROMETHEUS
        # =====================================================

        self.prometheus = Prometheus(
            available_engines=self.engine_manager.names()
        )

        # =====================================================
        # MISSION BUILDER
        # =====================================================

        self.mission_builder = MissionBuilder()

        # =====================================================
        # PLANNER
        # =====================================================

        self.planner = Planner()

        # =====================================================
        # EXECUTOR
        # =====================================================

        self.executor = Executor(
            self.engine_manager
        )

        # =====================================================
        # RESPONSE MANAGER
        # =====================================================

        self.response_manager = ResponseManager(
            self.profile,
            self.conversation
        )

        # =====================================================
        # DERNIER CONTEXTE
        # =====================================================

        self.last_context = None

        # =====================================================
        # DEBUG
        # =====================================================

        print("\n===== ARGOS =====")

        print("Profil chargé :")

        print(
            self.profile.load()
        )

        print("=================\n")

    # =========================================================
    # REFLEXION
    # =========================================================

    def think(self, message):
        """
        Traite une requête utilisateur.

        Le Brain orchestre uniquement le pipeline.

        Il ne contient pas la logique interne
        des moteurs.
        """

        # =====================================================
        # VERIFICATION
        # =====================================================

        if not isinstance(message, str):

            raise TypeError(
                "Le message doit être une chaîne de caractères."
            )

        message = message.strip()

        if not message:

            return ""

        # =====================================================
        # MEMOIRE
        # =====================================================

        memory = self.memory_extractor.extract(
            message,
            conversation=self.conversation.get_messages()
        )

        if memory is not None:

            print(
                "Mémoire détectée:",
                memory
            )

            if memory.get("type") == "profile":

                key = memory.get("key")
                value = memory.get("value")

                if key and value:

                    self.profile.set(
                        key,
                        value
                    )

                    print(
                        f"✓ Mémoire sauvegardée : "
                        f"{key} = {value}"
                    )

        # =====================================================
        # PROMETHEUS
        # =====================================================

        plan = self.prometheus.decide(
            message,
            conversation=self.conversation.get_messages()
        )

        # =====================================================
        # MISSION
        # =====================================================

        mission = self.mission_builder.build(
            plan
        )

        # =====================================================
        # PLANNER
        # =====================================================

        mission = self.planner.execute(
            mission
        )

        # =====================================================
        # HISTORIQUE AVANT LA REQUETE
        # =====================================================

        conversation = (
            self.conversation.get_messages()
        )

        # =====================================================
        # EXECUTION
        # =====================================================

        context = self.executor.execute(
            mission,
            message,
            conversation=conversation
        )

        # =====================================================
        # SAUVEGARDE DU CONTEXTE
        # =====================================================

        self.last_context = context

        # =====================================================
        # RESULTAT DES MOTEURS
        # =====================================================

        result = context.last_result()

        print(
            "\n===== DEBUG RESULTAT FINAL ====="
        )

        print(
            result
        )

        print(
            "===============================\n"
        )

        # =====================================================
        # AUCUN RESULTAT
        # =====================================================

        if result is None:

            return self._fallback(
                message
            )

        # =====================================================
        # RESULTAT DICTIONNAIRE
        # =====================================================

        if isinstance(result, dict):

            # -------------------------------------------------
            # REPONSE DIRECTE
            # -------------------------------------------------

            content = result.get(
                "content"
            )

            if content:

                self.conversation.add_user_message(
                    message
                )

                self.conversation.add_assistant_message(
                    content
                )

                return content

            # -------------------------------------------------
            # CONTEXTE POUR RESPONSE MANAGER
            # -------------------------------------------------

            prompt_context = result.get(
                "prompt_context"
            )

            if prompt_context:

                response = (
                    self.response_manager
                    .generate_with_context(
                        message,
                        context
                    )
                )

                return response

        # =====================================================
        # FALLBACK
        # =====================================================

        return self._fallback(
            message
        )

    # =========================================================
    # FALLBACK
    # =========================================================

    def _fallback(self, message):
        """
        Génère une réponse classique lorsque
        les moteurs ne fournissent pas de résultat
        exploitable.
        """

        response = self.response_manager.generate(
            message
        )

        return response

    # =========================================================
    # PROFIL
    # =========================================================

    def get_profile(self):

        return self.profile.load()

    # =========================================================
    # CONVERSATION
    # =========================================================

    def get_conversation(self):

        return self.conversation.get_messages()

    # =========================================================
    # CONTEXTE
    # =========================================================

    def get_last_context(self):

        return self.last_context

    # =========================================================
    # RESET
    # =========================================================

    def clear_conversation(self):

        self.conversation.clear()

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):

        return {

            "profile":
                self.profile.summary(),

            "conversation":
                self.conversation.summary(),

            "engines":
                self.engine_manager.names(),

            "prometheus":
                self.prometheus.summary()

        }

