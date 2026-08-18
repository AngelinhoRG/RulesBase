from app.retrieval import ask


def main():
    print("RulesBase dev REPL. Type a question, or 'quit' to exit.")
    while True:
        question = input("\n> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        result = ask(question)

        print(f"\nAnswer: {result['answer']}")
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  - [{s['score']}] {s['source_file']} > {s['section']}")
                print(f"    \"{s['text'][:200]}{'...' if len(s['text']) > 200 else ''}\"")


if __name__ == "__main__":
    main()
