"""Modes de fonctionnement d'ARGOS.

Principe défini dans le README §18 :

    - un mode reste actif jusqu'à ce que l'utilisateur le quitte ;
    - un mode ne désactive jamais les autres capacités d'ARGOS.

Ainsi, en mode Académie, ARGOS peut toujours utiliser Internet,
sa mémoire et ses outils. Le mode change la posture d'ARGOS,
pas ses capacités.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.config import ArgosConfig
from core.model_manager import (
    TASK_CODE,
    TASK_FAST,
    TASK_GENERAL,
    TASK_REASONING,
)

MODE_NORMAL = "normal"
MODE_ACADEMY = "academie"
MODE_DEVELOPMENT = "developpement"
MODE_RESEARCH = "recherche"
MODE_PROJECT = "projet"
MODE_PLANNING = "planification"
MODE_AUTOMATION = "automatisation"


@dataclass(frozen=True)
class ModeDefinition:
    """Description complète d'un mode."""

    key: str
    label: str
    description: str
    instructions: str
    aliases: Tuple[str, ...] = ()
    preferred_engines: Tuple[str, ...] = field(default=())
    model_task: str = TASK_GENERAL

    def matches(self, text: str) -> bool:
        """Indique si un texte désigne ce mode."""

        return any(alias in text for alias in self.aliases)


MODE_DEFINITIONS: Tuple[ModeDefinition, ...] = (

    ModeDefinition(
        key=MODE_NORMAL,
        label="Normal",
        description="Conversation générale et assistance quotidienne.",
        instructions=(
            "MODE NORMAL\n"
            "Réponds de façon naturelle, directe et utile. "
            "Adapte la longueur de ta réponse à la demande. "
            "Utilise la mémoire et les outils lorsque c'est pertinent, "
            "sans imposer de structure pédagogique ou technique."
        ),
        aliases=("normal", "conversation", "mode normal"),
        model_task=TASK_GENERAL,
    ),

    ModeDefinition(
        key=MODE_ACADEMY,
        label="Académie",
        description="Mode pédagogique : expliquer, guider, faire pratiquer.",
        instructions=(
            "MODE ACADEMIE\n"
            "Tu ne cherches pas seulement à donner la réponse. "
            "Tu expliques, tu guides, tu fais réfléchir, tu donnes des "
            "exemples, tu corriges, tu proposes des exercices et tu "
            "adaptes la difficulté au niveau de l'utilisateur. "
            "Vérifie régulièrement la compréhension avant d'avancer."
        ),
        aliases=("academie", "academique", "academy", "pedagogique"),
        preferred_engines=("academy", "knowledge"),
        model_task=TASK_GENERAL,
    ),

    ModeDefinition(
        key=MODE_DEVELOPMENT,
        label="Développement",
        description="Assistant de développement : inspecter, écrire, tester, corriger.",
        instructions=(
            "MODE DEVELOPPEMENT\n"
            "Tu agis comme un développeur rigoureux. "
            "Inspecte le projet avant de proposer quoi que ce soit, "
            "identifie les fichiers concernés, propose une architecture, "
            "écris du code complet, teste-le, détecte les erreurs et "
            "corrige-les. N'annonce jamais un résultat que tu n'as pas "
            "réellement vérifié."
        ),
        aliases=("developpement", "dev", "code", "programmation"),
        preferred_engines=("code", "knowledge"),
        model_task=TASK_CODE,
    ),

    ModeDefinition(
        key=MODE_RESEARCH,
        label="Recherche",
        description="Recherche d'informations et construction de connaissances.",
        instructions=(
            "MODE RECHERCHE\n"
            "Tu identifies d'abord ce que tu ignores, puis tu recherches, "
            "tu consultes plusieurs sources, tu les compares, tu extrais "
            "ce qui est pertinent et tu synthétises. "
            "Distingue toujours ce qui vient d'une source de ce qui vient "
            "de tes connaissances générales. Signale les informations "
            "incertaines ou contradictoires."
        ),
        aliases=("recherche", "research", "documentation"),
        preferred_engines=("internet", "knowledge"),
        model_task=TASK_REASONING,
    ),

    ModeDefinition(
        key=MODE_PROJECT,
        label="Projet",
        description="Suivi global d'un projet : objectifs, bugs, décisions, progression.",
        instructions=(
            "MODE PROJET\n"
            "Tu suis l'avancement du projet. "
            "Rappelle les objectifs, l'état d'avancement, les décisions "
            "déjà prises, les problèmes ouverts et les prochaines étapes. "
            "Reste cohérent avec les décisions mémorisées et signale toute "
            "contradiction avec un choix antérieur."
        ),
        aliases=("projet", "project", "chantier"),
        preferred_engines=("project", "knowledge"),
        model_task=TASK_GENERAL,
    ),

    ModeDefinition(
        key=MODE_PLANNING,
        label="Planification",
        description="Décomposition d'une demande en mission et en étapes.",
        instructions=(
            "MODE PLANIFICATION\n"
            "Tu transformes la demande en mission : objectifs, étapes "
            "ordonnées, dépendances, critères de réussite. "
            "Tu ne passes pas à l'exécution sans que le plan soit validé. "
            "Sois explicite sur les hypothèses et les risques."
        ),
        aliases=("planification", "planning", "plan"),
        preferred_engines=("planner",),
        model_task=TASK_REASONING,
    ),

    ModeDefinition(
        key=MODE_AUTOMATION,
        label="Automatisation",
        description="Exécution d'actions et de procédures, avec vérification.",
        instructions=(
            "MODE AUTOMATISATION\n"
            "Tu exécutes des actions réelles par les outils disponibles. "
            "Respecte strictement le système de permissions : demande "
            "l'autorisation avant toute action sensible. "
            "Après chaque action, tu observes le résultat, tu le vérifies "
            "et tu corriges si nécessaire. "
            "Tu ne considères jamais 'commande exécutée' comme "
            "équivalent à 'tâche réussie'."
        ),
        aliases=("automatisation", "automation", "automatique", "execution"),
        preferred_engines=("code", "internet"),
        model_task=TASK_CODE,
    ),
)

