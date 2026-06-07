import streamlit as st
import requests
from datetime import datetime, time

# Konfiguracja strony
st.set_page_config(page_title="Padel Dashboard", page_icon="🎾")

if "searched" not in st.session_state:
    st.session_state.searched = False

st.title("Padel Dashboard")

dni_tygodnia = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
data_input = st.date_input("Wybierz datę", value=datetime.now(), format="DD/MM/YYYY")

st.caption(f"**{dni_tygodnia[data_input.weekday()]}**")

# --- SEKCJA: PRZEDZIAŁ CZASOWY ---
st.markdown("**Przedział czasowy:**")
col1, col2 = st.columns(2)

with col1:
    poczatkowa_godzina = st.time_input("Od:", value=time(7, 0), step=1800)

with col2:
    # ZMIANA 1: Domyślnie ustawione na 00:00 (północ)
    koncowa_godzina = st.time_input("Do:", value=time(0, 0), step=1800)

# Nazwa pola z minutami
czas_trwania = st.number_input("Czas trwania rezerwacji (minuty)", min_value=30, max_value=300, value=90, step=30)

godziny = czas_trwania // 60
minuty_reszta = czas_trwania % 60
if godziny > 0 and minuty_reszta > 0:
    format_wyswietlany = f"{godziny}h {minuty_reszta}min"
elif godziny > 0:
    format_wyswietlany = f"{godziny}h"
else:
    format_wyswietlany = f"{minuty_reszta}min"
    
st.caption(f"Wybrany czas: **{format_wyswietlany}**")

lista_klubow = ["Pura", "Fast", "Padel Park", "Tenispoint"]
wybrane_kluby = st.multiselect(
    "Wybór klubów", 
    options=lista_klubow, 
    default=lista_klubow,
    placeholder="Wybierz klub"
)

warning_placeholder = st.empty()
if not st.session_state.searched:
    warning_placeholder.markdown("<p style='color:red; font-size:0.9em; font-style:italic;'>Pierwsze wyszukiwanie może trwać maksymalnie 60 sekund z uwagi na wybudzenie serwera</p>", unsafe_allow_html=True)

if st.button("Szukaj"):
    st.session_state.searched = True
    warning_placeholder.empty()
    
    if not wybrane_kluby:
        st.error("Nie wybrano żadnego klubu")
    else:
        if poczatkowa_godzina >= koncowa_godzina and koncowa_godzina != time(0,0):
            st.warning("Godzina końcowa musi być późniejsza niż godzina początkowa!")
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
                    max_godzina_end = (koncowa_godzina.hour * 60 + koncowa_godzina.minute)
                    
                    if max_godzina_end == 0:
                        max_godzina_end = 1440
                        
                    # ZMIANA 2: Słownik przechowuje teraz strukturę: nazwa_kortu -> { minuta_startu: link }
                    korty = {}
                    for t in terminy:
                        nazwa_kortu = t.get("kort")
                        godzina = t.get("godzina")
                        link = t.get("link", "")
                        if nazwa_kortu and godzina:
                            if nazwa_kortu not in korty:
                                korty[nazwa_kortu] = {}
                            korty[nazwa_kortu][w_minuty(godzina)] = link
                            
                    wynik = []
                    for nazwa_kortu, czasy_dict in korty.items():
                        czasy = sorted(czasy_dict.keys())
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
                                    
                                    if start >= min_godzina_start and end <= max_godzina_end:
                                        # Pobranie linku powiązanego z pierwszą godziną bloku rezerwacji
                                        link_rezerwacji = czasy_dict[start]
                                        wynik.append({
                                            "Kort": nazwa_kortu,
                                            "Godzina": f"{formatuj_czas(start)} - {formatuj_czas(end)}",
                                            "Link": link_rezerwacji,
                                            "sortowanie": start
                                        })
                                        
                    wynik = sorted(wynik, key=lambda x: x["sortowanie"])
                    
                    st.write(f"Znalezione wolne terminy - {len(wynik)}:")
                    
                    if wynik:
                        for w in wynik:
                            del w["sortowanie"]
                        
                        # ZMIANA 3: Renderowanie tabeli z interaktywną kolumną z linkami
                        st.dataframe(
                            wynik, 
                            use_container_width=True,
                            column_config={
                                "Link": st.column_config.LinkColumn(
                                    "Rezerwacja",
                                    help="Kliknij, aby przejść bezpośrednio do rezerwacji tego kortu",
                                    display_text="Zarezerwuj ↗"
                                )
                            }
                        )
                    else:
                        st.info("Brak kortów w wyznaczonym przedziale czasowym")
                        
                else:
                    st.error(f"Błąd API: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("Przekroczono czas oczekiwania. Kliknij 'Szukaj' jeszcze raz za 30 sekund.")
            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {e}")
