from core.base_engine import BaseEngine

import re
import unicodedata


class KnowledgeEngine(BaseEngine):
    """
    KnowledgeEngine
    ===============

    Moteur de connaissances personnelles d'ARGOS.

    Responsabilités :

        - lire ProfileMemory
        - utiliser ConversationMemory
        - comprendre les questions personnelles
        - résoudre les références contextuelles
        - tolérer certaines fautes d'orthographe
        - ne jamais modifier la mémoire
        - ne jamais inventer une information absente

    Exemple :

        Quel est mon jeu préféré ?
        -> Ton jeu préféré est Skies of Arcadia.

        Pourquoi j'aime mon jeu préféré ?
        -> Tu aimes Skies of Arcadia parce que ...

        Et pourquoi ?
        -> résolution à partir de la conversation précédente.

    Architecture :

        Brain
          ↓
        Executor
          ↓
        EngineManager
          ↓
        KnowledgeEngine
          ↓
        ProfileMemory
          +
        ConversationMemory
    """

    def __init__(
        self,
        profile_memory=None,
        conversation_memory=None
    ):

        super().__init__(
            name="knowledge",
            priority=10,
            capabilities=[
                "knowledge",
                "profile_knowledge",
                "personal_information",
                "context_resolution",
                "spelling_tolerance"
            ]
        )

        self.profile_memory = profile_memory
        self.conversation_memory = conversation_memory

        # =====================================================
        # ALIAS DES CHAMPS
        # =====================================================

        self.field_aliases = {

            # -------------------------------------------------
            # NOM
            # -------------------------------------------------

            "name": [

                "nom",
                "prenom",
                "prénom",

                "comment je m appelle",
                "comment je m'appelle",

                "qui suis je",
                "qui suis-je"

            ],

            # -------------------------------------------------
            # JEU PREFERE
            # -------------------------------------------------

            "favorite_game": [

                "jeu prefere",
                "jeu préféré",

                "jeu favori",

                "jeu favorit",

                "mon jeu prefere",
                "mon jeu préféré",

                "mon jeux prefere",
                "mon jeux préféré",

                "quel est mon jeu",
                "quelle est mon jeu",

                "quel est mon jeu prefere",
                "quel est mon jeu préféré",

                "quelle est mon jeu prefere",
                "quelle est mon jeu préféré"

            ],

            # -------------------------------------------------
            # RAISON DU JEU PREFERE
            # -------------------------------------------------

            "favorite_game_reason": [

                "pourquoi j aime mon jeu prefere",
                "pourquoi j'aime mon jeu prefere",

                "pourquoi j aime mon jeu préféré",
                "pourquoi j'aime mon jeu préféré",

                "pourquoi j aime ce jeu",
                "pourquoi j'aime ce jeu",

                "raison de mon jeu prefere",
                "raison de mon jeu préféré",

                "raison pour laquelle j aime mon jeu",
                "raison pour laquelle j'aime mon jeu",

                "pour quelle raison j aime mon jeu",
                "pour quelle raison j'aime mon jeu",

                "quelle est la raison de mon jeu prefere",
                "quelle est la raison de mon jeu préféré"

            ],

            # -------------------------------------------------
            # MOTEUR PREFERE
            # -------------------------------------------------

            "favorite_engine": [

                "moteur prefere",
                "moteur préféré",

                "moteur favori",

                "mon moteur prefere",
                "mon moteur préféré",

                "quel est mon moteur prefere",
                "quel est mon moteur préféré",

                "quelle est mon moteur prefere",
                "quelle est mon moteur préféré"

            ],

            # -------------------------------------------------
            # PROJET ACTUEL
            # -------------------------------------------------

            "current_project": [

                "projet actuel",
                "projet en cours",

                "mon projet",

                "sur quel projet je travaille",

                "sur quoi je travaille",

                "quel est mon projet",

                "quel est mon projet actuel"

            ],

            # -------------------------------------------------
            # LANGUE
            # -------------------------------------------------

            "language": [

                "langue",
                "langage",

                "quelle langue",

                "ma langue",

                "quelle est ma langue"

            ]
        }

    # =========================================================
    # NORMALISATION
    # =========================================================

    @staticmethod
    def normalize(text):
        """
        Normalise un texte pour permettre :

            - comparaison sans accents
            - tolérance aux apostrophes
            - suppression de ponctuation
            - comparaison insensible à la casse
        """

        if not text:
            return ""

        text = str(
            text
        ).lower().strip()

        # -----------------------------------------------------
        # Accents
        # -----------------------------------------------------

        text = unicodedata.normalize(
            "NFD",
            text
        )

        text = "".join(

            char

            for char in text

            if unicodedata.category(char) != "Mn"

        )

        # -----------------------------------------------------
        # Apostrophes
        # -----------------------------------------------------

        text = text.replace(
            "’",
            "'"
        )

        text = text.replace(
            "`",
            "'"
        )

        # Une apostrophe devient un espace.
        #
        # "j'aime" -> "j aime"

        text = text.replace(
            "'",
            " "
        )

        # -----------------------------------------------------
        # Ponctuation
        # -----------------------------------------------------

        text = re.sub(
            r"[^a-z0-9\s-]",
            " ",
            text
        )

        # -----------------------------------------------------
        # Espaces multiples
        # -----------------------------------------------------

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # PROFIL
    # =========================================================

    def _get_profile(self):
        """
        Récupère le dictionnaire du profil.

        Compatible avec plusieurs interfaces possibles
        de ProfileMemory.
        """

        if self.profile_memory is None:
            return {}

        # -----------------------------------------------------
        # Interface load()
        # -----------------------------------------------------

        if hasattr(
            self.profile_memory,
            "load"
        ):

            try:

                profile = (
                    self.profile_memory.load()
                )

                if isinstance(
                    profile,
                    dict
                ):

                    return profile

            except Exception:
                pass

        # -----------------------------------------------------
        # Interface get_profile()
        # -----------------------------------------------------

        if hasattr(
            self.profile_memory,
            "get_profile"
        ):

            try:

                profile = (
                    self.profile_memory
                    .get_profile()
                )

                if isinstance(
                    profile,
                    dict
                ):

                    return profile

            except Exception:
                pass

        # -----------------------------------------------------
        # Attribut profile
        # -----------------------------------------------------

        if hasattr(
            self.profile_memory,
            "profile"
        ):

            profile = (
                self.profile_memory.profile
            )

            if isinstance(
                profile,
                dict
            ):

                return profile

        # -----------------------------------------------------
        # Attribut data
        # -----------------------------------------------------

        if hasattr(
            self.profile_memory,
            "data"
        ):

            data = (
                self.profile_memory.data
            )

            if isinstance(
                data,
                dict
            ):

                return data

        # -----------------------------------------------------
        # Dictionnaire direct
        # -----------------------------------------------------

        if isinstance(
            self.profile_memory,
            dict
        ):

            return self.profile_memory

        return {}

    # =========================================================
    # VALEUR DU PROFIL
    # =========================================================

    def _get_value(
        self,
        field
    ):

        profile = self._get_profile()

        if not profile:
            return None

        value = profile.get(
            field
        )

        if value is None:
            return None

        if isinstance(
            value,
            str
        ):

            value = value.strip()

            if not value:
                return None

        return value

    # =========================================================
    # LEVENSHTEIN
    # =========================================================

    @staticmethod
    def _levenshtein(
        a,
        b
    ):
        """
        Distance de Levenshtein.

        Permet de comparer des mots malgré
        certaines fautes de frappe.
        """

        if a == b:
            return 0

        if not a:
            return len(b)

        if not b:
            return len(a)

        previous = list(
            range(
                len(b) + 1
            )
        )

        for i, char_a in enumerate(
            a,
            start=1
        ):

            current = [i]

            for j, char_b in enumerate(
                b,
                start=1
            ):

                insertion = (
                    current[j - 1] + 1
                )

                deletion = (
                    previous[j] + 1
                )

                substitution = (
                    previous[j - 1]
                )

                if char_a != char_b:

                    substitution += 1

                current.append(
                    min(
                        insertion,
                        deletion,
                        substitution
                    )
                )

            previous = current

        return previous[-1]

    # =========================================================
    # SIMILARITE
    # =========================================================

    @classmethod
    def _similar(
        cls,
        text,
        candidate,
        threshold=0.80
    ):
        """
        Compare deux textes avec tolérance
        aux fautes d'orthographe.
        """

        text = cls.normalize(
            text
        )

        candidate = cls.normalize(
            candidate
        )

        if not text or not candidate:
            return False

        if text == candidate:
            return True

        distance = cls._levenshtein(
            text,
            candidate
        )

        max_length = max(
            len(text),
            len(candidate)
        )

        if max_length == 0:
            return True

        similarity = (
            1 -
            (
                distance /
                max_length
            )
        )

        return similarity >= threshold

    # =========================================================
    # DETECTION D'UN MOT
    # =========================================================

    def _contains_similar_word(
        self,
        words,
        candidates
    ):
        """
        Vérifie si une liste de mots contient
        un mot suffisamment proche d'un candidat.
        """

        for word in words:

            for candidate in candidates:

                if self._similar(
                    word,
                    candidate
                ):

                    return True

        return False

    # =========================================================
    # DETECTION DU CHAMP
    # =========================================================

    def detect_field(
        self,
        message
    ):
        """
        Détermine quel champ du profil est concerné.
        """

        normalized = self.normalize(
            message
        )

        if not normalized:
            return None

        # -----------------------------------------------------
        # Expressions exactes / connues
        # -----------------------------------------------------

        for field, aliases in (
            self.field_aliases.items()
        ):

            for alias in aliases:

                alias_normalized = (
                    self.normalize(
                        alias
                    )
                )

                if alias_normalized in normalized:

                    return field

        words = normalized.split()

        # -----------------------------------------------------
        # JEU
        # -----------------------------------------------------

        has_game = (
            self._contains_similar_word(
                words,
                [
                    "jeu",
                    "jeux"
                ]
            )
        )

        # -----------------------------------------------------
        # FAVORI
        # -----------------------------------------------------

        has_favorite = (
            self._contains_similar_word(
                words,
                [
                    "prefere",
                    "favori",
                    "favorit"
                ]
            )
        )

        if has_game and has_favorite:

            return "favorite_game"

        # -----------------------------------------------------
        # MOTEUR
        # -----------------------------------------------------

        has_engine = (
            self._contains_similar_word(
                words,
                [
                    "moteur"
                ]
            )
        )

        if has_engine and has_favorite:

            return "favorite_engine"

        # -----------------------------------------------------
        # PROJET
        # -----------------------------------------------------

        if self._contains_similar_word(
            words,
            [
                "projet"
            ]
        ):

            return "current_project"

        # -----------------------------------------------------
        # LANGUE
        # -----------------------------------------------------

        if self._contains_similar_word(
            words,
            [
                "langue",
                "langage"
            ]
        ):

            return "language"

        # -----------------------------------------------------
        # NOM
        # -----------------------------------------------------

        if self._contains_similar_word(
            words,
            [
                "nom",
                "prenom"
            ]
        ):

            return "name"

        return None

    # =========================================================
    # CONVERSATION
    # =========================================================

    def _get_conversation(self):
        """
        Récupère l'historique conversationnel.
        """

        if self.conversation_memory is None:
            return []

        # -----------------------------------------------------
        # Interface get_messages()
        # -----------------------------------------------------

        if hasattr(
            self.conversation_memory,
            "get_messages"
        ):

            try:

                messages = (
                    self.conversation_memory
                    .get_messages()
                )

                if isinstance(
                    messages,
                    list
                ):

                    return messages

            except Exception:
                pass

        # -----------------------------------------------------
        # Attribut messages
        # -----------------------------------------------------

        if hasattr(
            self.conversation_memory,
            "messages"
        ):

            messages = (
                self.conversation_memory.messages
            )

            if isinstance(
                messages,
                list
            ):

                return messages

        return []

    # =========================================================
    # DERNIER MESSAGE UTILISATEUR
    # =========================================================

    def _get_last_user_message(self):
        """
        Retourne le dernier message de l'utilisateur
        présent dans ConversationMemory.
        """

        messages = (
            self._get_conversation()
        )

        for item in reversed(
            messages
        ):

            if isinstance(
                item,
                dict
            ):

                role = item.get(
                    "role",
                    ""
                )

                content = item.get(
                    "content",
                    ""
                )

                if (
                    role == "user"
                    and content
                ):

                    return content

            elif isinstance(
                item,
                str
            ):

                return item

        return None

    # =========================================================
    # DERNIER SUJET PERTINENT
    # =========================================================

    def _get_last_relevant_field(self):
        """
        Cherche dans l'historique le dernier champ personnel
        identifiable.

        Permet par exemple :

            Quel est mon jeu préféré ?
            Et pourquoi ?

        de résoudre "pourquoi" vers
        favorite_game_reason.
        """

        messages = (
            self._get_conversation()
        )

        for item in reversed(
            messages
        ):

            if not isinstance(
                item,
                dict
            ):

                continue

            role = item.get(
                "role",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            if role != "user":
                continue

            if not content:
                continue

            field = self.detect_field(
                content
            )

            if field:

                return field

        return None

    # =========================================================
    # QUESTION POURQUOI
    # =========================================================

    def _is_reason_question(
        self,
        message
    ):
        """
        Détecte une demande de justification.
        """

        normalized = self.normalize(
            message
        )

        if not normalized:
            return False

        reason_patterns = [

            "pourquoi",

            "pour quelle raison",

            "quelle est la raison",

            "raison pour laquelle"

        ]

        return any(
            pattern in normalized
            for pattern in reason_patterns
        )

    # =========================================================
    # QUESTION CONTEXTUELLE
    # =========================================================

    def _is_contextual_question(
        self,
        message
    ):
        """
        Détecte une question dépendant probablement
        du message précédent.
        """

        normalized = self.normalize(
            message
        )

        contextual_patterns = [

            "et pourquoi",
            "et comment",

            "pourquoi alors",

            "et pourquoi ca",
            "et pourquoi cela",

            "et comment ca",
            "et comment cela",

            "et donc",
            "et alors"

        ]

        return any(
            pattern in normalized
            for pattern in contextual_patterns
        )

    # =========================================================
    # RESOLUTION CONTEXTUELLE
    # =========================================================

    def _resolve_context_field(
        self,
        message
    ):
        """
        Résout les questions incomplètes à partir
        de la conversation précédente.
        """

        normalized = self.normalize(
            message
        )

        if not normalized:
            return None

        # =====================================================
        # "ET POURQUOI ?"
        # =====================================================

        if normalized in {

            "pourquoi",

            "et pourquoi",

            "pour quelle raison",

            "et pour quelle raison",

            "quelle est la raison",

            "et quelle est la raison"

        }:

            previous_field = (
                self._get_last_relevant_field()
            )

            if previous_field == "favorite_game":

                return (
                    "favorite_game_reason"
                )

            if previous_field == "favorite_engine":

                return (
                    "favorite_engine_reason"
                )

            return previous_field

        # =====================================================
        # REFERENCES COURTES
        # =====================================================

        # Ces formulations ne précisent pas de champ. Elles ne
        # peuvent donc être résolues que si la conversation porte
        # déjà sur une information personnelle identifiable.

        short_references = {

            "et ca",
            "et cela",

            "et lui",
            "et elle",

            "et ce dernier",
            "et cette derniere",

            "lequel",
            "laquelle",

            "et lequel",
            "et laquelle"

        }

        if normalized in short_references:

            return self._get_last_relevant_field()

        # =====================================================
        # POURQUOI + JEU
        # =====================================================

        if self._is_reason_question(
            message
        ):

            if (
                "jeu" in normalized
                or "jeux" in normalized
            ):

                return (
                    "favorite_game_reason"
                )

            # -------------------------------------------------
            # Exemple :
            #
            # "Pourquoi j'aime ça ?"
            #
            # Si le dernier sujet était le jeu préféré,
            # on utilise la raison du jeu.
            # -------------------------------------------------

            previous_field = (
                self._get_last_relevant_field()
            )

            if previous_field == "favorite_game":

                return (
                    "favorite_game_reason"
                )

        return None

    # =========================================================
    # FORMATAGE
    # =========================================================

    def _format_value(
        self,
        field,
        value
    ):
        """
        Transforme une valeur brute du profil
        en réponse naturelle.
        """

        if value is None:
            return None

        # -----------------------------------------------------
        # NOM
        # -----------------------------------------------------

        if field == "name":

            return (
                f"Tu t'appelles {value}."
            )

        # -----------------------------------------------------
        # JEU PREFERE
        # -----------------------------------------------------

        if field == "favorite_game":

            return (
                f"Ton jeu préféré est {value}."
            )

        # -----------------------------------------------------
        # RAISON DU JEU
        # -----------------------------------------------------

        if field == "favorite_game_reason":

            game = self._get_value(
                "favorite_game"
            )

            reason = str(
                value
            ).strip().rstrip(
                "."
            )

            # Les raisons apprises depuis un message utilisateur
            # sont souvent formulées à la première personne.
            # La réponse d'ARGOS s'adresse à l'utilisateur :
            # elle doit donc employer la deuxième personne.

            first_person_replacements = {
                "je l'adore": "tu l'adores",
                "je l'aime": "tu l'aimes",
                "j'adore": "tu adores",
                "j'aime": "tu aimes",
                "je préfère": "tu préfères"
            }

            reason_lower = reason.lower()

            for first_person, second_person in (
                first_person_replacements.items()
            ):

                if reason_lower.startswith(
                    first_person
                ):

                    reason = (
                        second_person +
                        reason[len(first_person):]
                    )

                    break

            if game:

                return (
                    f"Tu aimes {game} "
                    f"parce que {reason}."
                )

            return (
                reason + "."
            )

        # -----------------------------------------------------
        # MOTEUR PREFERE
        # -----------------------------------------------------

        if field == "favorite_engine":

            return (
                f"Ton moteur préféré "
                f"est {value}."
            )

        # -----------------------------------------------------
        # PROJET
        # -----------------------------------------------------

        if field == "current_project":

            return (
                f"Ton projet actuel "
                f"est {value}."
            )

        # -----------------------------------------------------
        # LANGUE
        # -----------------------------------------------------

        if field == "language":

            return (
                f"Ta langue préférée "
                f"est {value}."
            )

        return str(
            value
        )

    # =========================================================
    # CONSTRUCTION DU RESULTAT
    # =========================================================

    def _result(
        self,
        handled,
        field=None,
        known=False,
        answer=None,
        value=None
    ):
        """
        Construit un résultat compatible avec le Brain.

        IMPORTANT :

        "content" contient la réponse directe attendue
        par Brain.think().
        """

        return {

            "handled": handled,

            "field": field,

            "known": known,

            "answer": answer,

            "value": value,

            # -------------------------------------------------
            # Compatibilité Brain / ResponseManager
            # -------------------------------------------------

            "content": answer

        }

    # =========================================================
    # REPONSE
    # =========================================================

    def answer(
        self,
        message
    ):
        """
        Analyse une question personnelle et tente
        d'y répondre à partir de la mémoire.
        """

        if not message:

            return self._result(
                handled=False
            )

        # =====================================================
        # RESOLUTION CONTEXTUELLE
        # =====================================================

        field = (
            self._resolve_context_field(
                message
            )
        )

        # =====================================================
        # DETECTION NORMALE
        # =====================================================

        if field is None:

            field = self.detect_field(
                message
            )

        # =====================================================
        # AUCUN CHAMP CONCERNE
        # =====================================================

        if field is None:

            return self._result(
                handled=False
            )

        # =====================================================
        # RECUPERATION DE LA VALEUR
        # =====================================================

        value = self._get_value(
            field
        )

        # =====================================================
        # INFORMATION INCONNUE
        # =====================================================

        if value is None:

            # -------------------------------------------------
            # Cas spécial : raison du jeu
            # -------------------------------------------------

            if field == "favorite_game_reason":

                game = self._get_value(
                    "favorite_game"
                )

                if game:

                    answer = (
                        f"Je sais que ton jeu "
                        f"préféré est {game}, "
                        "mais je ne connais pas "
                        "encore la raison pour "
                        "laquelle tu l'aimes."
                    )

                else:

                    answer = (
                        "Je ne connais pas encore "
                        "la raison pour laquelle "
                        "tu aimes ce jeu."
                    )

            else:

                answer = (
                    "Je ne connais pas encore "
                    "cette information."
                )

            return self._result(
                handled=True,
                field=field,
                known=False,
                answer=answer,
                value=None
            )

        # =====================================================
        # INFORMATION CONNUE
        # =====================================================

        answer = self._format_value(
            field,
            value
        )

        return self._result(
            handled=True,
            field=field,
            known=True,
            answer=answer,
            value=value
        )

    # =========================================================
    # EXECUTION ARGOS
    # =========================================================

    def execute(
        self,
        message,
        context=None
    ):
        """
        Point d'entrée utilisé par EngineManager.
        """

        result = self.answer(
            message
        )

        # -----------------------------------------------------
        # Communication avec Context
        # -----------------------------------------------------

        if context is not None:

            if result.get(
                "handled"
            ):

                context.log(
                    "KnowledgeEngine : "
                    f"champ={result.get('field')} "
                    f"connu={result.get('known')}"
                )

                # -------------------------------------------------
                # Données structurées disponibles aux autres
                # moteurs.
                # -------------------------------------------------

                context.set(
                    "knowledge",
                    result
                )

                context.set(
                    "knowledge_field",
                    result.get(
                        "field"
                    )
                )

                context.set(
                    "knowledge_value",
                    result.get(
                        "value"
                    )
                )

                context.set(
                    "knowledge_known",
                    result.get(
                        "known"
                    )
                )

                context.set(
                    "knowledge_answer",
                    result.get(
                        "answer"
                    )
                )

        return result

    # =========================================================
    # ALIAS PUBLICS
    # =========================================================

    def process(
        self,
        message
    ):

        return self.answer(
            message
        )

    def handle(
        self,
        message
    ):

        return self.answer(
            message
        )

    def query(
        self,
        message
    ):

        return self.answer(
            message
        )

