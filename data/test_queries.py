from chromadb import Client

# Connect
client = Client()
collection = client.get_collection("railadvice_docs")

queries = [
    "Hva er ETCS?",
    "Fortell om Lars Mortvedt",
    "Hvilke prosjekter har RailAdvice gjort?",
    "Hva koster ETCS implementering?",
    "Flytoget Type 78"
]

for q in queries:
    results = collection.query(
        query_texts=[q],
        n_results=3  # number of matches you want
    )
    print(f"\nQuery: {q}")
    if results["documents"][0]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            print("Title:", meta["title"])
            print("Snippet:", doc[:300], "\n")
    else:
        print("No documents found.")
