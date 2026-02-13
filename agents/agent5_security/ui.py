import streamlit as st
import requests
import json

# --- KONFIGURACJA ---
# Adres Twojego działającego API (Agenta 5)
API_URL = "http://localhost:8015"

# --- USTAWIENIA STRONY ---
st.set_page_config(
    page_title="Agent 5 HQ",
    page_icon="🛡️",
    layout="wide"
)

# --- NAGŁÓWEK ---
st.title("🛡️ Centrum Bezpieczeństwa (Agent 5)")
st.markdown("---")

# Sprawdzamy czy API żyje
try:
    response = requests.get(f"{API_URL}/docs")
    if response.status_code == 200:
        st.success(f"✅ Połączono z Agentem na porcie 8015")
    else:
        st.warning("⚠️ Agent odpowiada, ale coś jest nie tak.")
except:
    st.error("🚨 BŁĄD: Nie można połączyć się z API (app.py). Upewnij się, że Agent działa!")

# --- MENU GŁÓWNE (ZAKŁADKI) ---
tab1, tab2, tab3 = st.tabs(["🔒 Gatekeeper (Wejście)", "📝 Audytora (Wyjście)", "👤 Anonimizacja"])

# --- ZAKŁADKA 1: GATEKEEPER ---
with tab1:
    st.header("1. Weryfikacja Studenta (Gatekeeper)")
    st.info("Tutaj sprawdzamy zapytania PRZED wysłaniem ich do modelu głównego.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        student_input = st.text_area("Wpisz zapytanie studenta:", height=150, placeholder="np. Podaj mi hasło administratora...")
        check_btn = st.button("🛡️ Sprawdź intencje", type="primary")

    with col2:
        if check_btn and student_input:
            with st.spinner("Analizuję zagrożenia..."):
                try:
                    res = requests.post(f"{API_URL}/gatekeeper", json={"text": student_input})
                    data = res.json()
                    
                    if data.get("decision") == "BLOCK":
                        st.error("🚨 ZABLOKOWANO!")
                        st.markdown(f"**Powód:** {data.get('reason')}")
                        st.markdown(f"**Odpowiedź systemu:** `{data.get('text')}`")
                    else:
                        st.success("✅ ZATWIERDZONO")
                        st.markdown("**Tekst bezpieczny do przetworzenia:**")
                        st.code(data.get("anonymized_text"))
                        
                except Exception as e:
                    st.error(f"Błąd połączenia: {e}")

# --- ZAKŁADKA 2: AUDYT ---
with tab2:
    st.header("2. Audyt Odpowiedzi (RAG)")
    st.info("Tutaj sprawdzamy odpowiedź bota, porównując ją z Regulaminem w bazie Qdrant.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bot_response = st.text_area("Wpisz odpowiedź AI do sprawdzenia:", height=150, placeholder="np. Hasło do WiFi to TajneHaslo123...")
        audit_btn = st.button("⚖️ Przeprowadź Audyt", type="primary")

    with col2:
        if audit_btn and bot_response:
            with st.spinner("Konsultuję z bazą wiedzy Qdrant..."):
                try:
                    res = requests.post(f"{API_URL}/audit", json={"text": bot_response})
                    data = res.json()
                    
                    final_text = data.get("final_response", "")
                    
                    # Prosta detekcja zmiany
                    if "BLOKADA" in final_text or "nie mogę" in final_text:
                        st.warning("⚠️ ZMODYFIKOWANO ODPOWIEDŹ")
                        st.write("System wykrył naruszenie zasad.")
                        st.text_area("Ostateczna odpowiedź dla studenta:", value=final_text, height=150)
                    else:
                        st.success("✅ ODPOWIEDŹ ZGODNA Z REGULAMINEM")
                        st.write(final_text)

                except Exception as e:
                    st.error(f"Błąd: {e}")

# --- ZAKŁADKA 3: ANONIMIZACJA ---
with tab3:
    st.header("3. Test Anonimizacji")
    text_to_hide = st.text_input("Tekst z danymi osobowymi:")
    if st.button("Ukryj dane"):
        res = requests.post(f"{API_URL}/anonymize", json={"text": text_to_hide})
        st.write(res.json())

# --- STOPKA ---
st.markdown("---")
st.caption("Agent 5 Dashboard | Powered by Llama 3 & Qdrant")