from core.brain import Brain


def main():

    brain = Brain()

    print("\n===== TEST APPRENTISSAGE =====\n")

    print("Profil AVANT :")
    print(
        brain.get_profile()
    )

    print("\n----- MESSAGE -----")

    message = (
        "Mon moteur préféré est Unreal Engine."
    )

    print(
        message
    )

    print("\n----- ARGOS -----")

    response = brain.think(
        message
    )

    print(
        "\nRéponse :",
        response
    )

    print("\n----- PROFIL APRES -----")

    print(
        brain.get_profile()
    )

    print("\n===== FIN DU TEST =====")


if __name__ == "__main__":

    main()