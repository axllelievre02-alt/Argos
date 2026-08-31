from memory.conversation import ConversationMemory


def main():

    memory = ConversationMemory()

    # =====================================================
    # CONVERSATION
    # =====================================================

    memory.add_user_message(
        "Quel est mon jeu préféré ?"
    )

    memory.add_assistant_message(
        "Ton jeu préféré est Skies of Arcadia."
    )

    memory.add_user_message(
        "Et pourquoi ?"
    )

    memory.add_assistant_message(
        "Je n'ai pas encore cette information."
    )

    # =====================================================
    # TEST
    # =====================================================

    print("\n===== TEST CONVERSATION MEMORY =====")

    print("\nMessages :")

    for message in memory.get_messages():

        print(message)

    print("\nDernier message :")

    print(
        memory.get_last_message()
    )

    print("\nDernier message utilisateur :")

    print(
        memory.get_last_user_message()
    )

    print("\nDernière réponse ARGOS :")

    print(
        memory.get_last_assistant_message()
    )

    print("\nDernier échange :")

    print(
        memory.get_last_exchange()
    )

    print("\nContexte récent :")

    print(
        memory.get_recent_context()
    )

    print("\nRecherche 'Skies of Arcadia' :")

    print(
        memory.find_messages(
            "Skies of Arcadia"
        )
    )

    print("\n===== SUMMARY =====")

    print(
        memory.summary()
    )

    print("\n===== FIN DU TEST =====")


if __name__ == "__main__":

    main()