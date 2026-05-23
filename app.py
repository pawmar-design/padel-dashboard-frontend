import streamlit as st
import requests
from datetime import datetime

# Konfiguracja strony
st.set_page_config(page_title="Padel Dashboard", page_icon="🎾")

# 1. Tytuł bez paletki
st.title("Padel Dashboard")

# Inputs
data_input = st.date_input("Wybierz datę", value=datetime.now())

# 2 & 3. Zmiana nazwy, min_value=30 (zapobiega błędowi 0 minut), max_value=300 (5h)
czas_trwania = st.number_input("Czas trwania rezerwacji", min_value=30, max_value=300, value=90, step=30)

# Dodatkowy bajer: tłumaczenie minut na czytelny format godzinowy pod polem
godziny = czas_trwania // 60
minuty_reszta = czas_trwania % 60
if godziny > 0 and minuty_reszta > 0:
    format_wyswietlany = f"{godziny}h {minuty_reszta}min"
elif godziny > 0:
    format_wyswietlany = f"{godziny}h"
else:
    format_wyswietlany = f"{minuty_reszta}min"
    
st.caption(f"Wybrany czas: **{format_wyswietlany}**")

if st.button("Szukaj"):
    try:
        # Wymuszenie formatu YYYY-MM-DD dla API
        format_daty = data_input.strftime('%Y-%m-%d')
        api_url = f"https://padel-dashboard-api.onrender.com/korty?data={format_daty}"
        
        # 4. Połączony komunikat (Streamlit nie pozwala na zmianę w trakcie blokującego zapytania)
        with st.spinner("Szukam kortów... (Jeśli to trwa dłużej, serwer się budzi ZzZz...)"):
            response = requests.get(api_url, timeout=60)
            
        if response.status_code == 200:
            data_json = response.json()
            
            # 1. Zbieranie wszystkich terminów z API
            terminy = []
            for klub in data_json.get("wyniki", []):
                terminy.extend(klub.get("dostepne_terminy", []))
                
            # 2. Przeliczanie parametrów
            wymagane_minuty = int(czas_trwania)
            wymagane_sloty = int(wymagane_minuty / 30)
            PRZESUNIECIE = 120 # Przesunięcie strefy czasowej (2 godziny)
            
            def w_minuty(czas_str):
                h, m = map(int, czas_str.split(':'))
                return (h * 60 + m) + PRZESUNIECIE
                
            def formatuj_czas(minuty):
                h = int((minuty % 1440) // 60)
                m = int(minuty % 60)
                return f"{h:02d}:{m:02d}"
                
            # 3. Grupowanie terminów po konkretnych kortach
            korty = {}
            for t in terminy:
                nazwa_kortu = t.get("kort")
                godzina = t.get("godzina")
                if nazwa_kortu and godzina:
                    if nazwa_kortu not in korty:
                        korty[nazwa_kortu] = []
                    korty[nazwa_kortu].append(w_minuty(godzina))
                    
            # 4. Algorytm szukania ciągłych bloków czasowych
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
                            wynik.append({
                                "Kort": nazwa_kortu,
                                "Godzina": f"{formatuj_czas(start)} - {formatuj_czas(end)}",
                                "sortowanie": start
                            })
                            
            # 5. Wyświetlanie wyników
            wynik = sorted(wynik, key=lambda x: x["sortowanie"])
            
            st.write(f"Znaleziono {len(wynik)} terminów:")
            
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
