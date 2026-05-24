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

# POPRAWKA: Zmiana nazwy na "Rezerwacje od godziny"
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

# Rezerwacja miejsca na czerwony komunikat
warning_placeholder = st.empty()
if not st.session_state.searched:
    warning_placeholder.markdown("<p style='color:red; font-size:0.9em; font-style:italic;'>Pierwsze wyszukiwanie może trwać maksymalnie 60 sekund z uwagi na wybudzenie serwera</p>", unsafe_allow_html=True)

if st.button("Szukaj"):
    st.session_state.searched = True
    warning_placeholder.empty()
    
    try:
        format_daty = data_input.strftime('%Y-%m-%d')
        api_url = f"https://padel-dashboard-api.onrender.com/korty?data={format_daty}"
        
        with st.spinner("Szukam kortów..."):
            response = requests.get(api_url, timeout=60)
            
        if response.status_code == 200:
            data_json = response.json()
            
            terminy = []
            for klub in data_json.get("wyniki", []):
                terminy.extend(klub.get("dostepne_terminy", []))
                
            wymagane_minuty = int(czas_trwania)
            wymagane_sloty = int(wymagane_minuty / 30)
            PRZESUNIECIE = 120 # Przesunięcie dla danych z API
            
            def w_minuty(czas_str):
                h, m = map(int, czas_str.split(':'))
                return (h * 60 + m) + PRZESUNIECIE
                
            def formatuj_czas(minuty):
                h = int((minuty % 1440) // 60)
                m = int(minuty % 60)
                return f"{h:02d}:{m:02d}"
                
            # Czas z komponentu pobieramy wprost, bez dodawania PRZESUNIECIA
            min_godzina_start = (poczatkowa_godzina.hour * 60 + poczatkowa_godzina.minute)
                
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
                            # Sprawdzenie poprawnie przeliczonej godziny początkowej
                            if start >= min_godzina_start:
                                end = start + wymagane_minuty
                                wynik.append({
                                    "Kort": nazwa_kortu,
                                    "Godzina": f"{formatuj_czas(start)} - {formatuj_czas(end)}",
                                    "sortowanie": start
                                })
                                
            wynik = sorted(wynik, key=lambda x: x["sortowanie"])
            
            # Nowy format komunikatu podsumowującego
            st.write(f"Znalezione wolne terminy - {len(wynik)}:")
            
            if wynik:
                for w in wynik:
                    del w["sortowanie"]
                st.dataframe(wynik, use_container_width=True)
            else:
                st.info("Brak kortów w wyznaczonym czasie")
                
        else:
            st.error(f"Błąd API: {response.status_code}")
            
    except requests.exceptions.Timeout:
        st.error("Przekroczono czas oczekiwania. Kliknij 'Szukaj' jeszcze raz za 30 sekund.")
    except Exception as e:
        st.error(f"Wystąpił nieoczekiwany błąd: {e}")