MODES_BY_KEY: Dict[str, ModeDefinition] = {
    definition.key: definition for definition in MODE_DEFINITIONS
}


def normalize(text: str) -> str:
    """Normalise un texte : minuscules, sans accents, espaces uniques."""

    if not isinstance(text, str):
        return ""

    text = unicodedata.normalize("NFD", text.lower())

    text = "".join(
        char for char in text if unicodedata.category(char) != "Mn"
    )

    return " ".join(text.split())


class ModeManager:
    """Gère le mode courant d'ARGOS."""

    def __init__(self, config: Optional[ArgosConfig] = None):

        self.config = config or ArgosConfig()

    # =========================================================
    # ETAT
    # =========================================================

    @property
    def current(self) -> str:
        """Clé du mode actif."""

        key = str(self.config.get("modes.current", MODE_NORMAL) or MODE_NORMAL)

        if key not in MODES_BY_KEY:
            return MODE_NORMAL

        return key

    def current_definition(self) -> ModeDefinition:

        return MODES_BY_KEY[self.current]

    def set_mode(self, key: str) -> ModeDefinition:
        """Active un mode et l'enregistre (il persiste entre sessions)."""

        if key not in MODES_BY_KEY:
            raise ValueError(
                f"Mode inconnu : {key!r}. "
                f"Modes valides : {', '.join(MODES_BY_KEY)}."
            )

        self.config.set("modes.current", key)

        return MODES_BY_KEY[key]

    def reset(self) -> ModeDefinition:
        """Revient au mode normal."""

        return self.set_mode(MODE_NORMAL)

    def is_active(self, key: str) -> bool:

        return self.current == key

    # =========================================================
    # DETECTION DANS UN MESSAGE
    # =========================================================

    def detect_command(self, message: str) -> Optional[Tuple[str, Optional[str]]]:
        """Détecte une demande de changement de mode.

        Retourne :

            ("set", clé)   pour activer un mode ;
            ("reset", None) pour revenir au mode normal ;
            None           si le message ne concerne pas les modes.
        """

        text = normalize(message)

        if not text:
            return None

        # -----------------------------------------------------
        # Quitter un mode
        # -----------------------------------------------------

        leave_markers = (
            "quitte le mode",
            "quitter le mode",
            "sors du mode",
            "sortir du mode",
            "arrete le mode",
            "desactive le mode",
            "fin du mode",
            "mode normal",
            "reviens en normal",
            "retour au mode normal",
            "plus de mode",
        )

        for marker in leave_markers:
            if marker in text:
                # "passe en mode normal" est un changement explicite
                # vers le mode normal, pas une sortie ambiguë.
                return "reset", None

        # -----------------------------------------------------
        # Entrer dans un mode
        # -----------------------------------------------------

        enter_markers = (
            "passe en mode",
            "passer en mode",
            "active le mode",
            "activer le mode",
            "mets toi en mode",
            "met toi en mode",
            "mets-toi en mode",
            "mode ",
        )

        if not any(marker in text for marker in enter_markers):
            return None

        # On cherche d'abord un mode explicitement nommé.
        for definition in MODE_DEFINITIONS:
            if definition.key in (MODE_NORMAL,):
                continue

            if definition.matches(text):
                return "set", definition.key

        return None

    def apply_message(self, message: str) -> Optional[ModeDefinition]:
        """Applique un éventuel changement de mode demandé.

        Retourne la nouvelle définition si le mode a changé,
        sinon None.
        """

        detected = self.detect_command(message)

        if not detected:
            return None

        command, key = detected

        if command == "reset":
            return self.reset()

        return self.set_mode(key)

    # =========================================================
    # CONTRIBUTION AU PROMPT
    # =========================================================

    def prompt_instructions(self) -> str:
        """Bloc de prompt décrivant le mode actif."""

        definition = self.current_definition()

        return (
            f"================================================\n"
            f"MODE ACTIF : {definition.label.upper()}\n"
            f"================================================\n\n"
            f"{definition.instructions}\n\n"
            "Ce mode modifie ta posture, pas tes capacités. "
            "Tu conserves l'accès à la mémoire, aux connaissances, "
            "à Internet et aux outils."
        )

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def all_modes(self) -> List[Dict[str, object]]:
        """Liste des modes, destinée à l'interface."""

        return [
            {
                "key": definition.key,
                "label": definition.label,
                "description": definition.description,
                "active": definition.key == self.current,
            }
            for definition in MODE_DEFINITIONS
        ]

    def summary(self) -> Dict[str, object]:

        definition = self.current_definition()

        return {
            "current": definition.key,
            "label": definition.label,
            "description": definition.description,
            "available": [item.key for item in MODE_DEFINITIONS],
        }
