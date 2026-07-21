# views/windows_popup.py
import customtkinter as ctk
from viewmodels.workspace_vm import WorkspaceViewModel
from models.parabola_config import ParabolaConfig
from models.sampling_mode import SamplingMode

# =========================================================================
# 1. POPUP: PARAMETRY SPRZĘTOWE KOMORY TPS
# =========================================================================
class HardwareParamsPopup(ctk.CTkToplevel):
    def __init__(self, master, viewmodel: WorkspaceViewModel, **kwargs):
        """Okienko modalne do edycji parametrów fizycznych i geometrii spektrometru."""
        super().__init__(master, **kwargs)
        self.vm = viewmodel
        
        self.title("Ustawienia spektrometru Thompson Parabola")
        self.geometry("580x420")
        self.resizable(False, False)
        self.transient(master) # Okno zawsze na wierzchu głównego okna
        
        # Główny layout siatki okna
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- KOLUMNA 1: Pola i Sektory Magnetyczne/Elektryczne ---
        self.col1_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col1_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        
        self._add_label(self.col1_frame, "⚡ Pola i współrzędne Z [m]").pack(anchor="w", pady=(0, 10))
        
        self.entry_B = self._create_field(self.col1_frame, "Pole magnetyczne B [T]:", self.vm.tps_params.B_field)
        self.entry_E = self._create_field(self.col1_frame, "Pole elektryczne E [V/m]:", self.vm.tps_params.E_field)
        self.entry_Zm1 = self._create_field(self.col1_frame, "Początek B (Zm1):", self.vm.tps_params.Zm1)
        self.entry_Zm2 = self._create_field(self.col1_frame, "Koniec B (Zm2):", self.vm.tps_params.Zm2)
        self.entry_Ze1 = self._create_field(self.col1_frame, "Początek E (Ze1):", self.vm.tps_params.Ze1)
        self.entry_Ze2 = self._create_field(self.col1_frame, "Koniec E (Ze2):", self.vm.tps_params.Ze2)

        # --- KOLUMNA 2: Geometria Przesłony i Okładzin ---
        self.col2_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col2_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=15)
        
        self._add_label(self.col2_frame, "📐 Geometria i szczeliny").pack(anchor="w", pady=(0, 10))
        
        self.entry_Zd = self._create_field(self.col2_frame, "Dystans detektora (Zd) [m]:", self.vm.tps_params.Zd)
        self.entry_d1 = self._create_field(self.col2_frame, "Szczelina wejściowa d1 [m]:", self.vm.tps_params.d1)
        self.entry_d2 = self._create_field(self.col2_frame, "Szczelina wyjściowa d2 [m]:", self.vm.tps_params.d2)
        self.entry_pin_d = self._create_field(self.col2_frame, "Średnica pinhole [mm]:", self.vm.tps_params.pin_d)
        self.entry_pin_target = self._create_field(self.col2_frame, "Dystans Target-Pinhole [m]:", self.vm.tps_params.pin_target)

        # --- DOLNY PANEL Z PRZYCISKAMI ---
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        self.btn_save = ctk.CTkButton(self.btn_frame, text="💾 Zastosuj zmiany", command=self._on_save_click, fg_color="#2b73b5", hover_color="#225c91")
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Anuluj", command=self.destroy, fg_color="#444444", hover_color="#555555")
        self.btn_cancel.pack(side="right", padx=5)

    def _create_field(self, parent, label_text, current_value):
        """Pomocniczy generator wiersza formularza (Label + Entry)."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), anchor="w", width=140)
        lbl.pack(side="left")
        entry = ctk.CTkEntry(row, height=24, font=ctk.CTkFont(size=12))
        entry.insert(0, str(current_value))
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _add_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888")

    def _on_save_click(self):
        """Pakuje dane z pól tekstowych i wysyła je prosto do walidatora w ViewModelu."""
        gui_data = {
            "B_field": self.entry_B.get(),
            "E_field": self.entry_E.get(),
            "Zm1": self.entry_Zm1.get(),
            "Zm2": self.entry_Zm2.get(),
            "Ze1": self.entry_Ze1.get(),
            "Ze2": self.entry_Ze2.get(),
            "Zd": self.entry_Zd.get(),
            "d1": self.entry_d1.get(),
            "d2": self.entry_d2.get(),
            "pin_d": self.entry_pin_d.get(),
            "pin_target": self.entry_pin_target.get()
        }
        # ViewModel zajmie się walidacją. Jeśli wpisano błąd, informacja pojawi się na pasku statusu
        self.vm.update_hardware_parameters(gui_data)
        self.destroy()


# =========================================================================
# 2. POPUP: FORMULARZ DODAWANIA NOWEJ TRAJEKTORII JONU
# =========================================================================
class AddParabolaPopup(ctk.CTkToplevel):
    def __init__(self, master, viewmodel: WorkspaceViewModel, **kwargs):
        """Okienko formularza specyfikacji nowego jona i zakresu energetycznego."""
        super().__init__(master, **kwargs)
        self.vm = viewmodel
        
        self.title("Konfiguracja nowej paraboli jonowej")
        self.geometry("380x360")
        self.resizable(False, False)
        self.transient(master)
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # --- POLA FORMULARZA ---
        self.entry_name = self._add_form_row("Nazwa identyfikacyjna:", "np. Proton (H+)")
        self.entry_A = self._add_form_row("Masa cząstki A [u]:", "1.0")
        self.entry_Q = self._add_form_row("Stan ładunkowy Q [e]:", "1.0")
        self.entry_Emin = self._add_form_row("Energia E_min [MeV]:", "0.1")
        self.entry_Emax = self._add_form_row("Energia E_max [MeV]:", "10.0")
        
        # Słupek wyboru metody próbkowania energii (Enum SamplingMode)
        row_enum = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row_enum.pack(fill="x", pady=6)
        ctk.CTkLabel(row_enum, text="Próbkowanie energii:", anchor="w", width=140).pack(side="left")
        
        # Pobieramy opcje tekstowe wprost z modelu Enuma
        enum_labels = [mode.label for mode in SamplingMode]
        self.combo_sampling = ctk.CTkComboBox(row_enum, values=enum_labels, height=26)
        self.combo_sampling.set(SamplingMode.QUADRATIC.label) # Domyślny wybór
        self.combo_sampling.pack(side="right", fill="x", expand=True)
        
        # --- PRZYCISKI AKCJI ---
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=(25, 0))
        
        self.btn_submit = ctk.CTkButton(self.btn_frame, text="➕ Dodaj ślad", command=self._on_submit_click, fg_color="#2b73b5", hover_color="#225c91")
        self.btn_submit.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Anuluj", command=self.destroy, fg_color="#444444", hover_color="#555555")
        self.btn_cancel.pack(side="right", padx=5)

    def _add_form_row(self, label_text, placeholder):
        row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=label_text, anchor="w", width=140).pack(side="left")
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=26)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _on_submit_click(self):
        """Zczytuje parametry, rzutuje typy, tworzy model ParabolaConfig i wstrzykuje do VM."""
        try:
            # Odzyskujemy pełnoprawny obiekt Enuma na bazie etykiety tekstowej z ComboBoxa
            chosen_label = self.combo_sampling.get()
            enum_mode = SamplingMode.from_label(chosen_label)
            
            # Tworzymy czysty obiekt modelu danych
            new_parabola = ParabolaConfig(
                name=self.entry_name.get() if self.entry_name.get() else "Jon nienazwany",
                A=float(self.entry_A.get() if self.entry_A.get() else 1.0),
                Q=float(self.entry_Q.get() if self.entry_Q.get() else 1.0),
                E_min=float(self.entry_Emin.get() if self.entry_Emin.get() else 0.1),
                E_max=float(self.entry_Emax.get() if self.entry_Emax.get() else 10.0),
                sampling_mode=enum_mode
                # rotation_deg przyjmie domyślnie -0.3 stopnia z definicji dataclass!
            )
            
            # Przekazujemy gotowy model do ViewModelu sesji.
            # VM asynchronicznie odpali Pushera i Ekstraktor w tle, po czym odświeży ekrany!
            self.vm.add_parabola(new_parabola)
            self.destroy()
            
        except ValueError:
            self.vm._notify_status_change("BŁĄD Formularza: Masa, Ładunek i Energie muszą być liczbami!")

class ParabolaConfigPopup(ctk.CTkToplevel):
    def __init__(self, master, viewmodel: WorkspaceViewModel, edit_index: int = None, **kwargs):
        super().__init__(master, **kwargs)
        self.vm = viewmodel
        self.edit_index = edit_index
        
        self.title("✏️ Edycja paraboli" if edit_index is not None else "➕ Dodaj nową parabolę")
        self.geometry("400x500")
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # --- POLA FORMULARZA ---
        self.entry_name = self._add_form_row("Nazwa identyfikacyjna:", "np. Proton (H+)")
        self.entry_A = self._add_form_row("Masa cząstki A [u]:", "1.0")
        self.entry_Q = self._add_form_row("Stan ładunkowy Q [e]:", "1.0")
        self.entry_E_min = self._add_form_row("Energia E_min [MeV]:", "0.1")
        self.entry_E_max = self._add_form_row("Energia E_max [MeV]:", "10.0")
        
        # Słupek wyboru metody próbkowania energii (Enum SamplingMode)
        row_enum = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row_enum.pack(fill="x", pady=6)
        ctk.CTkLabel(row_enum, text="Próbkowanie energii:", anchor="w", width=140).pack(side="left")
        
        # Pobieramy opcje tekstowe wprost z modelu Enuma
        enum_labels = [mode.label for mode in SamplingMode]
        self.combo_sampling = ctk.CTkComboBox(row_enum, values=enum_labels, height=26)
        self.combo_sampling.set(SamplingMode.QUADRATIC.label)
        self.combo_sampling.pack(side="right", fill="x", expand=True)
        
        # --- PRZYCISKI AKCJI ---
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=(25, 0))
        
        self.btn_submit = ctk.CTkButton(self.btn_frame, text="Edytuj ślad", command=self._on_submit_click, fg_color="#2b73b5", hover_color="#225c91")
        self.btn_submit.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Anuluj", command=self.destroy, fg_color="#444444", hover_color="#555555")
        self.btn_cancel.pack(side="right", padx=5)

        if self.edit_index is not None:
            p = self.vm.parabolas_list[self.edit_index]
            self.entry_name.insert(0, p.name)
            self.entry_A.insert(0, str(p.A))
            self.entry_Q.insert(0, str(p.Q))
            self.entry_E_min.insert(0, str(p.E_min))
            self.entry_E_max.insert(0, str(p.E_max))
            self.combo_sampling.set(p.sampling_mode)
            # ... upewnij się, że czyścisz domyślne placeholder-y przed insertem!

    def _add_form_row(self, label_text, placeholder):
        row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=label_text, anchor="w", width=140).pack(side="left")
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=26)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _on_submit_click(self):
        """Zapisuje dane ze zmienionego formularza."""
        try:
            name_val = self.entry_name.get().strip()
            name = name_val if name_val else "Jon nienazwany"
            
            A = float(self.entry_A.get().strip() if self.entry_A.get().strip() else 1.0)
            Q = float(self.entry_Q.get().strip() if self.entry_Q.get().strip() else 1.0)
            E_min = float(self.entry_E_min.get().strip() if self.entry_E_min.get().strip() else 0.1)
            E_max = float(self.entry_E_max.get().strip() if self.entry_E_max.get().strip() else 10.0)
            
            sampling_mode = SamplingMode.from_label(self.combo_sampling.get())

            if self.edit_index is not None:
                # TRYB EDYCJI: Przypisanie czystych wartości (BEZ PRZECINKÓW NA KOŃCU!)
                p = self.vm.parabolas_list[self.edit_index]
                p.name = name
                p.A = A
                p.Q = Q
                p.E_min = E_min
                p.E_max = E_max
                p.sampling_mode = sampling_mode
                
                # Przeliczenie i odświeżenie w tle
                self.vm._notify_status_change(f"Zaktualizowano parametry dla {p.name}. Trwa przeliczanie...")
                self.vm.recalculate_single_parabola(self.edit_index)
            else:
                # TRYB TWORZENIA NOWEJ PARABOLI
                new_parabola = ParabolaConfig(name, A, Q, E_min, E_max, sampling_mode)
                self.vm.add_parabola(new_parabola)
                
            self.destroy()
            
        except ValueError as e:
            print(f"Błąd walidacji formularza: {e}")