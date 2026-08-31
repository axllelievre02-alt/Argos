from core.brain import Brain


def main():

    brain = Brain()

    print("\n===== TEST KNOWLEDGE MEMORY =====\n")

    questions = [

        "Quel est mon jeu préféré ?",

        "Quel est mon moteur préféré ?",

        "Quel est mon projet actuel ?",

        "Que sais-tu sur moi ?"

    ]

    for question in questions:

        print(
            f"\nQuestion : {question}"
        )

        response = brain.think(
            question
        )

        print(
            f"Réponse : {response}"
        )

    print(
        "\n===== FIN DU TEST ====="
    )


if __name__ == "__main__":

    main()