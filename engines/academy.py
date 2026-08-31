from core.base_engine import BaseEngine


class AcademyEngine(BaseEngine):
    """
    Moteur pédagogique d'ARGOS.

    Academy détecte les demandes d'explication
    et prépare le contexte nécessaire à ResponseManager.

    Il ne génère pas directement la réponse finale.
    """

    def __init__(self):

        super().__init__(
            name="academy",
            priority=2,
            capabilities=[
                "academy",
                "education",
                "explanation"
            ]
        )

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(self, message, context):

        if not isinstance(message, str):

            return None

        message = message.strip()

        if not message:

            return None

        text = message.lower()

        # =====================================================
        # DETECTION
        # =====================================================

        explanation_request = (

            "explique" in text

            or "pourquoi" in text

            or "comment" in text

            or "c'est quoi" in text

            or "définition" in text

            or "definition" in text

            or "apprends" in text

            or "apprendre" in text

        )

        if not explanation_request:

            return None

        # =====================================================
        # CONTEXTE DE CONVERSATION
        # =====================================================

        conversation_context = context.get(
            "conversation_context",
            ""
        )

        # =====================================================
        # MESSAGE ACTUEL
        # =====================================================

        current_message = context.get(
            "current_message",
            message
        )

        # =====================================================
        # CONTEXTE DES AUTRES MOTEURS
        # =====================================================

        engine_results = context.all_engines()

        engine_context = ""

        if engine_results:

            engine_context = (
                "Résultats des moteurs déjà utilisés "
                "pour cette requête :\n\n"
            )

            for engine_name, result in engine_results.items():

                engine_context += (
                    f"[{engine_name}]\n"
                    f"{result}\n\n"
                )

        # =====================================================
        # CONSTRUCTION DU PROMPT
        # =====================================================

        prompt_context = (

            "MODE ACADEMIE\n\n"

            "Tu es le moteur pédagogique d'ARGOS.\n"

            "Tu dois produire une réponse claire, "
            "naturelle, pédagogique et adaptée "
            "au niveau de l'utilisateur.\n\n"

            "IMPORTANT :\n"

            "Si la demande actuelle fait référence "
            "à quelque chose mentionné précédemment, "
            "utilise le contexte conversationnel "
            "pour comprendre cette référence.\n\n"

            "Tu ne dois pas inventer une information "
            "absente du contexte.\n\n"

            "================================================\n"
            "CONTEXTE DE CONVERSATION\n"
            "================================================\n\n"

            f"{conversation_context}\n"

            "================================================\n"
            "RESULTATS DES AUTRES MOTEURS\n"
            "================================================\n\n"

            f"{engine_context}\n"

            "================================================\n"
            "DEMANDE ACTUELLE\n"
            "================================================\n\n"

            f"{current_message}\n\n"

            "Réponds en tenant compte du contexte précédent "
            "lorsque cela est pertinent."
        )

        # =====================================================
        # RESULTAT
        # =====================================================

        return {

            "mode": "academy",

            "type": "explanation",

            "content": None,

            "prompt_context": prompt_context

        }