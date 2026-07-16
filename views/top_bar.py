# views/top_bar.py
import customtkinter as ctk
from tkinter import filedialog
from viewmodels.workspace_vm import WorkspaceViewModel

# Importujemy popupy, które za chwilę powstaną/zostaną zmodyfikowane
# Wykorzystamy technikę leniwego importu lub założymy ich istnienie w views.windows_popup
from views.windows_popup import HardwareParamsPopup, AddParabolaPopup

class TopBarFrame(ctk.CTkFrame):
    def __init__(self, master, viewmodel: WorkspaceViewModel, **kwargs):
        """
        Górny pasek narzędziowy (Toolbar) do zarządzania sesją eksperymentu TPS.
        """
        # Nadajemy ramce delikatnie ciemniejszy odcień lub pozostawiamy standardowy dla spójności
        super().__init__(master, height=50, **kwargs)
        self.vm = viewmodel
        
        # --- LOGO / NAZWA APLIKACJI (LEWA STRONA) ---
        self.title_label = ctk.CTkLabel(
            self, 
            text="pyTPSeer 🦊", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        # V-line separator (wizualne odcięcie loga)
        self.separator = ctk.CTkFrame(self, width=2, height=30, fg_color="#444444")
        self.separator.pack(side="left", padx=10, pady=10)

        # --- PRZYCISKI AKCJI (UKŁADANE HORYZONTALNIE OD LEWEJ) ---
        
        # 1. Przycisk ładowania pliku .tif/.png
        self.btn_load = ctk.CTkButton(
            self, 
            text="📂 Wczytaj obraz", 
            command=self._on_load_file_click,
            width=150
        )
        self.btn_load.pack(side="left", padx=10, pady=10)

        self.btn_hardware = ctk.CTkButton(
            self, 
            text="⚙️ Parametry TPS", 
            command=self._on_hardware_click,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            width=180
        )
        self.btn_hardware.pack(side="left", padx=10, pady=10)

        self.btn_set_zero = ctk.CTkButton(
            self, 
            text="📍 Zaznacz punkt zero", 
            command=self._on_set_zero_click,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            width=160
        )
        self.btn_set_zero.pack(side="left", padx=5, pady=10)

        self.btn_add_ion = ctk.CTkButton(
            self, 
            text="➕ Dodaj nową parabolę", 
            command=self._on_add_parabola_click,
            fg_color="#2b73b5",
            hover_color="#225c91",
            width=180
        )
        self.btn_add_ion.pack(side="left", padx=10, pady=10)

    # =========================================================================
    # REAKCJE NA KLIKNIĘCIA (DELEGACJA DO VIEWMODELU LUB POPUPÓW)
    # =========================================================================

    def _on_load_file_click(self):
        """Otwiera systemowe okno wyboru pliku i przekazuje ścieżkę do ViewModelu."""
        file_path = filedialog.askopenfilename(
            title="Wybierz kadr z detektora spektrometru",
            filetypes=[
                ("Obrazy TIFF", "*.tif *.tiff"),
                ("Obrazy PNG", "*.png"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        
        if file_path: # Jeśli użytkownik nie kliknął 'Anuluj'
            # ViewModel przejmuje kontrolę: załaduje obraz, wyczyści stare parabole,
            # powiadomi paski statusu i kopnie canvasy do odświeżenia ekranu!
            self.vm.load_image(file_path)

    def _on_hardware_click(self):
        """Otwiera okno edycji parametrów geometrycznych i pól (B, E)."""
        # Tworzymy popup jako okno zależne (Toplevel) i wstrzykujemy mu ViewModel
        popup = HardwareParamsPopup(master=self.winfo_toplevel(), viewmodel=self.vm)
        popup.grab_set() # Blokuje interakcję z oknem głównym, dopóki popup jest otwarty

    def _on_add_parabola_click(self):
        """Otwiera formularz dodawania nowego jonu (formularz A, Q, E_min, E_max)."""
        if self.vm.mcp_model is None:
            # Małe zabezpieczenie z poziomu widoku, żeby nie dodawać jonów do próżni
            self.vm._notify_status_change("BŁĄD: Najpierw wczytaj obraz detektora!")
            return
            
        popup = AddParabolaPopup(master=self.winfo_toplevel(), viewmodel=self.vm)
        popup.grab_set()

    def _on_set_zero_click(self):
        """Przełącza system w tryb nasłuchiwania kliknięcia myszką na wykresie."""
        if self.vm.mcp_model is None:
            self.vm._notify_status_change("BŁĄD: Najpierw wczytaj obraz!")
            return
        
        self.vm.is_selecting_start = not self.vm.is_selecting_start
        
        if self.vm.is_selecting_start:
            self.btn_set_zero.configure(
                text="🎯 Kliknij na obrazie...", 
                fg_color="#2ba361",
                hover_color="#207a48"
            )
            self.vm._notify_status_change("Tryb wyboru aktywny. Kliknij lewym przyciskiem myszy w centrum pinhole.")
        else:
            self.reset_zero_button()
            self.vm._notify_status_change("Wyłączono tryb wyboru.")

    def reset_zero_button(self):
        """Przywraca domyślny wygląd przycisku."""
        self.btn_set_zero.configure(text="📍 Zaznacz punkt zero", fg_color="#3a3a3a", hover_color="#4a4a4a")