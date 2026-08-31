import tkinter as tk
from tkinter import scrolledtext

from core.brain import Brain


class ArgosApp:
    """
    Fenêtre principale d'ARGOS.

    L'interface graphique ne contient aucune logique d'intelligence.

    Elle transmet simplement les messages au Brain
    et affiche les réponses retournées.
    """

    def __init__(self):

        # =====================================================
        # FENÊTRE
        # =====================================================

        self.root = tk.Tk()

        self.root.title("ARGOS")

        self.root.geometry("900x650")

        self.root.minsize(
            700,
            500
        )

        # =====================================================
        # CERVEAU
        # =====================================================

        self.brain = Brain()

        # =====================================================
        # INTERFACE
        # =====================================================

        self._build_interface()

    # =========================================================
    # CONSTRUCTION DE L'INTERFACE
    # =========================================================

    def _build_interface(self):

        # -----------------------------------------------------
        # Zone de conversation
        # -----------------------------------------------------

        self.chat_display = scrolledtext.ScrolledText(

            self.root,

            wrap=tk.WORD,

            state=tk.DISABLED,

            font=(
                "Segoe UI",
                11
            )

        )

        self.chat_display.pack(

            fill=tk.BOTH,

            expand=True,

            padx=15,

            pady=15

        )

        # -----------------------------------------------------
        # Zone inférieure
        # -----------------------------------------------------

        bottom_frame = tk.Frame(
            self.root
        )

        bottom_frame.pack(

            fill=tk.X,

            padx=15,

            pady=15

        )

        # -----------------------------------------------------
        # Champ de saisie
        # -----------------------------------------------------

        self.message_entry = tk.Entry(

            bottom_frame,

            font=(
                "Segoe UI",
                11
            )

        )

        self.message_entry.pack(

            side=tk.LEFT,

            fill=tk.X,

            expand=True,

            padx=(
                0,
                10
            )

        )

        # -----------------------------------------------------
        # Bouton envoyer
        # -----------------------------------------------------

        self.send_button = tk.Button(

            bottom_frame,

            text="Envoyer",

            command=self.send_message,

            font=(
                "Segoe UI",
                10
            )

        )

        self.send_button.pack(
            side=tk.RIGHT
        )

        # -----------------------------------------------------
        # Touche Entrée
        # -----------------------------------------------------

        self.message_entry.bind(

            "<Return>",

            self._on_enter

        )

        # -----------------------------------------------------
        # Message de bienvenue
        # -----------------------------------------------------

        self._display_message(

            "ARGOS",

            "Bonjour. Je suis ARGOS. "
            "Comment puis-je vous aider ?"

        )

        # -----------------------------------------------------
        # Focus automatique
        # -----------------------------------------------------

        self.message_entry.focus_set()

    # =========================================================
    # ENVOI D'UN MESSAGE
    # =========================================================

    def send_message(self):

        message = (
            self.message_entry
            .get()
            .strip()
        )

        if not message:

            return

        # -----------------------------------------------------
        # Affichage du message utilisateur
        # -----------------------------------------------------

        self._display_message(

            "Ikaris",

            message

        )

        # -----------------------------------------------------
        # Nettoyage du champ
        # -----------------------------------------------------

        self.message_entry.delete(

            0,

            tk.END

        )

        # -----------------------------------------------------
        # Désactivation temporaire
        # -----------------------------------------------------

        self.send_button.config(
            state=tk.DISABLED
        )

        self.message_entry.config(
            state=tk.DISABLED
        )

        self.root.update_idletasks()

        try:

            # ================================================
            # ARGOS TRAITE LA REQUÊTE
            # ================================================

            answer = self.brain.think(
                message
            )

            # ================================================
            # AFFICHAGE DE LA REPONSE
            # ================================================

            self._display_message(

                "ARGOS",

                answer

            )

        except Exception as error:

            self._display_message(

                "ARGOS",

                (
                    "Une erreur est survenue :\n\n"
                    f"{error}"
                )

            )

            print(
                "ERREUR ARGOS :",
                error
            )

        finally:

            # -------------------------------------------------
            # Réactivation de l'interface
            # -------------------------------------------------

            self.send_button.config(
                state=tk.NORMAL
            )

            self.message_entry.config(
                state=tk.NORMAL
            )

            self.message_entry.focus_set()

    # =========================================================
    # TOUCHE ENTREE
    # =========================================================

    def _on_enter(self, event):

        self.send_message()

        return "break"

    # =========================================================
    # AFFICHAGE
    # =========================================================

    def _display_message(
        self,
        author,
        message
    ):

        self.chat_display.config(
            state=tk.NORMAL
        )

        self.chat_display.insert(

            tk.END,

            f"{author} :\n{message}\n\n"

        )

        self.chat_display.see(
            tk.END
        )

        self.chat_display.config(
            state=tk.DISABLED
        )

    # =========================================================
    # LANCEMENT
    # =========================================================

    def run(self):

        self.root.mainloop()