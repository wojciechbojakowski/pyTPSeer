# viewmodels/workspace_vm.py
import threading
from typing import Callable, Optional

import numpy as np
from models.mcp_image import MCPImage
from models.parabola_config import ParabolaConfig
from models.tps_parameters import TPSParameters
import core.numerical_engine as engine
import config

class WorkspaceViewModel:
    def __init__(self):
        # --- Data ---
        self.mcp_model: Optional[MCPImage] = None
        self.tps_params: TPSParameters = TPSParameters()
        self.parabolas_list: list[ParabolaConfig] = []

        # --- (UI STATE) ---
        self.is_selecting_start: bool = False
        self.active_cmap: str = "inferno"

        # --- System EVENT ---
        self._plots_update_callbacks: list[Callable[[], None]] = []
        self._status_change_callbacks: list[Callable[[str], None]] = []


        self.pinned_spectra: dict[str, tuple[np.ndarray, npParabolaConfig.ndarray, str]] = {}

    # =========================================================================
    # BIND with look
    # =========================================================================
    
    def bind_plots_update(self, callback: Callable[[], None]):
        """Widok rejestruje tu funkcję np. self.refresh_interface"""
        self._plots_update_callbacks.append(callback)

    def bind_status_change(self, callback: Callable[[str], None]):
        """Widok rejestruje tu funkcję aktualizacji paska statusu"""
        self._status_change_callbacks.append(callback)

    def _notify_plots_update(self):
        """Powiadamia wszystkie podpięte Widoki o konieczności przerysowania wykresów"""
        for callback in self._plots_update_callbacks:
            callback()

    def _notify_status_change(self, message: str):
        """Wysyła nowy komunikat tekstowy do paska statusu w Widoku"""
        for callback in self._status_change_callbacks:
            callback(message)

    # =========================================================================
    # User actions
    # =========================================================================

    def load_image(self, file_path: str):
        """LOAD IMAGE"""
        self._notify_status_change("Ładowanie i normalizacja obrazu...")
        img = MCPImage.load_and_normalize(file_path)
        
        if img is not None:
            self.mcp_model = img
            self.parabolas_list.clear()
            self._notify_status_change(f"Załadowano kadr: {img.width}x{img.height}")
            self._notify_plots_update()
            max_intensity = float(np.max(self.mcp_model.raw_matrix))
        else:
            self._notify_status_change("BŁĄD: Nie udało się wczytać pliku graficznego!")

    def set_start_point(self, x_m: float, y_m: float):
        """Set zero point"""
        if self.mcp_model is not None:
            self.mcp_model.start_point = (x_m, y_m)
            self._notify_status_change(f"Ustawiono punkt zero: X={x_m:.4f}m, Y={y_m:.4f}m")
            self.recalculate_all_parabolas()

    def add_parabola(self, config_data: ParabolaConfig):
        """Add parabola"""
        self.parabolas_list.append(config_data)
        self._notify_status_change(f"Dodano jon: {config_data.name}. Uruchamianie analizy...")
        
        self.recalculate_single_parabola(len(self.parabolas_list) - 1)
        self._notify_plots_update()
    
    def update_parabola_rotation(self, idx: int, new_deg: float):
        """Update idx parabola rotation"""
        if 0 <= idx < len(self.parabolas_list):
            p = self.parabolas_list[idx]
            p.rotation_parameter = float(new_deg)
            
            self.recalculate_single_parabola(idx)
            
            self._notify_status_change(f"Zmieniono rotację dla {p.name} na {new_deg:.2f} stopni.")
            self._notify_plots_update()

    def update_hardware_parameters(self, new_params: dict):
        """Update TPS parameters"""
        try:
            self.tps_params.update(**new_params)
            self._notify_status_change("Zaktualizowano parametry sprzętowe spektrometru.")
            self.recalculate_all_parabolas()
        except ValueError as err:
            self._notify_status_change(f"BŁĄD: {str(err)}")

    # =========================================================================
    # Connect Core with look
    # =========================================================================

    def recalculate_single_parabola(self, idx: int):
        """Data from models to engine"""
        if self.mcp_model is None or self.mcp_model.start_point is None:
            return
            
        p = self.parabolas_list[idx]
        x_zero, y_zero = self.mcp_model.start_point
        
        x_points, y_points, E_sampling = engine.draw_parabole_jit(
            tps=self.tps_params,
            p_config=p,
            x_zero=x_zero,
            y_zero=y_zero,
            rotation_deg=p.rotation_parameter
        )
        
        energies, dnde = engine.extract_tps_spectrum_jit(
            img_matrix=self.mcp_model.matrix,
            x_m=x_points,
            y_m=y_points,
            E_arr=E_sampling,
            parabola_config=p,
            tps_params=self.tps_params
        )

        if energies is not None and len(energies) > 0:
            # Zakładamy dystans np. L = 1.0 m (można to wziąć z config.TPS_PARAMS)
            L_flight = self.tps_params.pin_target 
            
            p.cached_tof_t, p.cached_tof_signal = engine.calculate_tof_spectrum(
                E_array_MeV=energies,
                dNdE_array=dnde,
                A=p.A,
                L_path_m=L_flight
            )
        
        p.update(line_x=x_points, line_y=y_points, spec_E=energies, spec_dNdE=dnde)

    def recalculate_all_parabolas(self):
        """Calculate all parabola"""
        if self.mcp_model is None:
            return
        for idx in range(len(self.parabolas_list)):
            self.recalculate_single_parabola(idx)
        self._notify_plots_update()

    # def toggle_pin_parabola(self, idx: int, color: str):
    #     """Przypina lub odpina widmo danej paraboli, aby zachować je przy zmianie obrazu."""
    #     if not (0 <= idx < len(self.parabolas_list)):
    #         return
            
    #     p = self.parabolas_list[idx]
    #     pin_key = f"📌 {p.name} (Ref)"
        
    #     if pin_key in self.pinned_spectra:
    #         # Jeśli już było przypięte - odpinamy
    #         del self.pinned_spectra[pin_key]
    #         self._notify_status_change(f"Odpięto widmo referencyjne dla {p.name}.")
    #     else:
    #         # Przypinamy: zapisujemy kopie współrzędnych i zachowujemy kolor wykresu!
    #         if p.cached_spec_E is not None and len(p.cached_spec_E) > 0:
    #             self.pinned_spectra[pin_key] = (
    #                 p.cached_spec_E.copy(), 
    #                 p.cached_spec_dNdE.copy(), 
    #                 color
    #             )
    #             self._notify_status_change(f"Przypięto widmo {p.name} jako referencję do porównań!")
    #         else:
    #             self._notify_status_change("Błąd: Nie można przypiąć pustego widma (najpierw wylicz ślad).")
                
    #     self._notify_plots_update() # Odświeżamy wykresy, by narysować przypiętą linię
    
    # # viewmodels/workspace_vm.py

    def remove_pinned_spectrum(self, pin_key: str):
        """Usuwa konkretne widmo referencyjne i przerysowuje wykres 1D."""
        if pin_key in self.pinned_spectra:
            del self.pinned_spectra[pin_key]
            self._notify_status_change(f"Usunięto referencję: {pin_key}")
            self._notify_plots_update() # Natychmiast znika z wykresu!

    def toggle_pin_parabola(self, idx: int, color: str):
        """Przypina lub odpina widmo danej paraboli."""
        if not (0 <= idx < len(self.parabolas_list)):
            return
            
        p = self.parabolas_list[idx]
        pin_key = f"📌 {p.name} (Ref)"
        
        if pin_key in self.pinned_spectra:
            self.remove_pinned_spectrum(pin_key)
        else:
            if p.cached_spec_E is not None and len(p.cached_spec_E) > 0:
                self.pinned_spectra[pin_key] = (
                    p.cached_spec_E.copy(), 
                    p.cached_spec_dNdE.copy(), 
                    color
                )
                self._notify_status_change(f"Przypięto widmo {p.name} jako referencję.")
            else:
                self._notify_status_change("Błąd: Nie można przypiąć pustego widma.")
                
            self._notify_plots_update()

    def set_background_threshold(self, threshold_val: float):
        """Ustawia nowy poziom odcięcia tła i wymusza ponowne przeliczenie widm."""
        if self.mcp_model is None:
            return
            
        self.mcp_model.background_threshold = float(threshold_val)
        
        # Skoro zmieniliśmy tło obrazu, musimy przeliczyć wykresy energii/TOF dla wszystkich parabol!
        self.recalculate_all_parabolas()