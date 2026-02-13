# Agent 5 -- Security & Compliance Layer

## Opis projektu

------------------------------------------------------------------------

## 1. Wprowadzenie

Agent 5 stanowi warstwę bezpieczeństwa i zgodności (Security 
& Compliance Layer) w architekturze systemu wieloagentowego opartego na modelach językowych (LLM). 
Jego zadaniem jest kontrola treści wejściowych oraz wyjściowych przy wykorzystaniu mechanizmu Pure Retrieval-Augmented Generation (Pure RAG).\
Pełni funkcję logicznej zapory bezpieczeństwa (**AI Firewall**)
działającej w architekturze wieloagentowej.

System realizuje kontrolę:

-    Danych wejściowych użytkownika (PRE-filter -- Gatekeeper)
-    Danych wyjściowych modelu (POST-filter -- Audit)
-    Zgodności z regulaminem przechowywanym w bazie wektorowej
    (Qdrant)
-    Rejestrowania decyzji w bazie PostgreSQL - Audit log

Kluczowe założenie:\
Wszystkie decyzje podejmowane są dynamicznie w oparciu o mechanizm Pure RAG.

------------------------------------------------------------------------

# 2. Architektura systemu

    Użytkownik
       ↓
    /gatekeeper  (PRE | Anonimizacja + RAG Policy Check)
       ↓
    Model LLM / Agent
       ↓
    /audit       (POST | Kontrola zgodności odpowiedzi)
       ↓
    Odpowiedź końcowa

------------------------------------------------------------------------

# 3. Komponenty technologiczne

  Warstwa | Technologia 
--- | --- 
API | FastAPI 
Model językowy | Ollama (llama3)
Embedding | nomic-embed-text
Baza wektorowa | Qdrant
Logi systemowe | PostgreSQL
Integracja RAG | LangChain

------------------------------------------------------------------------

# 4. Struktura projektu

    .
    ├── docker-compose.yml
    ├── app.py
    ├── ingest_security.py
    ├── requirements.txt
    ├── ui.py
    ├── resources/
    │   ├── dokumenty PDF/DOCX/TXT/JSON
    └── scripts/

### Najważniejsze pliki

-   **app.py** -- główna logika Agenta 5
-   **resources/** -- dokumenty zawierające regulaminy i polityki bezpieczeństwa wykorzystywane jako baza wiedzy
-   **docker-compose.yml** -- konfiguracja infrastruktury
-   **ingest_security.py** -- proces wektorowania dokumentów
-   **ui.py** -- interfejs testowy
------------------------------------------------------------------------

# 5 Instalacja i uruchomienie

## 5.1 Wymagania

-   Python 3.10+\
-   Docker\
-   Ollama

------------------------------------------------------------------------

## 5.2 Uruchomienie infrastruktury

``` bash
docker-compose up -d;
./agents/agent5_security/scripts/start_ui.sh
```

------------------------------------------------------------------------

## 5.3 Instalacja zależności

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 4️⃣ Uruchomienie aplikacji

``` bash
ai-stack/agents/agent5_security/scripts/start_agent5.sh
```

API dostępne pod:

    http://localhost:8015

Dokumentacja Swagger:

    http://localhost:8015/docs

UI dostępne pod:

    http://localhost:8005

------------------------------------------------------------------------

# 6. Ingestion dokumentów

Endpoint:

    POST /ingest/files

Proces:

1.  Odczyt dokumentów z katalogu `resources/`
2.  Podział na fragmenty (chunk_size = 1000, overlap = 100)
3.  Generowanie embeddingów
4.  Zapis do kolekcji `agent5_rules` w Qdrant
Wektorowa baza wiedzy stanowi jedyne źródło zasad wykorzystywanych w procesie decyzyjnym.
------------------------------------------------------------------------

# 7. Endpointy

## PRE /gatekeeper

Funkcjonalność:

-   Anonimizacja danych wrażliwych (imiona, nazwiska, PESEL, adresy).
-   Pobranie zasad z Qdrant
-   Decyzja i klasyfikacja zapytania: SAFE / DANGER

W przypadku naruszenia zasad zwracana jest decyzja **BLOCK**.

------------------------------------------------------------------------

## POST /audit

Funkcjonalność:

-   Analiza odpowiedzi wygenerowanej przez model
-   Ocena zgodności z zasadami przechowywanymi w Qdrant
-   W przypadku naruszenia zwracany komunikat:

```{=html}
<!-- -->
```
    BLOKADA: [Powód]

------------------------------------------------------------------------

# 8. Rejestrowanie zdarzeń

Tabela PostgreSQL:

    security_logs

Rejestrowane dane:

-   timestamp
-   endpoint
-   input_text
-   output_text
-   decision (PASS / BLOCK)

Mechanizm zapewnia pełną audytowalność działania systemu.

------------------------------------------------------------------------

# 9. Założenia projektowe

-   Brak reguł bezpieczeństwa o wysokim stopniu skomplikowania
-   Dynamiczne pobieranie zasad z bazy wektorowej
-   Separacja logiki aplikacyjnej od polityk
-   Deterministyczne działanie modelu (temperature = 0)
-   Możliwość aktualizacji zasad bez modyfikacji kodu
-   Decyzje podejmowane wyłącznie na podstawie wiedzy pobranej z bazy wektorowej

------------------------------------------------------------------------

# 10. Licencja i autorzy

Projekt przygotowany w celach badawczych i wdrożeniowych.

Autorzy:

-   Rafał S
-   Daniel T
-   Jan S
-   Jakub Ł


