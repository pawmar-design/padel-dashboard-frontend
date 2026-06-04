import streamlit as st
import requests
from datetime import datetime, time

# Konfiguracja strony
st.set_page_config(page_title="Padel Dashboard", page_icon="🎾")

# Inicjalizacja pamięci aplikacji dla czerwonego komunikatu
if "searched" not in st.session_state:
    st.session_state.searched = False

st.title("Padel Dashboard")

# Słownik polskich dni tygodnia
dni_tygodnia = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

data_input = st.date_input("Wybierz datę", value=datetime.now(), format="DD/MM/YYYY")

# Wyświetlanie samego dnia tygodnia (pogrubionego) pod datą
st.caption(f"**{dni_tygodnia[data_input.weekday()]}**")

# Interwały co 30 minut (1800 sekund) na liście rozwijanej
poczatkowa_godzina = st.time_input("Rezerwacje od godziny", value=time(7, 0), step=1800)

# Nazwa pola z minutami
czas_trwania = st.number_input("Czas trwania rezerwacji (minuty)", min_value=30, max_value=300, value=90, step=30)

# Tłumaczenie minut na format godzinowy
godziny = czas_trwania // 60
minuty_reszta = czas_trwania % 60
if godziny > 0 and minuty_reszta > 0:
    format_wyswietlany = f"{godziny}h {minuty_reszta}min"
elif godziny > 0:
    format_wyswietlany = f"{godziny}h"
else:
    format_wyswietlany = f"{minuty_reszta}min"
    
st.caption(f"Wybrany czas: **{format_wyswietlany}**")

# Filtr klubów
lista_klubow = ["Pura", "Fast", "Padel Park", "Tenispoint"]
wybrane_kluby = st.multiselect(
    "Wybór klubów", 
    options=lista_klubow, 
    default=lista_klubow,
    placeholder="Wybierz klub"
)

# Rezerwacja miejsca na czerwony komunikat
warning_placeholder = st.empty()
if not st.session_state.searched:
    warning_placeholder.markdown("<p style='color:red; font-size:0.9em; font-style:italic;'>Pierwsze wyszukiwanie może trwać maksymalnie 60 sekund z uwagi na wybudzenie serwera</p>", unsafe_allow_html=True)

if st.button("Szukaj"):
    st.session_state.searched = True
    warning_placeholder.empty()
    
    if not wybrane_kluby:
        st.error("Nie wybrano żadnego klubu")
    else:
        try:
            format_daty = data_input.strftime('%Y-%m-%d')
            api_url = f"https://padel-dashboard-api.onrender.com/korty?data={format_daty}"
            
            with st.spinner("Szukam kortów..."):
                response = requests.get(api_url, timeout=60)
                
            if response.status_code == 200:
                data_json = response.json()
                
                terminy = []
                for klub in data_json.get("wyniki", []):
                    nazwa_klubu = klub.get("klub")
                    status = klub.get("status", "sukces")
                    
                    if status == "403":
                        st.warning(f"⚠️ Odmowa serwera dla klubu {nazwa_klubu}")
                        continue
                    elif status != "sukces":
                        st.warning(f"⚠️ Problem z klubem {nazwa_klubu}: {status}")
                        continue
                    
                    if nazwa_klubu in wybrane_kluby:
                        terminy.extend(klub.get("dostepne_terminy", []))
                    
                wymagane_minuty = int(czas_trwania)
                wymagane_sloty = int(wymagane_minuty / 30)
                PRZESUNIECIE = 0
                
                def w_minuty(czas_str):
                    h, m = map(int, czas_str.split(':'))
                    return (h * 60 + m) + PRZESUNIECIE
                    
                def formatuj_czas(minuty):
                    h = int((minuty % 1440) // 60)
                    m = int(minuty % 60)
                    return f"{h:02d}:{m:02d}"
                    
                min_godzina_start = (poczatkowa_godzina.hour * 60 + poczatkowa_godzina.minute)
                    
                korty = {}
                for t in terminy:
                    nazwa_kortu = t.get("kort")
                    godzina = t.get("godzina")
                    link = t.get("link", "")
                    if nazwa_
