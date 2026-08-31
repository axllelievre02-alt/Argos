from memory.extractor import MemoryExtractor


def main():

    extractor = MemoryExtractor()

    print("\n===== TEST MEMORY EXTRACTOR =====\n")

    messages = [

        "Mon jeu préféré est Skies of Arcadia.",

        "Mon moteur préféré est Unreal Engine.",

        "Je travaille sur ARGOS.",

        "Bonjour ARGOS.",

    ]

    for message in messages:

        print(
            f"Message : {message}"
        )

        result = extractor.extract(
            message
        )

        print(
            f"Résultat : {result}\n"
        )

    print("===== SUMMARY =====")

    print(
        extractor.summary()
    )

    print(
        "\n===== FIN DU TEST ====="
    )


if __name__ == "__main__":

    main()