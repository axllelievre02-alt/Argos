import unittest

from core.brain import Brain
from core.context import Context
from core.prometheus import Prometheus
from core.response_manager import ResponseManager
from engines.knowledge import KnowledgeEngine
from engines.internet import InternetEngine
from memory.conversation import ConversationMemory
from memory.extractor import MemoryExtractor


class ArgosPipelineTests(unittest.TestCase):
    """Tests de régression du pipeline mémoire et contexte d'ARGOS."""

    def setUp(self):

        self.profile = {
            "name": "Ikaris",
            "language": "fr",
            "favorite_game": "Skies of Arcadia",
            "favorite_game_reason": "son univers et ses voyages en bateau volant",
            "favorite_engine": "Unreal Engine",
            "current_project": "ARGOS"
        }

    def test_knowledge_tolerates_spelling_variation(self):

        engine = KnowledgeEngine(
            profile_memory=self.profile
        )

        result = engine.answer(
            "Quel est mon jeu preferer ?"
        )

        self.assertTrue(result["handled"])
        self.assertTrue(result["known"])
        self.assertEqual(
            result["field"],
            "favorite_game"
        )
        self.assertIn(
            "Skies of Arcadia",
            result["content"]
        )

    def test_knowledge_resolves_contextual_why(self):

        conversation = ConversationMemory()

        conversation.add_user_message(
            "Quel est mon jeu préféré ?"
        )

        engine = KnowledgeEngine(
            profile_memory=self.profile,
            conversation_memory=conversation
        )

        result = engine.answer(
            "Et pourquoi ?"
        )

        self.assertTrue(result["handled"])
        self.assertEqual(
            result["field"],
            "favorite_game_reason"
        )
        self.assertIn(
            "bateau volant",
            result["content"]
        )

    def test_knowledge_resolves_short_reference(self):

        conversation = ConversationMemory()

        conversation.add_user_message(
            "Quel est mon projet actuel ?"
        )

        engine = KnowledgeEngine(
            profile_memory=self.profile,
            conversation_memory=conversation
        )

        result = engine.answer(
            "Et ça ?"
        )

        self.assertTrue(result["handled"])
        self.assertEqual(
            result["field"],
            "current_project"
        )
        self.assertIn(
            "ARGOS",
            result["content"]
        )

    def test_knowledge_formats_first_person_reason_for_user(self):

        profile = dict(
            self.profile,
            favorite_game_reason="j'adore son univers"
        )

        engine = KnowledgeEngine(
            profile_memory=profile
        )

        result = engine.answer(
            "Pourquoi j aime mon jeu prefere ?"
        )

        self.assertIn(
            "parce que tu adores son univers.",
            result["content"]
        )

    def test_prometheus_uses_knowledge_then_academy(self):

        prometheus = Prometheus(
            available_engines=[
                "knowledge",
                "academy"
            ]
        )

        plan = prometheus.decide(
            "Pourquoi j aime mon jeu prefere ?"
        )

        self.assertEqual(
            [task["engine"] for task in plan],
            ["knowledge", "academy"]
        )

    def test_prometheus_routes_short_personal_reference(self):

        prometheus = Prometheus(
            available_engines=[
                "knowledge",
                "academy"
            ]
        )

        plan = prometheus.decide(
            "Et ça ?",
            conversation=[
                {
                    "role": "user",
                    "content": "Quel est mon projet actuel ?"
                }
            ]
        )

        self.assertEqual(
            [task["engine"] for task in plan],
            ["knowledge"]
        )

    def test_prometheus_combines_internet_and_academy(self):

        prometheus = Prometheus(
            available_engines=[
                "knowledge",
                "academy",
                "internet"
            ]
        )

        plan = prometheus.decide(
            "Explique les actualités d'Unreal Engine en ligne."
        )

        self.assertEqual(
            [task["engine"] for task in plan],
            ["internet", "academy"]
        )

    def test_internet_engine_exposes_structured_results(self):

        def search_provider(query, max_results):

            self.assertEqual(
                query,
                "Nouveautés Unreal Engine"
            )

            self.assertEqual(max_results, 5)

            return [
                {
                    "title": "Documentation Unreal Engine",
                    "url": "https://example.com/unreal",
                    "snippet": "Informations officielles."
                }
            ]

        engine = InternetEngine(
            search_provider=search_provider
        )

        context = Context()

        result = engine.execute(
            "Nouveautés Unreal Engine",
            context
        )

        self.assertIsNone(result["error"])
        self.assertEqual(
            result["results"][0]["title"],
            "Documentation Unreal Engine"
        )
        self.assertIn(
            "https://example.com/unreal",
            result["prompt_context"]
        )
        self.assertEqual(
            context.get("internet_results"),
            result["results"]
        )

    def test_response_manager_receives_serialized_context(self):

        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Pourquoi j'aime mon jeu préféré ?"
                }
            ]
        )

        context.set_engine(
            "knowledge",
            {
                "content": (
                    "Tu aimes Skies of Arcadia "
                    "parce que son univers te plaît."
                )
            }
        )

        manager = ResponseManager.__new__(
            ResponseManager
        )

        formatted = manager._format_context(
            context
        )

        self.assertIn(
            "engine_results",
            formatted
        )
        self.assertIn(
            "Skies of Arcadia",
            formatted
        )
        self.assertNotIn(
            "core.context.Context",
            formatted
        )

    def test_extractor_requires_relevant_context_for_because(self):

        extractor = MemoryExtractor()

        self.assertIsNone(
            extractor.extract(
                "Parce que son univers me plaît.",
                conversation=[]
            )
        )

        result = extractor.extract(
            "Parce que son univers me plaît.",
            conversation=[
                {
                    "role": "user",
                    "content": "Pourquoi j aime mon jeu prefere ?"
                }
            ]
        )

        self.assertEqual(
            result["key"],
            "favorite_game_reason"
        )

    def test_brain_does_not_duplicate_model_conversation(self):

        brain = Brain()

        class FakeResponseManager:

            def generate_with_context(
                self,
                message,
                context
            ):

                brain.conversation.add_user_message(
                    message
                )

                brain.conversation.add_assistant_message(
                    "Réponse simulée."
                )

                return "Réponse simulée."

            def generate(
                self,
                message
            ):

                brain.conversation.add_user_message(
                    message
                )

                brain.conversation.add_assistant_message(
                    "Réponse simulée."
                )

                return "Réponse simulée."

        brain.response_manager = FakeResponseManager()

        answer = brain.think(
            "Pourquoi j aime mon jeu prefere ?"
        )

        self.assertEqual(
            answer,
            "Réponse simulée."
        )
        self.assertEqual(
            len(brain.get_conversation()),
            2
        )
        self.assertEqual(
            list(brain.get_last_context().all_engines()),
            ["knowledge", "academy"]
        )


if __name__ == "__main__":

    unittest.main()
