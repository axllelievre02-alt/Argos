import json
from pathlib import Path


class ProfileMemory:
    """
    Mémoire persistante du profil utilisateur d'ARGOS.

    Cette classe est responsable de la sauvegarde et de la lecture
    des informations stables concernant l'utilisateur.

    Elle est totalement indépendante du modèle de langage.

    Le modèle ne décide jamais directement de ce qui est enregistré
    dans le profil.
    """

    def __init__(self, file_path=None):

        # =====================================================
        # CHEMIN DU FICHIER
        # =====================================================

        if file_path is None:

            base_directory = (
                Path(__file__).resolve().parent.parent
            )

            file_path = (
                base_directory
                / "data"
                / "profile.json"
            )

        self.file_path = Path(file_path)

        # =====================================================
        # INITIALISATION
        # =====================================================

        self._ensure_file()

    # =========================================================
    # PROFIL PAR DEFAUT
    # =========================================================

    def _default_profile(self):

        return {
            "name": "",
            "language": "fr",
            "favorite_game": "",
            "favorite_engine": "",
            "current_project": ""
        }

    # =========================================================
    # INITIALISATION DU FICHIER
    # =========================================================

    def _ensure_file(self):

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.file_path.exists():

            self._write(
                self._default_profile()
            )

    # =========================================================
    # LECTURE
    # =========================================================

    def load(self):

        try:

            with self.file_path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            # Le fichier doit obligatoirement
            # contenir un dictionnaire.

            if not isinstance(data, dict):

                return self._default_profile()

            # -------------------------------------------------
            # Compléter les champs manquants
            # -------------------------------------------------

            default = self._default_profile()

            for key, value in default.items():

                if key not in data:

                    data[key] = value

            return data

        except (
            json.JSONDecodeError,
            OSError
        ):

            # Si le fichier est vide ou corrompu,
            # ARGOS revient à un profil propre.

            profile = self._default_profile()

            self._write(profile)

            return profile

    # =========================================================
    # ECRITURE
    # =========================================================

    def _write(self, data):

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary_file = self.file_path.with_suffix(
            ".tmp"
        )

        with temporary_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        temporary_file.replace(
            self.file_path
        )

    # =========================================================
    # MODIFICATION
    # =========================================================

    def set(self, key, value):

        profile = self.load()

        profile[key] = value

        self._write(profile)

    # =========================================================
    # LECTURE D'UNE VALEUR
    # =========================================================

    def get(self, key, default=None):

        profile = self.load()

        return profile.get(
            key,
            default
        )

    # =========================================================
    # VERIFICATION
    # =========================================================

    def exists(self, key):

        profile = self.load()

        return key in profile

    # =========================================================
    # SUPPRESSION
    # =========================================================

    def remove(self, key):

        profile = self.load()

        if key in profile:

            del profile[key]

            self._write(profile)

    # =========================================================
    # REINITIALISATION
    # =========================================================

    def reset(self):

        self._write(
            self._default_profile()
        )

    # =========================================================
    # INFORMATIONS
    # =========================================================

    def summary(self):

        profile = self.load()

        return {
            "file": str(self.file_path),
            "fields": list(profile.keys()),
            "name_set": bool(profile.get("name")),
            "language": profile.get("language", "fr")
        }