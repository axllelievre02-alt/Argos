"""Tests du système d'outils, des permissions et de la sécurité.

Ces tests vérifient le contrat le plus important du projet
(README §28) : ARGOS ne peut pas exécuter une action dangereuse
sans une autorisation explicite.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from core.config import ArgosConfig
from core.paths import PROJECT_ROOT
from core.permissions import (
    CRITICAL,
    READ,
    SAFE,
    SENSITIVE,
    PermissionManager,
)
from core.safety import (
    RISK_CRITICAL,
    RISK_SENSITIVE,
    command_risk,
    is_protected_path,
    path_risk,
)
from core.tools import build_default_registry
from core.tools.base import as_bool, as_int


class SafetyTests(unittest.TestCase):
    """Analyse de risque des commandes et des chemins."""

    def test_safe_command_is_not_dangerous(self):

        self.assertEqual(
            command_risk("python --version").level,
            0
        )

        self.assertEqual(
            command_risk("echo bonjour").level,
            0
        )

    def test_package_install_is_sensitive(self):

        self.assertEqual(
            command_risk("pip install requests").level,
            RISK_SENSITIVE
        )

    def test_disk_format_is_critical(self):

        self.assertEqual(
            command_risk("format c: /y").level,
            RISK_CRITICAL
        )

    def test_system_paths_are_protected(self):

        self.assertTrue(is_protected_path("C:/Windows/System32"))

    def test_writing_in_system_path_is_critical(self):

        self.assertEqual(
            path_risk("C:/Windows/System32/test.txt", write=True).level,
            RISK_CRITICAL
        )

    def test_writing_in_project_is_safe(self):

        self.assertEqual(
            path_risk(PROJECT_ROOT / "note.txt", write=True).level,
            1
        )


class CoercionTests(unittest.TestCase):

    def test_bool_coercion_accepts_french_and_english(self):

        for value in ("true", "True", "oui", "vrai", "1", 1, True):
            self.assertTrue(as_bool(value))

        for value in ("false", "non", "0", 0, False, ""):
            self.assertFalse(as_bool(value))

    def test_int_coercion_handles_garbage(self):

        self.assertEqual(as_int("42"), 42)
        self.assertEqual(as_int("abc", 7), 7)
        self.assertEqual(as_int(None, 7), 7)
        self.assertEqual(as_int("-5", None, minimum=1), 1)


class ToolLayerTests(unittest.TestCase):

    def setUp(self):

        self.tmp = tempfile.TemporaryDirectory()

        # Configuration isolée : les tests ne touchent pas aux
        # réglages réels de l'utilisateur.
        self.config = ArgosConfig(
            file_path=Path(self.tmp.name) / "settings.json"
        )

        self.permissions = PermissionManager(self.config)

        self.registry = build_default_registry(self.permissions)

        # Espace de travail réel, dans le projet, nettoyé à la fin.
        self.workspace = Path(
            tempfile.mkdtemp(dir=PROJECT_ROOT, prefix="_argos_test_")
        )

    def tearDown(self):

        shutil.rmtree(self.workspace, ignore_errors=True)

        self.tmp.cleanup()

    def _approve_all(self):

        calls = []

        def handler(request):

            calls.append(request)

            return True

        self.permissions.set_confirmation_handler(handler)

        return calls

    def test_registry_exposes_the_full_toolset(self):

        names = self.registry.names()

        for expected in (
            "list_files",
            "read_file",
            "search_files",
            "file_info",
            "write_file",
            "create_file",
            "append_file",
            "make_directory",
            "delete_file",
            "move_file",
            "run_command",
            "run_python",
            "search_web",
            "fetch_url",
            "open_path",
            "open_application",
        ):
            self.assertIn(expected, names)

    def test_describe_lists_usage_and_level(self):

        description = self.registry.describe()

        self.assertIn("read_file(path", description)
        self.assertIn("niveau", description)

    def test_read_tool_is_allowed_without_confirmation(self):

        result = self.registry.execute("list_files", path=str(PROJECT_ROOT))

        self.assertTrue(result.ok)
        self.assertIn("main.py", result.output)

    def test_unknown_tool_returns_error(self):

        result = self.registry.execute("outil_inexistant")

        self.assertFalse(result.ok)
        self.assertIn("Outil inconnu", result.error)

    def test_missing_required_parameter_is_reported(self):

        result = self.registry.execute("read_file")

        self.assertFalse(result.ok)
        self.assertIn("obligatoire", result.error)

    def test_write_inside_project_is_allowed(self):

        target = self.workspace / "note.txt"

        result = self.registry.execute(
            "write_file",
            path=str(target),
            content="bonjour",
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(target.read_text(encoding="utf-8"), "bonjour")

    def test_read_file_returns_numbered_lines(self):

        target = self.workspace / "lignes.txt"
        target.write_text("un\ndeux\ntrois\n", encoding="utf-8")

        result = self.registry.execute("read_file", path=str(target))

        self.assertTrue(result.ok)
        self.assertIn("1 | un", result.output)
        self.assertIn("3 | trois", result.output)

    def test_write_outside_project_requires_confirmation(self):

        outside = Path(self.tmp.name) / "hors_projet.txt"

        result = self.registry.execute(
            "write_file",
            path=str(outside),
            content="contenu",
        )

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertFalse(outside.exists())

    def test_write_outside_project_succeeds_once_approved(self):

        outside = Path(self.tmp.name) / "hors_projet.txt"

        calls = self._approve_all()

        result = self.registry.execute(
            "write_file",
            path=str(outside),
            content="contenu",
        )

        self.assertTrue(result.ok, result.error)
        self.assertEqual(len(calls), 1)
        self.assertTrue(outside.exists())

    def test_protected_path_write_is_refused_without_handler(self):

        result = self.registry.execute(
            "write_file",
            path="C:/Windows/System32/argos_interdit.txt",
            content="non",
        )

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertEqual(result.data.get("level"), CRITICAL)

    def test_destructive_command_is_refused_without_handler(self):

        result = self.registry.execute("run_command", command="format c: /y")

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertEqual(result.data.get("level"), CRITICAL)

    def test_safe_command_runs(self):

        result = self.registry.execute("run_command", command="echo argos")

        self.assertTrue(result.ok, result.error)
        self.assertIn("argos", result.output.lower())

    def test_python_execution_is_sensitive_and_approvable(self):

        refusal = self.registry.execute(
            "run_python",
            code="print('bonjour')",
        )

        self.assertFalse(refusal.ok)
        self.assertTrue(refusal.data.get("denied"))

        self._approve_all()

        result = self.registry.execute(
            "run_python",
            code="print('bonjour depuis ARGOS')",
        )

        self.assertTrue(result.ok, result.error)
        self.assertIn("bonjour depuis ARGOS", result.output)

    def test_deleting_non_empty_directory_is_critical(self):

        folder = self.workspace / "dossier"
        folder.mkdir()
        (folder / "fichier.txt").write_text("x", encoding="utf-8")

        result = self.registry.execute("delete_file", path=str(folder))

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertEqual(result.data.get("level"), CRITICAL)
        self.assertTrue(folder.exists())

    def test_critical_action_is_never_remembered(self):

        folder = self.workspace / "dossier"
        folder.mkdir()
        (folder / "fichier.txt").write_text("x", encoding="utf-8")

        calls = self._approve_all()

        first = self.registry.execute(
            "delete_file", path=str(folder), recursive=True
        )

        self.assertTrue(first.ok, first.error)

        # Deuxième dossier : la confirmation doit être redemandée,
        # car une action critique n'est jamais mémorisée.
        second_folder = self.workspace / "dossier2"
        second_folder.mkdir()
        (second_folder / "fichier.txt").write_text("y", encoding="utf-8")

        second = self.registry.execute(
            "delete_file", path=str(second_folder), recursive=True
        )

        self.assertTrue(second.ok, second.error)
        self.assertEqual(len(calls), 2)

    def test_confirmation_refusal_blocks_the_action(self):

        self.permissions.set_confirmation_handler(lambda _request: False)

        folder = self.workspace / "refuse"
        folder.mkdir()
        (folder / "fichier.txt").write_text("x", encoding="utf-8")

        result = self.registry.execute(
            "delete_file", path=str(folder), recursive=True
        )

        self.assertFalse(result.ok)
        self.assertTrue(folder.exists())

    def test_action_above_granted_level_is_refused_outright(self):

        # Un niveau 0 n'autorise même pas les actions sûres : la
        # demande doit être refusée, et non proposée à confirmation.
        self.permissions.set_level(READ)

        calls = self._approve_all()

        result = self.registry.execute(
            "write_file",
            path=str(self.workspace / "interdit.txt"),
            content="x",
        )

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertIn("niveau accordé", result.error)
        self.assertEqual(calls, [])
        self.assertFalse((self.workspace / "interdit.txt").exists())

    def test_fetch_url_rejects_non_http_scheme(self):

        result = self.registry.execute("fetch_url", url="file:///etc/passwd")

        self.assertFalse(result.ok)
        self.assertIn("non autorisé", result.error)

    def test_search_files_finds_text(self):

        (self.workspace / "cible.txt").write_text(
            "une aiguille ici\n", encoding="utf-8"
        )

        result = self.registry.execute(
            "search_files",
            query="aiguille",
            path=str(self.workspace),
        )

        self.assertTrue(result.ok)
        self.assertIn("cible.txt", result.output)

    def test_move_file_outside_project_is_sensitive(self):

        origin = self.workspace / "source.txt"
        origin.write_text("x", encoding="utf-8")

        result = self.registry.execute(
            "move_file",
            source=str(origin),
            destination=str(Path(self.tmp.name) / "destination.txt"),
        )

        self.assertFalse(result.ok)
        self.assertTrue(result.data.get("denied"))
        self.assertTrue(origin.exists())

    def test_effective_level_uses_the_higher_of_base_and_risk(self):

        tool = self.registry.get("run_command")

        level = self.registry.effective_level(
            tool,
            {"command": "pip install requests"},
        )

        self.assertEqual(level, SENSITIVE)

    def test_history_records_executions(self):

        self.registry.execute("list_files", path=str(PROJECT_ROOT))

        self.assertTrue(self.registry.history)

    def test_summary_reports_tools_and_permissions(self):

        summary = self.registry.summary()

        self.assertIn("tools", summary)
        self.assertEqual(summary["permissions"]["granted_level"], SAFE)


if __name__ == "__main__":

    unittest.main()
