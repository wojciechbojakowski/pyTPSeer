# viewmodels/workspace_vm.py
import os
import threading
from typing import Callable, Optional

from matplotlib import pyplot as plt
import copy
import numpy as np
from core.signal_processing import apply_spectrum_smoothing
from models.mcp_image import MCPImage
from models.parabola_config import ParabolaConfig
from models.sampling_mode import SmoothingMode
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

        self.active_cmap=copy.copy(plt.cm.turbo)
        self.active_cmap.set_under('white')

        self.spectrum_smoothing_mode = SmoothingMode.NONE
        self.spectrum_smoothing_param = 2 #Propably it is for change
        
        # --- System EVENT ---
        self._plots_update_callbacks: list[Callable[[], None]] = []
        self._status_change_callbacks: list[Callable[[str], None]] = []


        self.pinned_spectra: dict[str, tuple[np.ndarray, np.ndarray, str]] = {}

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
            if self.mcp_model is not None and self.mcp_model.start_point is not None:
                img.start_point = self.mcp_model.start_point
            self.mcp_model = img
            if self.parabolas_list:
                self.recalculate_all_parabolas()
            #self.parabolas_list.clear()
            file_name = os.path.basename(file_path)
            self._notify_status_change(f"Załadowano kadr: {file_name} {img.width}x{img.height}")
            self._notify_plots_update()
            max_intensity = float(np.max(self.mcp_model.raw_matrix))
        else:
            self._notify_status_change("BŁĄD: Nie udało się wczytać pliku graficznego! {file_path}")

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
        
        self.recalculate_all_parabolas()

    def export_spectrum_ascii(self, filepath: str):
        """
        Zapisuje widma energetyczne dN/dE wszystkich aktywnych i przypiętych parabol
        do pliku tekstowego w formacie ASCII (.dat / .txt / .csv).
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Nagłówek pliku z metadanymi
                f.write("# ==================================================\n")
                f.write("# pyTPSeer - Eksport Widma Energetycznego Jonów\n")
                if self.mcp_model:
                    f.write(f"# Plik źródłowy MCP: {os.path.basename(self.mcp_model.file_path)}\n")
                f.write(f"# Próg tła (Threshold): {getattr(self.mcp_model, 'background_threshold', 0.0):.2f}\n")
                f.write("# ==================================================\n\n")

                # 1. Zapis aktywnych trajektorii
                for p in self.parabolas_list:
                    if p.cached_spec_E is not None and len(p.cached_spec_E) > 0:
                        f.write(f"# --- Trajektoria: {p.name} (A={p.A}, Q={p.Q}, kat={p.rotation_parameter}, E_max={p.E_max}[MeV], E_min={p.E_min}[MeV]) ---\n")
                        f.write("# E_MeV_u\tdNdE_MeV1_sr1\n")
                        for e_val, dnde_val in zip(p.cached_spec_E, p.cached_spec_dNdE):
                            f.write(f"{e_val:.6e}\t{dnde_val:.6e}\n")
                        f.write("\n")
                # 2. Zapis przypiętych widm referencyjnych (jeśli istnieją)
                if self.pinned_spectra:
                    f.write("# ==================================================\n")
                    f.write("# WIDMA REFERENCYJNE (PRZYPIĘTE 📌)\n")
                    f.write("# ==================================================\n\n")
                    for pin_key, data in self.pinned_spectra.items():
                        if isinstance(data, tuple):
                            spec_E, spec_dNdE, _ = data
                        else:
                            spec_E, spec_dNdE = data.E, data.dNdE
                        
                        f.write(f"# --- {pin_key} ---\n")
                        f.write("# E_MeV_u\tdNdE_MeV1_sr1\n")
                        for e_val, dnde_val in zip(spec_E, spec_dNdE):
                            f.write(f"{e_val:.6e}\t{dnde_val:.6e}\n")
                        f.write("\n")

            self._notify_status_change(f"Pomyślnie wyeksportowano widmo ASCII: {os.path.basename(filepath)}")

        except Exception as e:
            self._notify_status_change(f"Błąd eksportu ASCII: {e}")

    
    def export_batch_series(self, output_dir: str = None):
        """
        Automatycznie przetwarza wszystkie pliki graficzne w bieżącym folderze,
        używając aktualnego punktu zero, parametrów TPS oraz zdefiniowanych parabol.
        Zapisuje widma ASCII do katalogu wyjściowego.
        """
        if self.mcp_model is None or not self.parabolas_list:
            self._notify_status_change("BŁĄD: Brak załadowanego obrazu lub parabol do przetwarzania!")
            return

        current_folder = os.path.dirname(self.mcp_model.file_path)
        if output_dir is None:
            output_dir = os.path.join(current_folder, "processed_spectra")
        
        os.makedirs(output_dir, exist_ok=True)

        valid_exts = ('.tif', '.tiff', '.png', '.root')
        files = sorted([f for f in os.listdir(current_folder) if f.lower().endswith(valid_exts)])

        processed_count = 0

        for file_name in files:
            full_path = os.path.join(current_folder, file_name)
            
            # Ładujemy obraz i przeliczamy ekstrakcję widm
            self.load_image(full_path)
            
            # Zapisujemy wyniki dla każdej paraboli
            base_name = os.path.splitext(file_name)[0]
            for p in self.parabolas_list:
                if p.cached_spec_E is not None and len(p.cached_spec_E) > 0:
                    out_file = os.path.join(output_dir, f"{base_name}_{p.name}_spectrum.dat")
                    
                    # Zapis kolumn: Energia [MeV/u], dN/dE [MeV^-1 sr^-1]
                    data_to_save = np.column_stack((p.cached_spec_E, p.cached_spec_dNdE))
                    header = f"Spectrum for {p.name} (A={p.A}, Q={p.Q})\nFile: {file_name}\nE_MeV/u\tdN/dE"
                    np.savetxt(out_file, data_to_save, fmt="%.6e", delimiter="\t", header=header)

            processed_count += 1

        self._notify_status_change(f"Pomyślnie przetworzono serię {processed_count} plików -> {output_dir}")

    
    def remove_parabola(self, parabola):
        """Usuwa wskazaną parabolę z listy sesji i odświeża wykresy."""
        if parabola in self.parabolas_list:
            self.parabolas_list.remove(parabola)
            
            self._notify_plots_update()
            self._notify_status_change(f"Usunięto parabolę: {parabola.name}")

    def update_parabola_config(self, index: int, name: str, A: float, Q: float, E_min: float, E_max: float, sampling_mode, gamma: float):
        """Modyfikuje istniejącą parabolę, przelicza jej trajektorię i odświeża wykresy."""
        if 0 <= index < len(self.parabolas_list):
            p = self.parabolas_list[index]
            p.name = name
            p.A = A
            p.Q = Q
            p.E_min = E_min
            p.E_max = E_max
            p.sampling_mode = sampling_mode
            p.power_exponent = gamma
            
            self.recalculate_single_parabola(index)
            
            self._notify_plots_update()
            self._notify_status_change(f"Zaktualizowano parametry dla {p.name}.")

    def get_spectrum_data_for_plot(self, parabola_index: int):
        parabola = self.parabolas_list[parabola_index]
        energies = parabola.cached_spec_E
        dnde = parabola.cached_spec_dNdE
        
        # Przetwarzanie i wygładzanie odbywa się w warstwie logiki!
        if self.spectrum_smoothing_mode != SmoothingMode.NONE:
            dnde = apply_spectrum_smoothing(dnde, mode=self.spectrum_smoothing_mode, param=self.spectrum_smoothing_param)
            
        return energies, dnde

    def set_spectrum_smoothing(self, mode: SmoothingMode):
        self.spectrum_smoothing_mode = mode

        if mode == SmoothingMode.SAVGOL:
            self.spectrum_smoothing_param = 11.0
        elif mode == SmoothingMode.GAUSSIAN:
            self.spectrum_smoothing_param = 2.0

        self._notify_status_change(f"Zmieniono wygładzanie widma na: {mode.name}")
        self._notify_plots_update()