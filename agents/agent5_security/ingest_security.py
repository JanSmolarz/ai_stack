import os
import json
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_core.documents import Document

# --- KONFIGURACJA (LOCALHOST) ---
QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
COLLECTION_NAME = "agent5_rules"
RESOURCES_DIR = "resources"

def ingest_rules():
    print(f"--- 1. Skanowanie REKURENCYJNE folderu: {RESOURCES_DIR} ---")
    
    documents = []
    if not os.path.exists(RESOURCES_DIR):
        print(f"BLAD: Nie znaleziono folderu {RESOURCES_DIR}!")
        return

    # os.walk przechodzi przez wszystkie podfoldery
    for root, dirs, files in os.walk(RESOURCES_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            # Pobieramy relatywna sciezke dla metadanych
            relative_path = os.path.relpath(file_path, RESOURCES_DIR)

            try:
                # --- OBSLUGA JSON ---
                if filename.endswith(".json"):
                    print(f"Wczytuje JSON: {relative_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                content = json.dumps(item, ensure_ascii=False, indent=2)
                                documents.append(Document(page_content=content, metadata={"source": relative_path}))
                        elif isinstance(data, dict):
                             content = json.dumps(data, ensure_ascii=False, indent=2)
                             documents.append(Document(page_content=content, metadata={"source": relative_path}))

                # --- OBSLUGA PDF ---
                elif filename.endswith(".pdf"):
                    print(f"Wczytuje PDF: {relative_path}")
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())
                
                # --- OBSLUGA DOCX ---
                elif filename.endswith(".docx"):
                    print(f"Wczytuje Word: {relative_path}")
                    loader = Docx2txtLoader(file_path)
                    documents.extend(loader.load())
                
                # --- OBSLUGA TXT ---
                elif filename.endswith(".txt"):
                    print(f"Wczytuje Text: {relative_path}")
                    loader = TextLoader(file_path, encoding="utf-8")
                    documents.extend(loader.load())
                
            except Exception as e:
                print(f"Blad przy pliku {relative_path}: {e}")

    if not documents:
        print("Nie wczytano dokumentow. Sprawdz folder resources i podfoldery!")
        return

    # --- 2. Podzial na kawalki (Chunking) ---
    print(f"--- 2. Przetwarzanie {len(documents)} fragmentow ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    # --- 3. Resetowanie Qdrant ---
    print(f"--- 3. Aktualizacja bazy Qdrant ---")
    client = QdrantClient(url=QDRANT_URL)
    
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
    )

    # --- 4. Generowanie wektorow ---
    print(f"--- 4. Generowanie wektorow i zapis do bazy ---")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    
    vector_store.add_documents(docs)
    print("--- SUKCES! Baza wiedzy (rekurencyjna) zaktualizowana ---")

if __name__ == "__main__":
    ingest_rules()
