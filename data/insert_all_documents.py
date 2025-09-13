import os
import json
from chromadb import Client

client = Client(persist_directory="./chroma_db")  # files stored locally
collection = client.get_or_create_collection(name="railadvice_documents")


# Use your collection name
collection_name = "railadvice_documents"
if collection_name in [col.name for col in client.list_collections()]:
    collection = client.get_collection(collection_name)
else:
    collection = client.create_collection(name=collection_name)

# Root folder containing JSON files
folder_path = "./data"

json_files = []

# Recursively find all JSON files
for root, dirs, files in os.walk(folder_path):
    for file in files:
        if file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print("JSON files found:", len(json_files))

# Load and insert documents
for file_path in json_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure it's a list of dicts
            if isinstance(data, dict):
                data = [data]
            for doc in data:
                # You can adjust fields for ChromaDB
                collection.add(
                    documents=[json.dumps(doc)],
                    metadatas=[{"source": file_path}],
                    ids=[f"{file_path}-{data.index(doc)}"]
                )
        print(f"Inserted {file_path}")
    except Exception as e:
        print(f"Error with {file_path}: {e}")

print("All documents processed.")
