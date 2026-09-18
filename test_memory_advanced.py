"""Tests de la mémoire avancée d'ARGOS.

Vérifie les niveaux de mémoire du README §7 :

    mémoire persistante    → ProfileMemory (déjà testée)
    mémoire sémantique     → LongTermMemory
    connaissances apprises → KnowledgeStore
    expériences            → ExperienceMemory
    procédures             → ProcedureMemory
"""

import tempfile
import unittest
from pathlib import Path

from memory.experience import ExperienceMemory
from memory.knowledge_store import KnowledgeStore
from memory.long_term import (
    CATEGORY_DECISION,
    CATEGORY_RULE,
    LongTermMemory,
)
from memory.procedures import ProcedureMemory


class MemoryTestCase(unittest.TestCase):

    def setUp(self):

        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):

        self.tmp.cleanup()


class LongTermMemoryTests(MemoryTestCase):

    def test_remember_and_get(self):

        memory = LongTermMemory(self.root / "long_term.json")

        memory.remember(
            "modèle principal",
            "qwen3:4b",
            category=CATEGORY_DECISION,
        )

        stored = memory.get("Modèle principal")

        self.assertIsNotNone(stored)
        self.assertEqual(stored["value"], "qwen3:4b")
        self.assertEqual(stored["category"], CATEGORY_DECISION)

    def test_remember_rejects_empty_values(self):

        memory = LongTermMemory(self.root / "long_term.json")

        self.assertIsNone(memory.remember("", "valeur"))
        self.assertIsNone(memory.remember("clé", "   "))
        self.assertEqual(memory.count(), 0)

    def test_update_preserves_creation_date(self):

        memory = LongTermMemory(self.root / "long_term.json")

        first = memory.remember("projet", "ARGOS")
        second = memory.remember("projet", "ARGOS V2")

        self.assertEqual(first["created"], second["created"])
        self.assertEqual(second["value"], "ARGOS V2")
        self.assertEqual(memory.count(), 1)

    def test_recall_finds_relevant_fact(self):

        memory = LongTermMemory(self.root / "long_term.json")

        memory.remember(
            "système de sauvegarde",
            "le format JSON Lines a été choisi pour les journaux",
        )
        memory.remember("cuisine", "le café se prépare avec de l'eau")

        results = memory.recall("quel format pour le système de sauvegarde")

        self.assertTrue(results)
        self.assertIn("sauvegarde", results[0]["key"].lower())

    def test_recall_ignores_unrelated_query(self):

        memory = LongTermMemory(self.root / "long_term.json")

        memory.remember("musique", "j'écoute du jazz")

        self.assertEqual(
            memory.recall("compile le projet python"),
            [],
        )

    def test_by_category_and_forget(self):

        memory = LongTermMemory(self.root / "long_term.json")

        memory.remember(
            "règle 1",
            "demander avant de supprimer",
            category=CATEGORY_RULE,
        )
        memory.remember("note 1", "une note quelconque")

        rules = memory.by_category(CATEGORY_RULE)

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["key"], "règle 1")

        self.assertTrue(memory.forget("règle 1"))
        self.assertFalse(memory.forget("règle 1"))
        self.assertEqual(memory.count(), 1)

    def test_prompt_text_lists_facts(self):

        memory = LongTermMemory(self.root / "long_term.json")

        memory.remember("projet", "ARGOS", category=CATEGORY_DECISION)

        text = memory.as_prompt_text()

        self.assertIn("ARGOS", text)
        self.assertIn("Décision", text)


