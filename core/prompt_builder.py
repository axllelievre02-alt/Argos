class PromptBuilder:
    """
    Construit le prompt système d'ARGOS.

    Le PromptBuilder ne possède aucune mémoire.

    Il rassemble simplement les informations fournies
    par les différents systèmes d'ARGOS afin de construire
    le contexte transmis au modèle de langage.

    Le modèle n'est qu'un moteur de génération.
    L'identité et les règles d'ARGOS sont définies ici.
    """

    def __init__(self, profile=None):

        self.profile = profile

        # =====================================================
        # IDENTITE
        # =====================================================

        self.identity = """
Tu es ARGOS.

ARGOS est une intelligence artificielle personnelle conçue
pour assister son utilisateur.

Ton utilisateur principal est Ikaris.

Tu dois te considérer comme ARGOS et non comme Qwen.

Qwen est uniquement le modèle de langage utilisé pour générer
le texte. Tu ne dois pas présenter Qwen comme ton identité.

Lorsque l'utilisateur demande "qui es-tu ?", présente-toi
comme ARGOS.
"""

        # =====================================================
        # LANGUE
        # =====================================================

        self.language = """
Réponds en français par défaut.

Si l'utilisateur demande explicitement une autre langue,
réponds dans cette langue.

Ne change pas spontanément de langue.
"""

        # =====================================================
        # COMPORTEMENT
        # =====================================================

        self.behavior = """
Tu dois être :

- utile ;
- clair ;
- précis ;
- honnête ;
- naturel ;
- cohérent avec la conversation.

Ne prétends jamais avoir effectué une action que tu n'as
pas réellement effectuée.

N'invente jamais de souvenir.

N'invente jamais une information personnelle concernant
l'utilisateur.

Si une information est présente dans la mémoire d'ARGOS,
tu peux l'utiliser.

Si une information n'est pas présente dans la mémoire,
ne prétends pas la connaître.

Lorsque tu ne connais pas une information, dis-le clairement.

Ne répète pas inutilement les mêmes explications.

Adapte la longueur de ta réponse à la demande de l'utilisateur.
"""

        # =====================================================
        # MEMOIRE
        # =====================================================

        self.memory_rules = """
La mémoire fournie dans ce prompt appartient à ARGOS.

Elle constitue une source de contexte utilisateur.

Tu dois distinguer :

1. ce qui est réellement présent dans la mémoire ;
2. ce qui apparaît uniquement dans la conversation actuelle ;
3. ce que tu ne sais pas.

Ne transforme jamais une supposition en souvenir.
"""

    # =========================================================
    # CONSTRUCTION
    # =========================================================

    def build(self):

        sections = []

        # -----------------------------------------------------
        # Identité
        # -----------------------------------------------------

        sections.append(
            self.identity.strip()
        )

        # -----------------------------------------------------
        # Langue
        # -----------------------------------------------------

        sections.append(
            self.language.strip()
        )

        # -----------------------------------------------------
        # Comportement
        # -----------------------------------------------------

        sections.append(
            self.behavior.strip()
        )

        # -----------------------------------------------------
        # Mémoire
        # -----------------------------------------------------

        sections.append(
            self.memory_rules.strip()
        )

        # -----------------------------------------------------
        # Profil utilisateur
        # -----------------------------------------------------

        profile_context = self._build_profile_context()

        if profile_context:

            sections.append(
                profile_context
            )

        return "\n\n".join(
            sections
        )

    # =========================================================
    # PROFIL
    # =========================================================

    def _build_profile_context(self):

        if self.profile is None:

            return ""

        try:

            profile = self.profile.load()

        except Exception:

            return ""

        if not isinstance(profile, dict):

            return ""

        lines = []

        # -----------------------------------------------------
        # Nom
        # -----------------------------------------------------

        name = profile.get(
            "name",
            ""
        )

        if name:

            lines.append(
                f"- Nom de l'utilisateur : {name}"
            )

        # -----------------------------------------------------
        # Langue
        # -----------------------------------------------------

        language = profile.get(
            "language",
            ""
        )

        if language:

            lines.append(
                f"- Langue préférée : {language}"
            )

        # -----------------------------------------------------
        # Jeu préféré
        # -----------------------------------------------------

        favorite_game = profile.get(
            "favorite_game",
            ""
        )

        if favorite_game:

            lines.append(
                f"- Jeu préféré : {favorite_game}"
            )

        # -----------------------------------------------------
        # Moteur préféré
        # -----------------------------------------------------

        favorite_engine = profile.get(
            "favorite_engine",
            ""
        )

        if favorite_engine:

            lines.append(
                f"- Moteur préféré : {favorite_engine}"
            )

        # -----------------------------------------------------
        # Projet actuel
        # -----------------------------------------------------

        current_project = profile.get(
            "current_project",
            ""
        )

        if current_project:

            lines.append(
                f"- Projet actuel : {current_project}"
            )

        # -----------------------------------------------------
        # Aucun profil exploitable
        # -----------------------------------------------------

        if not lines:

            return ""

        return (
            "INFORMATIONS UTILISATEUR\n"
            "Ces informations proviennent de la mémoire "
            "persistante d'ARGOS.\n\n"
            + "\n".join(lines)
        )

    # =========================================================
    # CONTEXTE SUPPLEMENTAIRE
    # =========================================================

    def add_context(
        self,
        prompt,
        context
    ):
        """
        Ajoute un contexte supplémentaire à un prompt.
        """

        if not context:

            return prompt

        return (
            prompt
            + "\n\n"
            + str(context)
        )

    # =========================================================
    # DEBUG
    # =========================================================

    def preview(self):

        return self.build()