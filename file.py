
from creating_vectordatabase import build_vector_database
from Reterival_engine import create_chat_engine


def main():
    
    index, nodes = build_vector_database(force_rebuild=False)

    

    chat_engine = create_chat_engine(index, nodes)

    print("🤖 Laptop Assistant Ready!")
    print("-" * 40)
    print("Type 'exit' to quit")
    print("-" * 40 + "\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n AI: Goodbye! \n")
                break

            print("    Thinking...", end="\r")
            
            response = chat_engine.chat(user_input)
            
            
            print(f" AI: {response}\n")

        except KeyboardInterrupt:
            print("\n\n AI: Goodbye! \n")
            break
        except Exception as e:
            print(f"\n Error: {e}\n")


if __name__ == "__main__":
    main()