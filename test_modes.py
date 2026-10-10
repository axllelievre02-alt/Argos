"""Tests d'intégration des modes V1 dans le pipeline ARGOS."""

import tempfile
import unittest
from pathlib import Path

from core.brain import Brain
from core.config import ArgosConfig
from core.modes import MODE_ACADEMY, MODE_DEVELOPMENT, ModeManager
from core.response_manager import ResponseManager
from memory.conversation import ConversationMemory


class EmptyProfile:
    """Profil minimal pour isoler les tests de prompt."""

    def load(self):
        return {}

    def summary(self):
        return {}


class RecordingModelManager:
    """Double déterministe qui enregistre le routage demandé."""

    def __init__(self):
        self.calls = []
        self.last_model = "modele-test"

    def generate(self, messages, task, model=None):
        self.calls.append(
            {"messages": messages, "task": task, "model": model}
        )
        return "Réponse de test."

    def configured_model(self, task):
        return f"modele-{task}"


class ModeIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = ArgosConfig(
            file_path=Path(self.directory.name) / "settings.json"
        )

    def tearDown(self):
        self.directory.cleanup()

    def test_mode_command_is_persistent_and_does_not_call_model(self):
        brain = Brain(
            config=self.config,
            conversation_file=Path(self.directory.name) / "conversation.jsonl",
        )

        answer = brain.think("Passe en mode académie")

        self.assertIn("Mode Académie activé", answer)
        self.assertEqual(brain.mode_manager.current, MODE_ACADEMY)

        reloaded = ModeManager(
            ArgosConfig(file_path=self.config.file_path)
        )
        self.assertEqual(reloaded.current, MODE_ACADEMY)

    def test_mode_changes_prompt_and_model_task(self):
        modes = ModeManager(self.config)
        recorder = RecordingModelManager()
        manager = ResponseManager(
            EmptyProfile(),
            ConversationMemory(),
            model_manager=recorder,
            mode_manager=modes,
        )

        modes.set_mode(MODE_ACADEMY)
        answer = manager.generate("Explique les listes Python.")

        self.assertEqual(answer, "Réponse de test.")
        self.assertEqual(recorder.calls[-1]["task"], "general")
        self.assertIn("MODE ACTIF : ACADÉMIE", manager.get_system_prompt())

        modes.set_mode(MODE_DEVELOPMENT)
        manager.generate("Analyse ce fichier.")

        self.assertEqual(recorder.calls[-1]["task"], "code")
        self.assertIn("MODE ACTIF : DÉVELOPPEMENT", manager.get_system_prompt())


if __name__ == "__main__":
    unittest.main()
