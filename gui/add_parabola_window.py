# gui/add_parabola_window.py
import customtkinter as ctk

class AddParabolaWindow(ctk.CTkToplevel):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        
        self.controller = controller
        self.title("Dodaj nową parabolę jonową")
        self.geometry("400x420")
        
        # Modalność
        self.lift()
        self.focus_set()
        self.grab_set()
        
        # Definicje presetów (Nazwa: (A, Q, E_min, E_max))
        self.presets = {
            "Wodór / Proton (H+)": ("Proton (H+)", "1.0", "1.0", "0.2", "3.0"),
            "Węgiel C6+": ("Wegiel (C6+)", "12.0", "6.0", "1.0", "20.0"),
            "Węgiel C4+": ("Wegiel (C4+)", "12.0", "4.0", "1.0", "15.0"),
            "Własna cząstka...": ("", "1.0", "1.0", "0.5", "2.0")
        }

        # --- PRESET DROPDOWN ---
        lbl_preset = ctk.CTkLabel(self, text="Wybierz szybki szablon jonu:", font=ctk.CTkFont(weight="bold"))
        lbl_preset.pack(pady=(15, 2), padx=20, anchor="w")
        
        self.combo_presets = ctk.CTkComboBox(
            self, 
            values=list(self.presets.keys()),
            command=self._on_preset_selected
        )
        self.combo_presets.pack(fill="x", padx=20, pady=(0, 15))

        # --- FORMULARZ INPUTÓW ---
        self.entries = {}
        
        # Pola: klucz -> (Etykieta, Wartość startowa)
        field_specs = {
            "name": "Nazwa na wykresie:",
            "A": "Masa cząstki A [u]:",
            "Q": "Ładunek cząstki Q [e]:",
            "E_min": "Energia minimalna E_min [MeV]:",
            "E_max": "Energia maksymalna E_max [MeV]:"
        }
        
        for key, label_text in field_specs.items():
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(fill="x", padx=20, pady=4)
            
            lbl = ctk.CTkLabel(frame, text=label_text)
            lbl.pack(side="left", anchor="w")
            
            entry = ctk.CTkEntry(frame, width=150)
            entry.pack(side="right", anchor="e")
            self.entries[key] = entry

        # Wczytaj domyślnie pierwszy szablon (Proton)
        self.combo_presets.set("Wodór / Proton (H+)")
        self._on_preset_selected("Wodór / Proton (H+)")

        # --- PRZYCISKI NA DOLE ---
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=25)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Anuluj", fg_color="gray", width=100, command=self.destroy)
        self.btn_cancel.pack(side="left")
        
        self.btn_add = ctk.CTkButton(self.btn_frame, text="Dodaj do widoku", fg_color="#2b9348", hover_color="#1b5e20", command=self._validate_and_submit)
        self.btn_add.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _on_preset_selected(self, choice):
        """Automatycznie uzupełnia pola tekstowe po wybraniu szablonu"""
        name, a, q, emin, emax = self.presets[choice]
        
        for key, val in zip(["name", "A", "Q", "E_min", "E_max"], [name, a, q, emin, emax]):
            self.entries[key].delete(0, "end")
            self.entries[key].insert(0, val)

    def _validate_and_submit(self):
        """Sprawdza poprawność typów i wysyła obiekt konfiguracji do MainWindow"""
        try:
            name = self.entries["name"].get().strip()
            if not name: name = "Jon"
                
            config_data = {
                "name": name,
                "A": float(self.entries["A"].get()),
                "Q": float(self.entries["Q"].get()),
                "E_min": float(self.entries["E_min"].get()),
                "E_max": float(self.entries["E_max"].get())
            }
            
            # Przekazujemy konfigurację do okna głównego
            self.controller.add_new_parabola(config_data)
            self.destroy()
            
        except ValueError:
            # Podświetlenie błędnych pól na czerwono
            for entry in self.entries.values():
                try:
                    if entry.get() == self.entries["name"].get(): continue
                    float(entry.get())
                    entry.configure(border_color=["#979da2", "#565b5e"])
                except ValueError:
                    entry.configure(border_color="red")