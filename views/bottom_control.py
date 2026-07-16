# views/bottom_control.py
import customtkinter as ctk
import os
from viewmodels.workspace_vm import WorkspaceViewModel

class BottomControlFrame(ctk.CTkFrame):
    def __init__(self, master, viewmodel: WorkspaceViewModel, **kwargs):
        """
        Dolny panel sterowania sesją (Folder, Kalibracja rotacji, Lista parabol).
        """
        super().__init__(master, height=100, **kwargs)
        self.vm = viewmodel
        self.selected_parabola_idx = None  # Indeks aktualnie edytowanej paraboli

        # Konfiguracja siatki (3 główne kolumny o różnych wagach)
        self.grid_columnconfigure(0, weight=2)  # Folder (Średnia)
        self.grid_columnconfigure(1, weight=3)  # Inspektor rotacji (Szeroka)
        self.grid_columnconfigure(2, weight=3)  # Przewijana lista jonów (Szeroka)
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # KOLUMNA 1: PRZEGLĄDARKA FOLDERU (LEWA STRONA)
        # =========================================================================
        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        
        self.lbl_folder_title = ctk.CTkLabel(self.folder_frame, text="📁 Nawigacja serii danych", font=ctk.CTkFont(weight="bold"))
        self.lbl_folder_title.pack(anchor="w", pady=(0, 5))
        
        self.lbl_file_name = ctk.CTkLabel(self.folder_frame, text="Brak załadowanego pliku", text_color="gray", wraplength=250, justify="left")
        self.lbl_file_name.pack(anchor="w", pady=5)
        
        # Przyciski nawigacji spięte w jeden horyzontalny rząd
        self.nav_buttons_frame = ctk.CTkFrame(self.folder_frame, fg_color="transparent")
        self.nav_buttons_frame.pack(anchor="w", fill="x", pady=5)
        
        self.btn_prev = ctk.CTkButton(self.nav_buttons_frame, text="◀ Poprzedni", width=100, command=lambda: self._navigate_folder(step=-1))
        self.btn_prev.pack(side="left", padx=(0, 5))
        
        self.btn_next = ctk.CTkButton(self.nav_buttons_frame, text="Następny ▶", width=100, command=lambda: self._navigate_folder(step=1))
        self.btn_next.pack(side="left", padx=5)

        # Separator pionowy 1
        self.sep1 = ctk.CTkFrame(self, width=2, fg_color="#444444")
        self.sep1.grid(row=0, column=0, sticky="nse", pady=15)

        # =========================================================================
        # KOLUMNA 2: INSPEKTOR PARABOLI / ROTACJA (ŚRODEK)
        # =========================================================================
        self.tuning_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tuning_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)
        
        self.lbl_tuning_title = ctk.CTkLabel(self.tuning_frame, text="🎯 Kalibracja aktywnego śladu", font=ctk.CTkFont(weight="bold"))
        self.lbl_tuning_title.pack(anchor="w", pady=(0, 10))
        
        self.lbl_active_ion = ctk.CTkLabel(self.tuning_frame, text="Wybierz parabolę z listy po prawej...", text_color="gray")
        self.lbl_active_ion.pack(anchor="w", pady=5)
        
        # Kontrolki suwaka (Domyślnie zablokowane, dopóki użytkownik nie wybierze jona)
        self.slider_frame = ctk.CTkFrame(self.tuning_frame, fg_color="transparent")
        self.slider_frame.pack(fill="x", pady=5)
        
        self.rot_slider = ctk.CTkSlider(self.slider_frame, from_=-5.0, to=5.0, number_of_steps=1000, command=self._on_slider_move)
        self.rot_slider.set(0.0)
        self.rot_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.rot_slider.configure(state="disabled") # Blokada startowa
        
        self.entry_rot_val = ctk.CTkEntry(self.slider_frame, width=70, font=ctk.CTkFont(family="monospace", size=11), justify="center")
        self.entry_rot_val.insert(0, "0.00°")
        self.entry_rot_val.configure(state="disabled")
        self.entry_rot_val.pack(side="right")
        
        self.entry_rot_val.bind("<Return>", self._on_entry_submit)

        # Separator pionowy 2
        self.sep2 = ctk.CTkFrame(self, width=2, fg_color="#444444")
        self.sep2.grid(row=0, column=1, sticky="nse", pady=5)

        # =========================================================================
        # KOLUMNA 3: PRZEWIJANA LISTA PARABOL (PRAWA STRONA)
        # =========================================================================
        self.list_container = ctk.CTkFrame(self, fg_color="transparent")
        self.list_container.grid(row=0, column=2, sticky="nsew", padx=15, pady=10)
        
        self.lbl_list_title = ctk.CTkLabel(self.list_container, text="📊 Aktywne trajektorie jonów", font=ctk.CTkFont(weight="bold"))
        self.lbl_list_title.pack(anchor="w", pady=(0, 5))
        
        self.scroll_list = ctk.CTkScrollableFrame(self.list_container, height=70, label_text="")
        self.scroll_list.pack(fill="both", expand=True)

        # =========================================================================
        # GLOBALNY PASEK STATUSU (NA SAMYM DOLE RAMKI)
        # =========================================================================
        self.status_label = ctk.CTkLabel(self, text="Status: Gotowy.", text_color="#888888", anchor="w", font=ctk.CTkFont(size=11))
        self.status_label.place(relx=0.0, rely=1.0, anchor="sw", x=15, y=-5)

    # =========================================================================
    # DYNAMICZNA AKTUALIZACJA WIDOKU LISTY (WYWOŁYWANA PRZEZ MAIN_WINDOW)
    # =========================================================================
    
    def refresh_parabola_list(self, color_palette: list):
        """
        Czyści i buduje na nowo przewijaną listę jonów na bazie aktualnego stanu VM.
        Ta metoda jest wywoływana z głównej pętli rysowania w MainWindow.
        """
        # Czyszczenie starych widgetów z listy scrollowanej
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
            
        if self.vm.mcp_model is not None:
            self.lbl_file_name.configure(text=os.path.basename(self.vm.mcp_model.file_path))

        # Jeśli lista jest pusta, resetujemy kalibrator środkowy
        if not self.vm.parabolas_list:
            self._disable_inspector()
            return

        # Generowanie wierszy dla każdego jona
        for idx, p in enumerate(self.vm.parabolas_list):
            color = color_palette[idx % len(color_palette)]
            
            row = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Kolorowy znacznik paraboli
            color_dot = ctk.CTkLabel(row, text="■", text_color=color, font=ctk.CTkFont(size=14))
            color_dot.pack(side="left", padx=5)
            
            # Przycisk-etykieta: kliknięcie wybiera tę parabolę do edycji rotacji
            btn_select = ctk.CTkButton(
                row, 
                text=f"{p.name} (A={p.A}, Q={p.Q})", 
                anchor="w",
                fg_color="transparent", 
                text_color="white",
                hover_color="#3a3a3a",
                height=22,
                command=lambda i=idx: self._select_parabola_for_tuning(i)
            )
            btn_select.pack(side="left", fill="x", expand=True)
            
            # Wyświetlanie aktualnego kąta z cache modelu
            lbl_angle = ctk.CTkLabel(row, text=f"{p.rotation_parameter:.2f}°", font=ctk.CTkFont(family="monospace", size=11), text_color="gray")
            lbl_angle.pack(side="right", padx=10)

        # Zabezpieczenie indeksu po ewentualnym usunięciu elementów
        if self.selected_parabola_idx is not None and self.selected_parabola_idx >= len(self.vm.parabolas_list):
            self._disable_inspector()

    # =========================================================================
    # LOGIKA WEWNĘTRZNA KOMPONENTU
    # =========================================================================

    def _select_parabola_for_tuning(self, idx: int):
        """Włącza i ustawia suwak kalibracji dla wybranego jona."""
        self.selected_parabola_idx = idx
        p = self.vm.parabolas_list[idx]
        
        self.lbl_active_ion.configure(text=f"Modyfikujesz: {p.name}", text_color="#2b73b5")
        self.rot_slider.configure(state="normal")
        self.rot_slider.set(p.rotation_parameter)
        self.lbl_rot_val.configure(text=f"{p.rotation_parameter:.2f}°")

    def _on_slider_move(self, value: float):
        """Przekazuje ruch suwaka prosto do asynchronicznego silnika w ViewModelu."""
        if self.selected_parabola_idx is not None:
            self.lbl_rot_val.configure(text=f"{value:.2f}°")
            # Przekazujemy indeks i wartość - VM zajmie się resztą asynchronicznie w tle!
            self.vm.update_parabola_rotation(self.selected_parabola_idx, value)

    def _disable_inspector(self):
        """Resetuje i blokuje panel kalibracji."""
        self.selected_parabola_idx = None
        self.lbl_active_ion.configure(text="Wybierz parabolę z listy po prawej...", text_color="gray")
        self.rot_slider.set(0.0)
        self.rot_slider.configure(state="disabled")
        self.lbl_rot_val.configure(text="0.00°")

    def _navigate_folder(self, step: int):
        """Inteligentnie wyszukuje poprzedni/następny plik graficzny w tym samym katalogu."""
        if self.vm.mcp_model is None:
            return
            
        current_path = self.vm.mcp_model.file_path
        folder = os.path.dirname(current_path)
        current_file = os.path.basename(current_path)
        
        # Filtrujemy tylko pliki graficzne spektrometru
        valid_extensions = ('.tif', '.tiff', '.png')
        all_files = sorted([f for f in os.listdir(folder) if f.lower().endswith(valid_extensions)])
        
        if current_file in all_files:
            curr_idx = all_files.index(current_file)
            next_idx = (curr_idx + step) % len(all_files) # Zapętlenie folderu
            next_file_path = os.path.join(folder, all_files[next_idx])
            
            # Wywołanie globalnego ładowania w ViewModelu
            self.vm.load_image(next_file_path)

    def update_status_label(self, message: str):
        """CALLBACK: Metoda bindowania danych statusu bezpośrednio z ViewModelu."""
        self.status_label.configure(text=f"Status: {message}")


    def _select_parabola_for_tuning(self, idx: int):
        """Włącza kontrolki i ustawia aktualne wartości."""
        self.selected_parabola_idx = idx
        p = self.vm.parabolas_list[idx]
        
        self.lbl_active_ion.configure(text=f"Modyfikujesz: {p.name}", text_color="#2b73b5")
        
        self.rot_slider.configure(state="normal")
        self.rot_slider.set(p.rotation_deg)
        
        self.entry_rot_val.configure(state="normal")
        self.entry_rot_val.delete(0, "end")
        self.entry_rot_val.insert(0, f"{p.rotation_deg:.2f}")

    def _on_slider_move(self, value: float):
        """Ruch suwaka natychmiast uaktualnia pole tekstowe i buforuje obliczenia."""
        if self.selected_parabola_idx is not None:
            # Aktualizacja pola tekstowego (bez wywoływania eventu zatwierdzenia)
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{value:.2f}")
            
            # Przesyłamy żądanie do ViewModelu (on sam ograniczy ruch do 33ms!)
            self.vm.update_parabola_rotation(self.selected_parabola_idx, value)

    def _on_entry_submit(self, event):
        """Wciśnięcie klawisza Enter w polu tekstowym."""
        if self.selected_parabola_idx is None:
            return
            
        raw_text = self.entry_rot_val.get()
        try:
            # Próbujemy sparsować tekst na float
            val = float(raw_text.replace("°", "").strip())
            
            # Ograniczamy do zakresu suwaka
            val = min(max(val, -10.0), 10.0)
            
            # Synchronizujemy suwak
            self.rot_slider.set(val)
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{val:.2f}")
            
            # Przekazujemy zmianę i natychmiastowo wymuszamy odświeżenie wykresu
            self.vm.update_parabola_rotation(self.selected_parabola_idx, val)
            self.focus() # Zdejmujemy focus z pola tekstowego po zatwierdzeniu
            
        except ValueError:
            # W razie błędnego wpisu przywracamy poprzednią wartość
            p = self.vm.parabolas_list[self.selected_parabola_idx]
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{p.rotation_deg:.2f}")

    def _disable_inspector(self):
        """Resetuje i blokuje panel kalibracji."""
        self.selected_parabola_idx = None
        self.lbl_active_ion.configure(text="Wybierz parabolę z listy po prawej...", text_color="gray")
        self.rot_slider.set(0.0)
        self.rot_slider.configure(state="disabled")
        self.entry_rot_val.delete(0, "end")
        self.entry_rot_val.insert(0, "0.00")
        self.entry_rot_val.configure(state="disabled")