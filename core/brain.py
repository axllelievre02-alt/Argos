from memory.profile import ProfileMemory
from memory.conversation import ConversationMemory
from memory.extractor import MemoryExtractor
from memory.long_term import LongTermMemory

from core.response_manager import ResponseManager
from core.engine_manager import EngineManager
from core.mission_builder import MissionBuilder
from core.planner import Planner
from core.executor import Executor
from core.prometheus import Prometheus
from core.task_analyzer import TaskAnalyzer
from core.config import ArgosConfig
from core.model_manager import ModelManager
from core.modes import ModeManager
from core.paths import CONVERSATION_FILE

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
        TaskAnalyzer
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

    def __init__(self, config=None, conversation_file=None):

        # Les réglages, modes et modèles partagent la même configuration.
        self.config = config or ArgosConfig()

        self.mode_manager = ModeManager(self.config)

        self.model_manager = ModelManager(self.config)

        # =====================================================
        # MEMOIRE DE PROFIL
        # =====================================================

        self.profile = ProfileMemory()

        # =====================================================
        # MEMOIRE DE CONVERSATION
        # =====================================================

        self.conversation = ConversationMemory(
            max_messages=self.config.get("memory.max_messages", 50),
            file_path=conversation_file or CONVERSATION_FILE,
            persist=self.config.get("memory.persist_conversation", True),
        )

        # =====================================================
        # EXTRACTION DE MEMOIRE
        # =====================================================

        self.memory_extractor = MemoryExtractor()

        # =====================================================
        # MEMOIRE LONGUE DUREE
        # =====================================================

        self.long_term_memory = LongTermMemory()

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
        # TASK ANALYZER
        # =====================================================

        self.task_analyzer = TaskAnalyzer()

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
            self.conversation,
            model_manager=self.model_manager,
            mode_manager=self.mode_manager,
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

        if not isinstance(
            message,
            str
        ):

            raise TypeError(
                "Le message doit être une chaîne de caractères."
            )

        message = message.strip()

        if not message:

            return ""

        # Un changement de mode est une commande ARGOS : il est appliqué
        # immédiatement, persiste dans la configuration, et ne nécessite
        # aucune génération par le modèle.
        changed_mode = self.mode_manager.apply_message(message)

        if changed_mode is not None:

            answer = (
                f"Mode {changed_mode.label} activé. "
                "Il restera actif jusqu'à ce que tu reviennes "
                "en mode normal."
            )

            self.conversation.add_user_message(message)
            self.conversation.add_assistant_message(answer)

            return answer

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

            elif memory.get("type") == "long_term":

                record = self.long_term_memory.remember(
                    memory.get("key", ""),
                    memory.get("value", ""),
                    category=memory.get("category", "note")
                )

                if record:

                    print(
                        "✓ Note longue durée sauvegardée : "
                        f"{record.get('key')}"
                    )

        # =====================================================
        # TASK ANALYZER
        # =====================================================

        analysis = self.task_analyzer.analyze(
            message,
            conversation=self.conversation.get_messages()
        )

        print(
            "\n===== TASK ANALYZER ====="
        )

        print(
            analysis
        )

        print(
            "=========================\n"
        )

        # =====================================================
        # PROMETHEUS
        # =====================================================

        plan = self.prometheus.decide(
            analysis,
            conversation=self.conversation.get_messages()
        )

        # =====================================================
        # AUCUN MOTEUR NECESSAIRE
        # =====================================================

        if not plan:

            print(
                "ARGOS : Aucun moteur spécialisé "
                "nécessaire pour cette requête."
            )

            return self._fallback(
                message
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

        context.set(
            "long_term_matches",
            self.long_term_memory.recall(
                message,
                limit=3
            )
        )

        # =====================================================
        # RESULTAT DES MOTEURS
        # =====================================================

        result = context.last_result()

        # Une information personnelle reconnue par KnowledgeEngine est
        # autoritative. Academy peut avoir été exécuté après KnowledgeEngine
        # pour enrichir le contexte, mais ne doit jamais reformuler ni
        # contredire un fait ou une préférence déjà mémorisée.
        knowledge_result = context.get_engine(
            "knowledge"
        )

        if self._is_authoritative_knowledge_result(
            knowledge_result
        ):

            result = knowledge_result

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

        if isinstance(
            result,
            dict
        ):

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

    def _fallback(
        self,
        message
    ):
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
    # PRIORITE DES FAITS MEMORISES
    # =========================================================

    @staticmethod
    def _is_authoritative_knowledge_result(result):
        """Indique si un résultat Knowledge doit être rendu tel quel."""

        return (
            isinstance(result, dict)
            and result.get("handled") is True
            and bool(result.get("content"))
        )

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

            "long_term_memory":
                self.long_term_memory.summary(),

            "mode":
                self.mode_manager.summary(),

            "model":
                self.model_manager.summary(),

            "engines":
                self.engine_manager.names(),

            "task_analyzer":
                self.task_analyzer.summary(),

            "prometheus":
                self.prometheus.summary()

        }
