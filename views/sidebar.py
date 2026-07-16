# views/sidebar.py
import customtkinter as ctk
from viewmodels.workspace_vm import WorkspaceViewModel

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, viewmodel: WorkspaceViewModel):
        super().__init__(master)
        self.vm = viewmodel
        
        # --- PRZYKŁAD: Pola tekstowe parametrów komory spektrometru ---
        self.b_field_entry = ctk.CTkEntry(self, placeholder_text="B Field [T]")
        self.b_field_entry.insert(0, str(self.vm.tps_params.B_field))
        self.b_field_entry.pack(pady=5)
        
        self.btn_apply_hardware = ctk.CTkButton(
            self, text="Zastosuj pola komory", command=self._on_apply_hardware_click
        )
        self.btn_apply_hardware.pack(pady=5)

        # --- PRZYKŁAD: Pasek statusu (Data Binding dla tekstu) ---
        self.status_label = ctk.CTkLabel(self, text="Status: Oczekiwanie...", text_color="gray")
        self.status_label.pack(side="bottom", fill="x", pady=10)

    def _on_apply_hardware_click(self):
        """Zczytuje interfejs i bezpiecznie przesyła słownik zmian do ViewModelu"""
        gui_changes = {
            "B_field": self.b_field_entry.get(),
            # "E_field": self.e_field_entry.get(), ... dopisujesz resztę pól GUI
        }
        # ViewModel sam to zwaliduje w osobnym wątku tła!
        self.vm.update_hardware_parameters(gui_changes)

    def _on_parabola_slider_move(self, parabola_idx: int, new_angle_value: float):
        """
        Wywoływane np. podczas przesuwania suwaka przypisanego do konkretnej paraboli.
        Przekazuje indeks jona z listy oraz nową rotację prosto do asynchronicznego worker-a.
        """
        self.vm.update_parabola_rotation(idx=parabola_idx, new_deg=new_angle_value)

    def update_status_label(self, message: str):
        """CALLBACK: ViewModel wywoła to automatycznie, gdy zmieni się stan operacji"""
        self.status_label.configure(text=f"Status: {message}")