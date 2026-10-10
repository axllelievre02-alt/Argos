"""Tests de persistance de ConversationMemory."""

import tempfile
import unittest
from pathlib import Path

from memory.conversation import ConversationMemory


class ConversationPersistenceTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "conversation.jsonl"

    def tearDown(self):
        self.directory.cleanup()

    def test_messages_survive_a_new_memory_instance(self):
        first = ConversationMemory(
            max_messages=4,
            file_path=self.path,
            persist=True,
        )
        first.add_user_message("Bonjour ARGOS")
        first.add_assistant_message("Bonjour Ikaris")

        restarted = ConversationMemory(
            max_messages=4,
            file_path=self.path,
            persist=True,
        )

        self.assertEqual(
            restarted.get_messages(),
            [
                {"role": "user", "content": "Bonjour ARGOS"},
                {"role": "assistant", "content": "Bonjour Ikaris"},
            ],
        )

    def test_persistence_respects_history_limit_and_clear(self):
        memory = ConversationMemory(
            max_messages=2,
            file_path=self.path,
            persist=True,
        )
        memory.add_user_message("un")
        memory.add_assistant_message("deux")
        memory.add_user_message("trois")

        restarted = ConversationMemory(
            max_messages=2,
            file_path=self.path,
            persist=True,
        )

        self.assertEqual(
            [item["content"] for item in restarted.get_messages()],
            ["deux", "trois"],
        )

        restarted.clear()
        self.assertTrue(
            ConversationMemory(
                file_path=self.path,
                persist=True,
            ).is_empty()
        )


if __name__ == "__main__":
    unittest.main()
