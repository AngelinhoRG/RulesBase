from app import catalog
from app.config import DEFAULT_CATEGORY
from app.retrieval import ask


def choose_category():
    categories = catalog.list_categories()
    print(f"Categories: {', '.join(categories) if categories else '(none ingested yet)'}")
    choice = input(f"Category [{DEFAULT_CATEGORY}]: ").strip()
    return choice or DEFAULT_CATEGORY


def main():
    print("RulesBase dev REPL.")
    category = choose_category()
    game = None
    print(f"\nSearching category: {category!r} (game filter: {game or 'none'})")
    print("Commands: '/category <name>', '/game <name or blank to clear>', 'quit'\n")

    while True:
        question = input("> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        if question.startswith("/category"):
            category = question[len("/category") :].strip() or DEFAULT_CATEGORY
            print(f"Category set to {category!r}")
            continue
        if question.startswith("/game"):
            game = question[len("/game") :].strip() or None
            if game and game not in catalog.list_games(category):
                print(f"Warning: {game!r} has no rulebook in category {category!r} -- every question will return no results until you fix the category or game.")
            print(f"Game filter set to {game!r}")
            continue

        result = ask(question, category=category, game=game)

        print(f"\nAnswer: {result['answer']}")
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  - [{s['score']}] {s['source_file']} > {s['section']}")
                print(f"    \"{s['text'][:200]}{'...' if len(s['text']) > 200 else ''}\"")
        print()


if __name__ == "__main__":
    main()
