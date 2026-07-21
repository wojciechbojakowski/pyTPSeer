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
        # =========================================================================
        # KOLUMNA 2: INSPEKTOR PARABOLI / ROTACJA I TŁO (ŚRODEK)
        # =========================================================================
        self.tuning_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tuning_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)
        
        self.lbl_tuning_title = ctk.CTkLabel(self.tuning_frame, text="🎯 Kalibracja aktywnego śladu", font=ctk.CTkFont(weight="bold"))
        self.lbl_tuning_title.pack(anchor="w", pady=(0, 5))
        
        # --- 1. KONTROLKI ROTACJI ---
        self.lbl_active_ion = ctk.CTkLabel(self.tuning_frame, text="Wybierz parabolę z listy po prawej...", text_color="gray")
        self.lbl_active_ion.pack(anchor="w", pady=(0, 2))
        
        self.slider_frame = ctk.CTkFrame(self.tuning_frame, fg_color="transparent")
        self.slider_frame.pack(fill="x", pady=(0, 5))
        
        self.rot_slider = ctk.CTkSlider(
            self.slider_frame, 
            from_=-10.0, 
            to=10.0, 
            number_of_steps=2000, 
            command=self._on_slider_move
        )
        self.rot_slider.set(0.0)
        self.rot_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.rot_slider.configure(state="disabled")
        
        self.rot_slider.bind("<ButtonRelease-1>", self._on_slider_released)
        self.rot_slider.bind("<KeyRelease>", self._on_slider_released)
        
        self.entry_rot_val = ctk.CTkEntry(self.slider_frame, width=70, font=ctk.CTkFont(family="monospace", size=11), justify="center")
        self.entry_rot_val.insert(0, "0.00°")
        self.entry_rot_val.configure(state="disabled")
        self.entry_rot_val.pack(side="right")
        self.entry_rot_val.bind("<Return>", self._on_entry_submit)

        # Separator poziomka dla czystości interfejsu
        sep_bg = ctk.CTkFrame(self.tuning_frame, height=1, fg_color="#333333")
        sep_bg.pack(fill="x", pady=6)

        # --- 2. KONTROLKI USUWANIA TŁA (THRESHOLDING) ---
        self.lbl_bg = ctk.CTkLabel(self.tuning_frame, text="🧹 Odcięcie tła szumu (Threshold):", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_bg.pack(anchor="w", pady=(0, 2))

        self.bg_subframe = ctk.CTkFrame(self.tuning_frame, fg_color="transparent")
        self.bg_subframe.pack(fill="x")

        self.slider_bg = ctk.CTkSlider(
            self.bg_subframe, 
            from_=0.0, 
            to=1.0,  # Zakres dynamicznie aktualizowany w load_image
            number_of_steps=500, 
            command=self._on_bg_slider_move
        )
        self.slider_bg.set(0.0)
        self.slider_bg.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Obliczenia tła również wykonujemy dopiero po puszczeniu suwaka, by zapobiec lagom!
        self.slider_bg.bind("<ButtonRelease-1>", self._on_bg_slider_released)
        self.slider_bg.bind("<KeyRelease>", self._on_bg_slider_released)

        self.lbl_bg_val = ctk.CTkLabel(self.bg_subframe, text="0.0", width=50, font=ctk.CTkFont(family="monospace", size=11), anchor="e")
        self.lbl_bg_val.pack(side="right")

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
    
    # def refresh_parabola_list(self, color_palette: list):
    #     """
    #     Czyści i buduje na nowo przewijaną listę jonów na bazie aktualnego stanu VM.
    #     Ta metoda jest wywoływana z głównej pętli rysowania w MainWindow.
    #     """
    #     # Czyszczenie starych widgetów z listy scrollowanej
    #     for widget in self.scroll_list.winfo_children():
    #         widget.destroy()
            
    #     if self.vm.mcp_model is not None:
    #         self.lbl_file_name.configure(text=os.path.basename(self.vm.mcp_model.file_path))

    #     # Jeśli lista jest pusta, resetujemy kalibrator środkowy
    #     if not self.vm.parabolas_list:
    #         self._disable_inspector()
    #         return

    #     # Generowanie wierszy dla każdego jona
    #     for idx, p in enumerate(self.vm.parabolas_list):
    #         color = color_palette[idx % len(color_palette)]
            
    #         row = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
    #         row.pack(fill="x", pady=2)
            
    #         # Kolorowy znacznik paraboli
    #         color_dot = ctk.CTkLabel(row, text="■", text_color=color, font=ctk.CTkFont(size=14))
    #         color_dot.pack(side="left", padx=5)
            
    #         # Przycisk-etykieta: kliknięcie wybiera tę parabolę do edycji rotacji
    #         btn_select = ctk.CTkButton(
    #             row, 
    #             text=f"{p.name} (A={p.A}, Q={p.Q})", 
    #             anchor="w",
    #             fg_color="transparent", 
    #             text_color="white",
    #             hover_color="#3a3a3a",
    #             height=22,
    #             command=lambda i=idx: self._select_parabola_for_tuning(i)
    #         )
    #         btn_select.pack(side="left", fill="x", expand=True)
            
    #         # Wyświetlanie aktualnego kąta z cache modelu
    #         lbl_angle = ctk.CTkLabel(row, text=f"{p.rotation_parameter:.2f}°", font=ctk.CTkFont(family="monospace", size=11), text_color="gray")
    #         lbl_angle.pack(side="right", padx=10)

    #     # Zabezpieczenie indeksu po ewentualnym usunięciu elementów
    #     if self.selected_parabola_idx is not None and self.selected_parabola_idx >= len(self.vm.parabolas_list):
    #         self._disable_inspector()

    # =========================================================================
    # LOGIKA WEWNĘTRZNA KOMPONENTU
    # =========================================================================

    def _on_bg_slider_move(self, value: float):
        """Wykonywane na bieżąco podczas ruchu suwaka tła - tylko aktualizuje etykietę."""
        self.lbl_bg_val.configure(text=f"{value:.1f}")

    def _on_bg_slider_released(self, event):
        """Wykonywane DOPIERO po puszczeniu myszki - przelicza tło i odświeża wykresy."""
        val = self.slider_bg.get()
        self.vm.set_background_threshold(val)

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
        self.rot_slider.set(p.rotation_parameter)
        
        self.entry_rot_val.configure(state="normal")
        self.entry_rot_val.delete(0, "end")
        self.entry_rot_val.insert(0, f"{p.rotation_parameter:.2f}")

    def _disable_inspector(self):
        """Resetuje i blokuje panel kalibracji."""
        self.selected_parabola_idx = None
        self.lbl_active_ion.configure(text="Wybierz parabolę z listy po prawej...", text_color="gray")
        self.rot_slider.set(0.0)
        self.rot_slider.configure(state="disabled")
        self.entry_rot_val.delete(0, "end")
        self.entry_rot_val.insert(0, "0.00")
        self.entry_rot_val.configure(state="disabled")

    def _on_slider_move(self, value: float):
        """Wykonywane na bieżąco podczas ruchu suwaka. 
        Tylko aktualizuje tekst na ekranie, NIE liczy niczego w tle."""
        if self.selected_parabola_idx is not None:
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{value:.2f}")

    def _on_slider_released(self, event):
        """Wykonywane DOPIERO wtedy, gdy użytkownik puści suwak myszką."""
        if self.selected_parabola_idx is not None:
            current_val = self.rot_slider.get()
            # Dopiero teraz wysyłamy jedno zapytanie o przeliczenie nowej paraboli!
            self.vm.update_parabola_rotation(self.selected_parabola_idx, current_val)

    def _on_entry_submit(self, event):
        """Wpisanie wartości z klawiatury i kliknięcie Enter - liczy od razu."""
        if self.selected_parabola_idx is None:
            return
        try:
            val = float(self.entry_rot_val.get().replace("°", "").strip())
            val = min(max(val, -10.0), 10.0)
            
            self.rot_slider.set(val)
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{val:.2f}")
            
            # Wpisanie z palca traktujemy jako intencję natychmiastowego przeliczenia
            self.vm.update_parabola_rotation(self.selected_parabola_idx, val)
            self.focus()
        except ValueError:
            p = self.vm.parabolas_list[self.selected_parabola_idx]
            self.entry_rot_val.delete(0, "end")
            self.entry_rot_val.insert(0, f"{p.rotation_deg:.2f}")

        
    # views/bottom_control.py

    def refresh_parabola_list(self, color_palette: list):
        """
        Odświeża listę aktywnych trajektorii oraz przypiętych widm referencyjnych.
        """
        # Czyszczenie starej listy
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        # Aktualizacja nazwy załadowanego pliku
        if self.vm.mcp_model is not None:
            self.lbl_file_name.configure(text=os.path.basename(self.vm.mcp_model.file_path))

        has_pinned = bool(self.vm.pinned_spectra)
        has_active = bool(self.vm.parabolas_list)

        if not has_pinned and not has_active:
            lbl_empty = ctk.CTkLabel(self.scroll_list, text="Brak śladów. Dodaj nową parabolę!", text_color="gray")
            lbl_empty.pack(pady=10)
            self._disable_inspector()
            return

        # =========================================================================
        # SEKCJA 1: PRZYPIĘTE WIDMA REFERENCYJNE (📌)
        # =========================================================================
        if has_pinned:
            lbl_pinned_hdr = ctk.CTkLabel(
                self.scroll_list, 
                text="📌 PRZYPIĘTE REFERENCJE", 
                font=ctk.CTkFont(size=10, weight="bold"), 
                text_color="#2b73b5"
            )
            lbl_pinned_hdr.pack(anchor="w", padx=5, pady=(2, 2))

            for pin_key, data in list(self.vm.pinned_spectra.items()):
                # Format danych zależy od tego czy używasz tuple, czy obiektu PinnedSpectrum:
                if isinstance(data, tuple):
                    _, _, pinned_color = data
                else:
                    pinned_color = data.color

                row = ctk.CTkFrame(self.scroll_list, fg_color="#1e2630", corner_radius=6)
                row.pack(fill="x", pady=2, padx=2)

                # Wskaźnik koloru widma referencyjnego
                color_indicator = ctk.CTkFrame(row, width=10, height=10, fg_color=pinned_color)
                color_indicator.pack(side="left", padx=(8, 5))

                lbl_info = ctk.CTkLabel(
                    row, 
                    text=pin_key, 
                    anchor="w", 
                    font=ctk.CTkFont(size=11), 
                    text_color="#e0e0e0"
                )
                lbl_info.pack(side="left", fill="x", expand=True)

                # Przycisk usunięcia / odpięcia widma z pamięci (🗑️)
                btn_remove_pin = ctk.CTkButton(
                    row, 
                    text="🗑️", 
                    width=26, 
                    height=22,
                    fg_color="#8b0000",
                    hover_color="#b22222",
                    command=lambda k=pin_key: self._on_remove_pinned_click(k)
                )
                btn_remove_pin.pack(side="right", padx=4, pady=2)

            # Separator między sekcjami
            sep = ctk.CTkFrame(self.scroll_list, height=1, fg_color="#333333")
            sep.pack(fill="x", pady=5, padx=5)

        # =========================================================================
        # SEKCJA 2: AKTYWNE TRAJEKTORIE JONÓW (⚡)
        # =========================================================================
        if has_active:
            if has_pinned:
                lbl_active_hdr = ctk.CTkLabel(
                    self.scroll_list, 
                    text="⚡ AKTYWNE TRAJEKTORIE", 
                    font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color="gray"
                )
                lbl_active_hdr.pack(anchor="w", padx=5, pady=(2, 2))

            for idx, p in enumerate(self.vm.parabolas_list):
                color = color_palette[idx % len(color_palette)]
                
                row = ctk.CTkFrame(self.scroll_list, fg_color="transparent")
                row.pack(fill="x", pady=2, padx=2)

                # Kolorowy znacznik paraboli
                color_indicator = ctk.CTkFrame(row, width=10, height=10, fg_color=color)
                color_indicator.pack(side="left", padx=(5, 8))

                # Wybór paraboli do modyfikacji rotacji
                lbl_info = ctk.CTkLabel(
                    row, 
                    text=f"{p.name} (A={p.A:.1f}, Q={p.Q:.1f})", 
                    anchor="w",
                    font=ctk.CTkFont(size=11),
                    cursor="hand2"
                )
                lbl_info.pack(side="left", fill="x", expand=True)
                lbl_info.bind("<Button-1>", lambda event, i=idx: self._select_parabola_for_tuning(i))

                # Przycisk EDYCJI (✏️)
                btn_edit = ctk.CTkButton(
                    row, 
                    text="✏️", 
                    width=26, 
                    height=22,
                    fg_color="#3a3a3a",
                    hover_color="#555555",
                    command=lambda i=idx: self._on_edit_parabola_click(i)
                )
                btn_edit.pack(side="right", padx=2)

                # Przycisk PRZYPIĘCIA WIDMA (📌)
                pin_key = f"📌 {p.name} (Ref)"
                is_pinned = pin_key in self.vm.pinned_spectra
                pin_color = "#2b73b5" if is_pinned else "#3a3a3a"
                
                btn_pin = ctk.CTkButton(
                    row, 
                    text="📌", 
                    width=26, 
                    height=22,
                    fg_color=pin_color,
                    hover_color="#225c91",
                    command=lambda i=idx, col=color: self._on_pin_parabola_click(i, col)
                )
                btn_pin.pack(side="right", padx=2)

        # Zabezpieczenie indeksu w kal
    # --- CALLBACKI DLA PRZYCISKÓW ---

    def _on_pin_parabola_click(self, idx: int, color: str):
        """Wywoływane po kliknięciu pinezki."""
        self.vm.toggle_pin_parabola(idx, color)

    def _on_edit_parabola_click(self, idx: int):
        """Wywoływane po kliknięciu ołówka. Otwiera okno edycji z załadowanymi danymi."""
        # Tutaj wywołujemy popup edycji. 
        # Przekazujemy indeks modyfikowanej paraboli, aby popup zapisał zmiany w tym samym obiekcie
        from views.windows_popup import ParabolaConfigPopup
        popup = ParabolaConfigPopup(master=self.winfo_toplevel(), viewmodel=self.vm, edit_index=idx)
        popup.grab_set()

    def _on_remove_pinned_click(self, pin_key: str):
        """Usuwa przypięte widmo referencyjne z bufora w ViewModelu."""
        self.vm.remove_pinned_spectrum(pin_key)