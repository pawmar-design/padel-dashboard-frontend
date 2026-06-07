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

# --- NOWA SEKCJA: Przedział czasowy ---
st.write("**Przedział czasowy:**")
col1, col2 = st.columns(2)

with col1:
    poczatkowa_godzina = st.time_input("Od:", value=time(7, 0), step=1800)
    
with col2:
    koncowa_godzina = st.time_input("Do:", value=time(23, 0), step=1800)
# --------------------------------------

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
                    
                # Przeliczenie wybranych godzin na minuty od początku dnia
                min_godzina_start = (poczatkowa_godzina.hour * 60 + poczatkowa_godzina.minute)
                max_godzina_end = (koncowa_godzina.hour * 60 + koncowa_godzina.minute)
                
                # Zabezpieczenie dla ustawienia "Do: 00:00" (traktujemy jako koniec dnia)
                if max_godzina_end == 0:
                    max_godzina_end = 1440
                    
                korty = {}
                for t in terminy:
                    nazwa_kortu = t.get("kort")
                    godzina = t.get("godzina")
                    if nazwa_kortu and godzina:
                        if nazwa_kortu not in korty:
                            korty[nazwa_kortu] = []
                        korty[nazwa_kortu].append(w_minuty(godzina))
                        
                wynik = []
                for nazwa_kortu, czasy in korty.items():
                    czasy = sorted(czasy)
                    if len(czasy) >= wymagane_sloty:
                        for i in range(len(czasy) - wymagane_sloty + 1):
                            ciagle = True
                            for j in range(1, wymagane_sloty):
                                if czasy[i + j] != czasy[i] + (j * 30):
                                    ciagle = False
                                    break
                            if ciagle:
                                start = czasy[i]
                                end = start + wymagane_minuty
                                
                                # Sprawdzenie czy cały blok mieści się w przedziale czasowym użytkownika
                                if start >= min_godzina_start and end <= max_godzina_end:
                                    wynik.append({
