"""Tests de la couche configuration et modèles d'ARGOS.

Ces tests vérifient le principe central du README §25 :
le modèle est un outil interchangeable, pas l'identité d'ARGOS.
"""

import json
import tempfile
import unittest
from pathlib import Path

from core.config import ArgosConfig
from core.model_manager import ModelManager
from core.models.base import ModelError, ModelProvider
from core.models.ollama_provider import OllamaProvider


class FakeProvider(ModelProvider):
    """Fournisseur déterministe utilisé pour tester le routage."""

    name = "fake"

    def __init__(self, models, failing=()):

        self._models = list(models)
        self._failing = set(failing)
        self.calls = []

    def is_available(self):
        return True

    def list_models(self):
        return list(self._models)

    def chat(self, model, messages, options=None):

        self.calls.append(model)

        if model in self._failing:
            raise ModelError(f"modele indisponible : {model}")

        return f"reponse de {model}"


class ConfigTests(unittest.TestCase):

    def setUp(self):

        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "settings.json"

    def tearDown(self):

        self.directory.cleanup()

    def test_defaults_are_created_on_first_load(self):

        config = ArgosConfig(file_path=self.path)

        self.assertTrue(self.path.exists())
        self.assertEqual(config.get("models.default"), "qwen3:4b")
        self.assertEqual(config.get("permissions.level"), 1)

    def test_dotted_read_and_write(self):

        config = ArgosConfig(file_path=self.path)

        config.set("models.routes.code", "modele-code")

        self.assertEqual(
            config.get("models.routes.code"),
            "modele-code"
        )

        # La valeur doit survivre à un rechargement.
        reloaded = ArgosConfig(file_path=self.path)

        self.assertEqual(
            reloaded.get("models.routes.code"),
            "modele-code"
        )

    def test_missing_key_returns_default(self):

        config = ArgosConfig(file_path=self.path)

        self.assertEqual(
            config.get("inconnu.cle", "defaut"),
            "defaut"
        )

    def test_partial_file_is_completed_by_defaults(self):

        self.path.write_text(
            json.dumps({"models": {"default": "autre"}}),
            encoding="utf-8"
        )

        config = ArgosConfig(file_path=self.path)

        self.assertEqual(config.get("models.default"), "autre")
        self.assertIn("permissions", config.all())


class ModelManagerRoutingTests(unittest.TestCase):

    def setUp(self):

        self.directory = tempfile.TemporaryDirectory()
        self.config = ArgosConfig(
            file_path=Path(self.directory.name) / "settings.json"
        )

    def tearDown(self):

        self.directory.cleanup()

    def _manager(self, models, failing=()):

        provider = FakeProvider(models, failing=failing)

        manager = ModelManager(
            config=self.config,
            providers=[provider],
        )

        return manager, provider

    def test_resolve_uses_configured_route(self):

        self.config.set("models.routes.code", "modele-code")

        manager, _ = self._manager(
            ["modele-code", "modele-general"]
        )

        self.assertEqual(
            manager.resolve_model("code"),
            "modele-code"
        )

    def test_resolve_falls_back_to_default_model(self):

        self.config.set("models.default", "modele-general")
        self.config.set("models.routes.code", "absent")

        manager, _ = self._manager(
            ["modele-general", "autre"]
        )

        self.assertEqual(
            manager.resolve_model("code"),
            "modele-general"
        )

    def test_resolve_matches_untagged_model_name(self):

        self.config.set("models.default", "qwen3")

        manager, _ = self._manager(["qwen3:4b"])

        self.assertEqual(
            manager.resolve_model("general"),
            "qwen3:4b"
        )

    def test_generate_uses_selected_model(self):

        self.config.set("models.default", "modele-general")

        manager, provider = self._manager(["modele-general"])

        answer = manager.generate(
            [{"role": "user", "content": "bonjour"}]
        )

        self.assertEqual(answer, "reponse de modele-general")
        self.assertEqual(manager.last_model, "modele-general")
        self.assertEqual(provider.calls, ["modele-general"])

    def test_generate_falls_back_when_model_fails(self):

        self.config.set("models.default", "casse")

        manager, provider = self._manager(
            ["casse", "secours"],
            failing=["casse"],
        )

        answer = manager.generate(
            [{"role": "user", "content": "bonjour"}]
        )

        self.assertEqual(answer, "reponse de secours")
        self.assertEqual(provider.calls, ["casse", "secours"])

    def test_generate_raises_when_every_model_fails(self):

        self.config.set("models.default", "a")

        manager, _ = self._manager(
            ["a", "b"],
            failing=["a", "b"],
        )

        with self.assertRaises(ModelError):

            manager.generate(
                [{"role": "user", "content": "bonjour"}]
            )

    def test_set_route_rejects_unknown_task(self):

        manager, _ = self._manager(["modele"])

        with self.assertRaises(ValueError):
            manager.set_route("inconnu", "modele")


class OllamaProviderTests(unittest.TestCase):
    """Tests d'intégration avec le serveur Ollama local."""

    @classmethod
    def setUpClass(cls):

        cls.provider = OllamaProvider()

        cls.available = cls.provider.is_available()

    def test_provider_reports_availability(self):

        # Le test se contente de vérifier la cohérence du drapeau.
        self.assertIsInstance(self.available, bool)

        if not self.available:
            self.skipTest("Serveur Ollama non disponible.")

    def test_provider_lists_models(self):

        if not self.available:
            self.skipTest("Serveur Ollama non disponible.")

        models = self.provider.list_models()

        self.assertTrue(models)
        self.assertIsInstance(models[0], str)

    def test_provider_answers_a_short_prompt(self):

        if not self.available:
            self.skipTest("Serveur Ollama non disponible.")

        models = self.provider.list_models()

        answer = self.provider.chat(
            models[0],
            [
                {
                    "role": "system",
                    "content": "Reponds uniquement par le mot OK.",
                },
                {"role": "user", "content": "Dis OK."},
            ],
        )

        self.assertTrue(answer)
        self.assertNotIn("<think", answer)

    def test_provider_rejects_unknown_model(self):

        if not self.available:
            self.skipTest("Serveur Ollama non disponible.")

        with self.assertRaises(ModelError):

            self.provider.chat(
                "modele-qui-nexiste-pas:0b",
                [{"role": "user", "content": "test"}],
            )


if __name__ == "__main__":

    unittest.main()
