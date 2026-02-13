import os
import uvicorn
import uuid
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# LangChain & Qdrant & Ollama
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient
from qdrant_client.http import models

# --- KONFIGURACJA ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "agent5_rules"
RESOURCES_DIR = "resources"

# Konfiguracja PostgreSQL
# WAŻNE: Podmień "twoje_haslo" na prawdziwe hasło do bazy!
PG_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "twoje_haslo", 
    "port": "5432"
}

app = FastAPI(title="Agent 5 - Security & Compliance (Pure RAG)")

# 1. Inicjalizacja modeli
print("--- Inicjalizacja Modeli AI ---")
llm = ChatOllama(model="llama3", base_url=OLLAMA_URL, temperature=0)
embeddings = OllamaEmbeddings(base_url=OLLAMA_URL, model="nomic-embed-text")

# 2. Połączenie z Qdrant
print("--- Łączenie z Qdrant ---")
client = QdrantClient(url=QDRANT_URL)
vector_store = Qdrant(
    client=client, 
    collection_name=COLLECTION_NAME, 
    embeddings=embeddings
)

class SecurityRequest(BaseModel):
    text: str

# --- POMOCNICZE: BAZA DANYCH SQL ---

def init_db():
    """Tworzy tabelę logów, jeśli nie istnieje."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS security_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint VARCHAR(50),
                input_text TEXT,
                output_text TEXT,
                decision VARCHAR(20)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("--- BAZA DANYCH: Tabela logów gotowa ---")
    except Exception as e:
        print(f"--- BAZA DANYCH BŁĄD (Sprawdź hasło w PG_CONFIG!): {e} ---")

# Uruchamiamy inicjalizację bazy przy starcie
init_db()

def log_to_db(endpoint, input_text, output_text, decision):
    """Zapisuje zdarzenie do PostgreSQL."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        sql = "INSERT INTO security_logs (endpoint, input_text, output_text, decision) VALUES (%s, %s, %s, %s)"
        cur.execute(sql, (endpoint, input_text, output_text, decision))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Błąd logowania DB: {e}")

# --- SEKCJA 1: INGESTION (WGRYWANIE DANYCH) ---

@app.post("/ingest/files")
def ingest_from_files():
    """Wczytuje PDF, DOCX i TXT z folderu resources do Qdrant."""
    if not os.path.exists(RESOURCES_DIR):
        raise HTTPException(status_code=404, detail=f"Folder {RESOURCES_DIR} nie istnieje")

    documents = []
    for filename in os.listdir(RESOURCES_DIR):
        file_path = os.path.join(RESOURCES_DIR, filename)
        try:
            loader = None
            if filename.endswith(".pdf"): loader = PyPDFLoader(file_path)
            elif filename.endswith(".docx"): loader = Docx2txtLoader(file_path)
            elif filename.endswith(".txt"): loader = TextLoader(file_path, encoding="utf-8")
            
            if loader: 
                print(f"Wczytuję: {filename}")
                documents.extend(loader.load())
        except Exception as e:
            print(f"Błąd pliku {filename}: {e}")

    if not documents:
        return {"message": "Brak dokumentów do wczytania."}

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    # Dodawanie do Qdrant
    vector_store.add_documents(docs)
    return {"status": "success", "chunks_added": len(docs)}

# --- SEKCJA 2: REAL-TIME SECURITY (LOGIKA AGENTA) ---

