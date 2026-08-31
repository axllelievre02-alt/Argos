from core.brain import Brain


def main():

    print("\n===== TEST BRAIN =====\n")

    # =====================================================
    # UNE SEULE INSTANCE D'ARGOS
    # =====================================================

    brain = Brain()

    # =====================================================
    # PREMIERE QUESTION
    # =====================================================

    question_1 = "Quel est mon jeu préféré ?"

    print("Question 1 :")
    print(question_1)

    print("\n===== REPONSE 1 =====")

    response_1 = brain.think(
        question_1
    )

    print(response_1)

    # =====================================================
    # DEUXIEME QUESTION
    # =====================================================

    question_2 = "Et pourquoi ?"

    print("\nQuestion 2 :")
    print(question_2)

    print("\n===== REPONSE 2 =====")

    response_2 = brain.think(
        question_2
    )

    print(response_2)

    # =====================================================
    # CONTEXTE
    # =====================================================

    print("\n===== CONTEXTE =====")

    context = brain.get_last_context()

    if context:

        print(
            context.summary()
        )

    # =====================================================
    # CONVERSATION
    # =====================================================

    print("\n===== CONVERSATION =====")

    for message in brain.get_conversation():

        print(
            f"{message['role']} : "
            f"{message['content']}"
        )

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n===== SUMMARY =====")

    print(
        brain.summary()
    )

    print("\n===== FIN DU TEST =====")


if __name__ == "__main__":

    main()