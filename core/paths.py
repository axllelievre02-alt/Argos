"""Résolution des chemins d'ARGOS.

ARGOS doit rester portable : PC, clé USB, autre machine.

Tous les chemins sont donc calculés à partir de la racine du projet
et ne sont jamais codés en dur ailleurs dans le code.

Structure des données :

    data/
        profile.json
        settings.json
        memory/
            conversation.jsonl
            long_term.json
        knowledge/
            knowledge.json
        projects/
            projects.json
        logs/
            argos.log
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
MEMORY_DIR = DATA_DIR / "memory"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
PROJECTS_DIR = DATA_DIR / "projects"
LOG_DIR = DATA_DIR / "logs"

PROFILE_FILE = DATA_DIR / "profile.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
CONVERSATION_FILE = MEMORY_DIR / "conversation.jsonl"
LONG_TERM_FILE = MEMORY_DIR / "long_term.json"
EXPERIENCE_FILE = MEMORY_DIR / "experiences.json"
PROCEDURE_FILE = MEMORY_DIR / "procedures.json"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "knowledge.json"
PROJECTS_FILE = PROJECTS_DIR / "projects.json"
LOG_FILE = LOG_DIR / "argos.log"

DIRECTORIES = (
    DATA_DIR,
    MEMORY_DIR,
    KNOWLEDGE_DIR,
    PROJECTS_DIR,
    LOG_DIR,
)


def ensure_directories() -> None:
    """Crée l'arborescence de données si elle n'existe pas."""

    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def is_inside_project(path) -> bool:
    """Indique si un chemin se situe dans la racine du projet."""

    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError):
        return False

    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return False

    return True