@app.post("/gatekeeper")
def gatekeeper(request: SecurityRequest):
    """
    CZYSTY RAG GATEKEEPER:
    1. Anonimizacja.
    2. Pobranie zasad z Qdrant.
    3. Decyzja TYLKO na podstawie pobranych zasad.
    """
    print(f"[GATEKEEPER] Otrzymano: {request.text}")

    # --- 1. ANONIMIZACJA ---
    anon_prompt = ChatPromptTemplate.from_template(
        """Jesteś oficerem RODO. Zastąp dane wrażliwe (Imiona, Nazwiska, PESEL, Adresy) etykietą [DANE].
        Nie zmieniaj reszty treści.
        Tekst: "{text}"
        Wyjście:"""
    )
    anonymized_text = (anon_prompt | llm | StrOutputParser()).invoke({"text": request.text}).strip()

    # --- 2. RAG (Pobranie zasad) ---
    # Szukamy zasad pasujących do zapytania studenta
    docs = vector_store.similarity_search(request.text, k=3)
    rules_context = "\n".join([f"- {d.page_content}" for d in docs])
    
    if not rules_context:
        # Jeśli baza milczy, uznajemy, że nie ma zakazu.
        rules_context = "Brak specyficznych zakazów dotyczących tego tematu."

    print(f"[RAG Rules Found]: {rules_context[:100]}...")

    # --- 3. DETEKCJA (SAFE / DANGER) ---
    # Model działa teraz jako sędzia, który patrzy tylko w dostarczony "kodeks"
    attack_prompt = ChatPromptTemplate.from_template(
        """Jesteś AI Firewall. Twoim zadaniem jest ocena tekstu WYŁĄCZNIE w oparciu o poniższe zasady.
        
        OBOWIĄZUJĄCE ZASADY (z Bazy Wiedzy):
        {rules}
        
        INSTRUKCJA:
        1. Przeanalizuj tekst użytkownika.
        2. Czy tekst łamie którąkolwiek z powyższych zasad?
        3. Jeśli TAK -> Odpowiedz "DANGER".
        4. Jeśli NIE (lub brak zasad) -> Odpowiedz "SAFE".
        
        TEKST UŻYTKOWNIKA: "{text}"
        
        Decyzja (tylko jedno słowo: SAFE lub DANGER):
        """
    )
    
    verdict = (attack_prompt | llm | StrOutputParser()).invoke({
        "text": request.text, 
        "rules": rules_context
    }).strip().upper()
    
    print(f"[GATEKEEPER] Werdykt AI: {verdict}")

    if "DANGER" in verdict:
        msg = "Dostęp zablokowany na podstawie Regulaminu Bezpieczeństwa."
        log_to_db("/gatekeeper", request.text, msg, "BLOCK")
        return {
            "decision": "BLOCK", 
            "reason": "RAG Policy Violation", 
            "text": msg,
            "anonymized_preview": anonymized_text 
        }

    log_to_db("/gatekeeper", request.text, anonymized_text, "PASS")
    return {"decision": "PASS", "anonymized_text": anonymized_text}

@app.post("/audit")
def audit_response(request: SecurityRequest):
    """
    CZYSTY RAG AUDIT:
    Sprawdza odpowiedź bota wyłącznie pod kątem zasad w Qdrant.
    """
    print(f"[AUDIT] Weryfikuję odpowiedź: {request.text}")
    
    docs = vector_store.similarity_search(request.text, k=3)
    context = "\n".join([f"- {d.page_content}" for d in docs])
    
    if not context:
        context = "Brak specyficznych wytycznych w bazie."

    audit_prompt = ChatPromptTemplate.from_template(
        """Jesteś audytorem. Oceniasz odpowiedź bota na podstawie dostarczonego REGULAMINU.
        
        REGULAMIN (z Qdrant):
        {context}
        
        ODPOWIEDŹ BOTA:
        "{text}"
        
        Czy ta odpowiedź narusza powyższy regulamin (np. ujawnia dane, które są w nim chronione)?
        Jeśli TAK -> Zwróć tekst zaczynający się od: "BLOKADA: [Powód]"
        Jeśli NIE -> Zwróć oryginalny tekst bez zmian.
        """
    )
    
    final_output = (audit_prompt | llm | StrOutputParser()).invoke({
        "context": context,
        "text": request.text
    }).strip()

    status = "BLOCK" if "BLOKADA" in final_output else "PASS"
    log_to_db("/audit", request.text, final_output, status)

    return {"status": "audited", "final_response": final_output}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8015)
