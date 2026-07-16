# viewmodels/workspace_vm.py
import threading
from typing import Callable, Optional
from models.mcp_image import MCPImage
from models.parabola_config import ParabolaConfig
from models.tps_parameters import TPSParameters
import core.numerical_engine as engine  # Compiled engine @njit
import config

class WorkspaceViewModel:
    def __init__(self):
        # --- Data ---
        self.mcp_model: Optional[MCPImage] = None
        self.tps_params: TPSParameters = TPSParameters()
        self.parabolas_list: list[ParabolaConfig] = []  # POPRAWKA: poprawny zapis list[T]

        # --- (UI STATE) ---
        # self.rotation_deg: float = -0.3
        self.is_selecting_start: bool = False  # POPRAWKA: czysty Python 'bool' zamiast Numby
        self.active_cmap: str = "inferno"

        # --- System EVENT (OBSERVER PATTERN / DATA BINDING) ---
        self._plots_update_callbacks: list[Callable[[], None]] = []
        self._status_change_callbacks: list[Callable[[str], None]] = []


        self._target_rotations: dict[int, float] = {}
        self._last_calculated_rotations: dict[int, float] = {}
        self._throttler_running = False

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
        """Ładuje i normalizuje nowe zdjęcie MCP"""
        self._notify_status_change("Ładowanie i normalizacja obrazu...")
        img = MCPImage.load_and_normalize(file_path)
        
        if img is not None:
            self.mcp_model = img
            self.parabolas_list.clear()  # Nowe zdjęcie resetuje aktywne jony
            self._notify_status_change(f"Załadowano kadr: {img.width}x{img.height}")
            self._notify_plots_update()
        else:
            self._notify_status_change("BŁĄD: Nie udało się wczytać pliku graficznego!")

    def set_start_point(self, x_m: float, y_m: float):
        """Ustawia punkt zero (start point) dla układu spektrometru"""
        if self.mcp_model is not None:
            self.mcp_model.start_point = (x_m, y_m)
            self._notify_status_change(f"Ustawiono punkt zero: X={x_m:.4f}m, Y={y_m:.4f}m")
            self.recalculate_all_parabolas()  # Punkt zero wymusza przeliczenie wszystkiego

    def add_parabola(self, config_data: ParabolaConfig):
        """Dodaje nowy tor jonowy do sesji i od razu go przelicza"""
        self.parabolas_list.append(config_data)
        self._notify_status_change(f"Dodano jon: {config_data.name}. Uruchamianie analizy...")
        
        # Przeliczamy tylko tę jedną, nowo dodaną parabolę
        self.recalculate_single_parabola(len(self.parabolas_list) - 1)
        self._notify_plots_update()

    def update_rotation_angle(self, new_deg: float):
        """Aktualizuje kąt obrotu i przelicza geometrię oraz spektra"""
        self.rotation_deg = float(new_deg)
        self.recalculate_all_parabolas()
    
    def update_parabola_rotation(self, idx: int, new_deg: float):
        """Aktualizuje kąt obrotu tylko dla wybranej paraboli i ją przelicza"""
        if 0 <= idx < len(self.parabolas_list):
            p = self.parabolas_list[idx]
            p.rotation_parameter = float(new_deg)
            
            self.recalculate_single_parabola(idx)
            
            self._notify_status_change(f"Zmieniono rotację dla {p.name} na {new_deg} stopni.")
            self._notify_plots_update()

    def update_hardware_parameters(self, new_params: dict):
        """Aktualizuje i waliduje parametry komory spektrometru z pól tekstowych"""
        try:
            self.tps_params.update(**new_params)
            self._notify_status_change("Zaktualizowano parametry sprzętowe spektrometru.")
            self.recalculate_all_parabolas()
        except ValueError as err:
            # Przechwytujemy błąd z metody validate() modelu i przekazujemy do GUI
            self._notify_status_change(f"BŁĄD: {str(err)}")

    # =========================================================================
    # Connect Core with look
    # =========================================================================

    def recalculate_single_parabola(self, idx: int):
        """Pobiera czyste dane z modeli i przekazuje je do ciężkich pętli @njit w core"""
        if self.mcp_model is None or self.mcp_model.start_point is None:
            return
            
        p = self.parabolas_list[idx]
        x_zero, y_zero = self.mcp_model.start_point
        
        # 1. Wywołanie skompilowanego pushera trajektorii z core/numerical_engine.py
        x_points, y_points, E_sampling = engine.draw_parabole_jit(
            tps=self.tps_params,
            p_config=p,
            x_zero=x_zero,
            y_zero=y_zero,
            rotation_deg=p.rotation_parameter
        )
        
        # 2. Wywołanie skompilowanego kombajnu ekstrakcji widma z pikseli
        energies, dnde = engine.extract_tps_spectrum_jit(
            img_matrix=self.mcp_model.matrix,
            x_m=x_points,
            y_m=y_points,
            E_arr=E_sampling,
            parabola_config=p,
            tps_params=self.tps_params
        )
        
        # 3. Zapisujemy wyniki bezpośrednio do pamięci podręcznej (Cache) Modelu
        p.update(line_x=x_points, line_y=y_points, spec_E=energies, spec_dNdE=dnde)

    def recalculate_all_parabolas(self):
        """Przelicza całą sesję od nowa i wymusza odświeżenie ekranu"""
        if self.mcp_model is None:
            return
        for idx in range(len(self.parabolas_list)):
            self.recalculate_single_parabola(idx)
        self._notify_plots_update()

    def update_parabola_rotation(self, idx: int, new_deg: float):
        """
        Zbiera żądania zmiany kąta obrotu z GUI (z suwaka lub pola tekstowego).
        Zamiast od razu spawnować wątek, zapisuje tylko cel i uruchamia zegar taktujący.
        """
        if 0 <= idx < len(self.parabolas_list):
            self._target_rotations[idx] = float(new_deg)
            self.parabolas_list[idx].rotation_parameter = float(new_deg)
            
            # Jeśli zegar 33ms jeszcze nie tyka – uruchamiamy go!
            if not self._throttler_running:
                self._throttler_running = True
                self._run_throttler_tick()

    def _run_throttler_tick(self):
        """Sprawdza co ~33ms, czy któryś kąt różni się od ostatnio przeliczonego."""
        something_to_calculate = False
        active_idx = None
        
        for idx, target_val in list(self._target_rotations.items()):
            last_val = self._last_calculated_rotations.get(idx, None)
            if last_val is None or abs(target_val - last_val) > 1e-4:
                # Wartość się zmieniła! Musimy ją przeliczyć
                something_to_calculate = True
                active_idx = idx
                break  # Przeliczamy jedną na klatkę, by nie zablokować procesora

        if something_to_calculate and active_idx is not None:
            target_val = self._target_rotations[active_idx]
            self._last_calculated_rotations[active_idx] = target_val
            
            # Odpalamy szybki wątek w tle tylko dla tej konkretnej zmiany
            threading.Thread(
                target=self._async_recalculate_worker,
                args=(active_idx,),
                daemon=True
            ).start()
            
        # Taktowanie pętli (33ms = ok. 30 Hz). 
        # Wywołujemy to na kolejce zdarzeń głównego okna aplikacji.
        if hasattr(self, '_plots_update_callbacks') and self._plots_update_callbacks:
            # Ponieważ ViewModel nie ma bezpośredniego pojęcia o widgetach Tkintera,
            # wykorzystamy sztuczkę: poprosimy pierwszy zarejestrowany callback (MainWindow),
            # aby wywołał tę pętlę po 33 ms za pomocą swojej metody .after()
            main_window_instance = self._plots_update_callbacks[0].__self__
            main_window_instance.after(33, self._run_throttler_tick)
        else:
            self._throttler_running = False

    def update_parabola_rotation(self, idx: int, new_deg: float):
        """Asynchronicznie aktualizuje rotację i odpala wątek"""
        if 0 <= idx < len(self.parabolas_list):
            self.parabolas_list[idx].rotation_deg = float(new_deg)
            
            # Odpalamy obliczenia w osobnym wątku, żeby nie mrozić GUI!
            threading.Thread(
                target=self._async_recalculate_worker, 
                args=(idx,), 
                daemon=True # Daemon=True sprawi, że wątek zamknie się automatycznie, jeśli zamkniesz aplikację
            ).start()

    def _async_recalculate_worker(self, idx: int):
        """Ta funkcja wykonuje się w TLE (w osobnym wątku procesora)"""
        if self.mcp_model is None or self.mcp_model.start_point is None:
            return

        self.is_calculating = True
        self._notify_status_change("Silnik Numba liczy widmo w tle...")

        p = self.parabolas_list[idx]
        x_zero, y_zero = self.mcp_model.start_point
        
        # 1. Ciężka fizyka (dzięki nogil=True w core nie blokuje to okienka!)
        x_points, y_points, E_sampling = engine.draw_parabole_jit(
            self.tps_params, p, x_zero, y_zero, p.rotation_deg
        )
        
        energies, dnde = engine.extract_tps_spectrum_jit(
            self.mcp_model.matrix, x_points, y_points, E_sampling, p, self.tps_params
        )
        
        # 2. Zapis do pamięci podręcznej (Cache)
        p.update(line_x=x_points, line_y=y_points, spec_E=energies, spec_dNdE=dnde)

        # 3. Koniec pracy
        self.is_calculating = False
        self._notify_status_change(f"Ukończono analizę dla {p.name}.")
        
        # Kopnięcie widoku, żeby się przerysował
        self._notify_plots_update()

    def recalculate_all_parabolas(self):
        """Odpala przeliczenie całej sesji w jednym osobnym wątku zbiorczym"""
        if self.mcp_model is None:
            return
            
        def run_all():
            for idx in range(len(self.parabolas_list)):
                # Wywołujemy samą logikę matematyczną sekwencyjnie wewnątrz tego jednego wątku tła
                self._async_recalculate_worker(idx)
                
        threading.Thread(target=run_all, daemon=True).start()