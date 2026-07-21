# pyTPSeer

**Oprogramowanie do analizy i obróbki widm z Thomson Parabola Spectrometer (TPS)**
`pyTPSeer` to desktopowa aplikacja naukowa napisana w języku Python, przeznaczona do kalibracji, symulacji trajektorii jonów oraz ekstrakcji różniczkowych widm energetycznych ($dN/dE$) i widm czasu przelotu (**TOF**) z kadrów detektorów MCP.

---

## 🌟 Kluczowe Funkcjonalności

* **Akomodacja i Kalibracja Kątowa:** Płynna kalibracja rotacji śladu jonowego w czasie rzeczywistym z poziomu suwaka lub precyzyjnego pola tekstowego.
* **Szybkie Silniki Numeryczne (JIT / Numba):** Całkowanie równań ruchu jonów w polach $E$ i $B$ przyspieszane kompilacją JIT (30+ FPS).
* **Automatyczne Wycinanie Widm (1D):** Równoległa generacja widm energetycznych $dN/dE$ oraz widm czasu przelotu TOF bezpośrednio z macierzy jasności obrazu.
* **Redukcja Szumów i Odcięcie Tła (Thresholding):** Interaktywne odcinanie szumu cieplnego kamery/detektora na żywo.
* **Architektura MVVM:** Czysty podział na warstwy logiki naukowej, modeli oraz warstwy CustomTkinter + Matplotlib.

---

## 🛠️ Wymagania i Instalacja

### Wymagania systemowe

* Python 3.10+
* Systemy: Linux (zalecany Debian/Ubuntu), Windows 10/11, macOS

### Instalacja krok po kroku

1. **Sklonuj repozytorium:**

   ```bash
       git clone https://github.com/wojciechbojakowski/pyTPSeer.git
       cd pyTPSeer
   ```
2. **Stwórz i aktywuj środowisko wirtualne:**

   ```bash
       python3 -m venv env
       source env/bin/activate        # Linux / macOS
       # lub dla Windows: env\Scripts\activate
   ```
3. **Zainstaluj wymagane pakiety:**

   ```bash
       pip install -r requirements.txt
   ```
4. **Uruchom aplikację:**

   ```bash
       python3 main.py
   ```

---

## 📂 Struktura Projektu

```text
    pyTPSeer/
    ├── config.py                 # Stałe fizyczne (M_ION, Q_ION) i domyślne parametry pola
    ├── main.py                   # Punkt wejścia aplikacji
    ├── core/                     # Silnik numeryczny JIT (Numba) i integrator równań ruchu
    │   └── numerical_engine.py
    ├── models/                   # Modele danych (MCPModel, ParabolaConfig, TPSParams)
    │   ├── mcp_model.py
    │   └── parabola_config.py
    ├── viewmodels/               # Warstwa logiki biznesowej i wielowątkowości (MVVM)
    │   └── workspace_vm.py
    └── views/                    # Warstwa interfejsu graficznego (CustomTkinter + Matplotlib)
        ├── main_window.py
        ├── plot_canvas.py
        ├── top_bar.py
        ├── bottom_control.py
        └── windows_popup.py
```

---

## 🔬 Podstawowy Workflow Pracy

1. **Wczytaj Obraz:** Kliknij `Wczytaj obraz MCP` i wybierz plik `.tif` / `.png` / `.root`.
2. **Podaj Parametry TPS:** Kliknij w `Parametry TPS` i ustaw parametry.
3. **Ustaw Punkt Zero:** Kliknij `Zaznacz punkt zero`, a następnie wskaż na obrazie pozycję otworka (pinhole / $x_0, y_0$).
4. **Dodaj Ślad Jonowy:** Wybierz `Dodaj nową parabolę`, podaj masę $A$, ładunek $Q$ oraz zakres energii.
5. **Skalibruj Rotację:** Wybierz parabolę z dolnej listy i dopasuj jej kąt suwakiem lub wpisując wartość z palca.
6. **Odetnij Tło:** Dostosuj suwak `🧹 Odcięcie tła`, aby usunąć szum matrycy.
7. **Porównaj Wyniki:** Przypnij wybrane widmo ikoną 📌, wczytaj kolejny plik i porównaj uzyskane piki!

---

## 📜 Licencja

Projekt udostępniany na licencji MIT / Akademickiej.
