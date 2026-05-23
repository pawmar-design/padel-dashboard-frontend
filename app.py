import streamlit as st
import requests
from datetime import datetime

# Konfiguracja strony
st.set_page_config(page_title="Padel Dashboard", page_icon="🎾")

st.title("🎾 Padel Dashboard")

# 1. Inputs (zamiast komponentów Retool)
data = st.date_input("Wybierz datę", value=datetime.now())
czas_trwania = st.number_input("Czas trwania (minuty)", value=60, step=30)

if st.button("Szukaj"):
    # 2. Pobieranie danych z Twojego API na Renderze
    try:
        api_url = f"https://padel-dashboard-api.onrender.com/korty?data={data}"
        response = requests.get(api_url, timeout=10)
        data_json = response.json()
        
        # Logika filtrowania (odpowiednik Twojego JS z Retoola)
        wszystkie_terminy = []
        for klub in data_json.get("wyniki", []):
            wszystkie_terminy.extend(klub.get("dostepne_terminy", []))
            
        # ... tutaj wstawiasz identyczną logikę sortowania/grupowania co w JS ...
        # Streamlit wyświetli wynik jako prostą tabelę lub listę
        
        st.write(f"Znaleziono {len(wszystkie_terminy)} terminów:")
        st.table(wszystkie_terminy) # Lub ładniejszy format
        
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")