class KnowledgeStoreTests(MemoryTestCase):

    def test_learn_and_get(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        store.learn(
            "pathlib",
            "Path remplace os.path pour manipuler les chemins.",
            source="docs.python.org",
        )

        entry = store.get("Pathlib")

        self.assertIsNotNone(entry)
        self.assertEqual(entry["confidence"], 0.5)
        self.assertIn("docs.python.org", entry["sources"])

    def test_corroboration_raises_confidence(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        store.learn("httpx", "Client HTTP asynchrone.", source="source A")

        first = store.get("httpx")["confidence"]

        store.learn("httpx", "Client HTTP asynchrone.", source="source B")

        second = store.get("httpx")

        self.assertGreater(second["confidence"], first)
        self.assertEqual(len(second["sources"]), 2)

    def test_same_source_does_not_raise_confidence(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        store.learn("ollama", "Serveur local.", source="A")
        store.learn("ollama", "Serveur local.", source="A")

        self.assertEqual(store.get("ollama")["confidence"], 0.5)

    def test_confidence_never_exceeds_one(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        for index in range(10):
            store.learn("test", "contenu", source=f"source-{index}")

        self.assertLessEqual(store.get("test")["confidence"], 1.0)

    def test_search_and_knows(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        store.learn("dictionnaire Python", "Structure clé/valeur.")

        self.assertTrue(store.knows("dictionnaire Python"))

        results = store.search("comment utiliser un dictionnaire")

        self.assertTrue(results)

    def test_unknown_topic_is_not_known(self):

        store = KnowledgeStore(self.root / "knowledge.json")

        self.assertFalse(store.knows("sujet jamais appris"))
        self.assertIsNone(store.get("sujet jamais appris"))


class ExperienceMemoryTests(MemoryTestCase):

    def test_record_and_success_rate(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        memory.record("créer un fichier", "write_file", ok=True)
        memory.record(
            "créer un fichier",
            "write_file",
            ok=False,
            detail="permission refusée",
        )

        rate = memory.success_rate("créer un fichier")

        self.assertEqual(rate["total"], 2)
        self.assertEqual(rate["successes"], 1)
        self.assertEqual(rate["rate"], 0.5)

    def test_recent_returns_newest_first(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        memory.record("tâche A", "action A", ok=True)
        memory.record("tâche B", "action B", ok=True)

        recent = memory.recent(2)

        self.assertEqual(recent[0]["task"], "tâche B")

    def test_failures_for_filters_failures_only(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        memory.record("lancer les tests", "run_command", ok=False)
        memory.record("lancer les tests", "run_command", ok=True)

        failures = memory.failures_for("lancer les tests")

        self.assertEqual(len(failures), 1)
        self.assertFalse(failures[0]["ok"])

    def test_lessons_report_repeated_failures(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        memory.record("déployer", "git push", ok=False)
        memory.record("déployer", "git push", ok=False)

        lessons = memory.lessons()

        self.assertTrue(lessons)
        self.assertIn("git push", lessons[0])

    def test_similar_finds_past_experience(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        memory.record(
            "corriger une erreur d'import",
            "read_file",
            ok=True,
            detail="le module memory.store manquait",
        )

        results = memory.similar("erreur d'import dans memory store")

        self.assertTrue(results)

    def test_empty_memory_is_safe(self):

        memory = ExperienceMemory(self.root / "experiences.json")

        self.assertEqual(memory.count(), 0)
        self.assertEqual(memory.success_rate()["rate"], 0.0)
        self.assertEqual(memory.lessons(), [])
        self.assertEqual(memory.as_prompt_text(), "")


class ProcedureMemoryTests(MemoryTestCase):

    def test_save_and_get(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        memory.save(
            "créer une scène Unreal",
            [
                "Ouvrir Unreal Engine",
                "Créer un niveau vide",
                "Ajouter une caméra",
                "Ajouter une lumière",
            ],
            goal="Obtenir une scène éclairée",
            software="Unreal Engine",
        )

        procedure = memory.get("Créer une scène Unreal")

        self.assertIsNotNone(procedure)
        self.assertEqual(len(procedure["steps"]), 4)
        self.assertEqual(procedure["software"], "Unreal Engine")

    def test_steps_accept_multiline_string(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        memory.save("export", "Étape un\n\nÉtape deux\nÉtape trois")

        procedure = memory.get("export")

        self.assertEqual(len(procedure["steps"]), 3)

    def test_save_rejects_empty_procedure(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        self.assertIsNone(memory.save("", ["étape"]))
        self.assertIsNone(memory.save("nom", []))
        self.assertEqual(memory.count(), 0)

    def test_find_returns_relevant_procedure(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        memory.save(
            "créer une scène Unreal",
            ["Ouvrir Unreal Engine", "Créer un niveau"],
            goal="scène éclairée",
            software="Unreal Engine",
        )

        results = memory.find("créer une scène dans Unreal Engine")

        self.assertTrue(results)
        self.assertEqual(results[0]["name"], "créer une scène Unreal")

    def test_use_increments_counter(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        memory.save("build", ["Configurer", "Compiler"])

        memory.use("build")
        memory.use("build")

        self.assertEqual(memory.get("build")["uses"], 2)

    def test_format_is_readable(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        procedure = memory.save(
            "build",
            ["Configurer", "Compiler"],
            goal="obtenir un exécutable",
        )

        text = ProcedureMemory.format(procedure)

        self.assertIn("1. Configurer", text)
        self.assertIn("2. Compiler", text)

    def test_latest_returns_most_recent(self):

        memory = ProcedureMemory(self.root / "procedures.json")

        memory.save("première", ["a"])
        memory.save("seconde", ["b"])

        latest = memory.latest()

        self.assertIn(latest["name"], ("première", "seconde"))


if __name__ == "__main__":

    unittest.main()
