# views/main_window.py
import customtkinter as ctk
from views.top_bar import TopBarFrame         
from views.bottom_control import BottomControlFrame
from views.plot_canvas import MCPCanvas, PlotCanvas1D
from viewmodels.workspace_vm import WorkspaceViewModel
import config

class MainWindow(ctk.CTk):
    def __init__(self, viewmodel: WorkspaceViewModel):
        super().__init__()
        self.vm = viewmodel
        self.color_palette = ['#ff0054', '#390099', '#ffbd00', '#00b4d8']

        self.title(config.NAME)
        self.geometry("1400x900")
        
        # --- KONFIGURACJA SIATKI GŁÓWNEJ (3 RZĘDY) ---
        self.grid_rowconfigure(0, weight=0)  
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # =========================================================================
        # 1. RZĄD GÓRNY: Pasek przycisków i popupów (Smażony na całą szerokość)
        # =========================================================================
        self.top_bar = TopBarFrame(master=self, viewmodel=self.vm)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        # =========================================================================
        # 2. RZĄD ŚRODKOWY: Kolumna 1 (Zdjęcie MCP) | Kolumna 2 (Widma dN/dE + TOF)
        # =========================================================================
        # Lewa kolumna: Główna grafika MCP
        self.plot_frame = MCPCanvas(master=self)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Prawa kolumna: Kontener na dwa wykresy (Energia + TOF) ułożone w pionie
        self.right_plots_container = ctk.CTkFrame(master=self, fg_color="transparent")
        self.right_plots_container.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        self.right_plots_container.grid_rowconfigure(0, weight=1)
        self.right_plots_container.grid_rowconfigure(1, weight=1)
        self.right_plots_container.grid_columnconfigure(0, weight=1)
        
        # Wykres Energii (Górny w prawej kolumnie)
        self.spectrum_frame = PlotCanvas1D(master=self.right_plots_container,is_log_y=True)
        self.spectrum_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=5)
        
        # Wykres TOF (Dolny w prawej kolumnie - na razie placeholder)
        self.tof_frame = PlotCanvas1D(master=self.right_plots_container)
        self.tof_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)
        self._init_tof_placeholder()

        # =========================================================================
        # 3. RZĄD DOLNY: Przeglądarka folderu, rotacja i lista parabol
        # =========================================================================
        self.bottom_control = BottomControlFrame(master=self, viewmodel=self.vm)
        self.bottom_control.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.plot_frame.canvas.mpl_connect('button_press_event', self._on_plot_click)
        # =========================================================================
        # REAKTYWNE BINDOWANIE MVVM
        # =========================================================================
        self.vm.bind_plots_update(self.refresh_interface)
        self.vm.bind_status_change(self.bottom_control.update_status_label)

    def _init_tof_placeholder(self):
        """Inicjalizuje pusty wykres TOF czekający na implementację"""
        self.tof_frame.ax.clear()
        self.tof_frame.ax.set_title("Widmo czasu przelotu TOF (Oczekiwanie na implementację...)")
        self.tof_frame.ax.set_xlabel("Czas [ns]")
        self.tof_frame.ax.set_ylabel("Sygnał [a.u.]")
        self.tof_frame.ax.grid(True, linestyle="--", alpha=0.3)
        self.tof_frame.canvas.draw()

    def refresh_interface(self):
        """Bezpieczny wątkowo mechanizm odświeżania wykresów z cache"""
        self.after(0, self._safe_redraw_canvases)

    def _safe_redraw_canvases(self):
        if self.vm.mcp_model is None:
            return

        h, w = self.vm.mcp_model.shape
        extent_sizes = [0, w * config.PX_TO_METER, 0, h * config.PX_TO_METER]

        self.plot_frame.draw_detector_frame(
            img_matrix=self.vm.mcp_model.matrix, 
            extent_sizes=extent_sizes, 
            start_point=self.vm.mcp_model.start_point,
            cmap=self.vm.active_cmap
        )
        
        self.spectrum_frame.clear_and_setup(
            title="Widmo różniczkowe energii jonów",
            xlabel="Energia [MeV/u]",
            ylabel="dN/dE [MeV$^{-1}$ sr$^{-1}$]"
        )

        self.tof_frame.clear_and_setup(
            title="Widmo czasu przelotu (Time-of-Flight)",
            xlabel="Czas przelotu t [ns]",
            ylabel="Sygnał TOF [a.u.]"
        )

        # =========================================================================
        # NOWOŚĆ: Najpierw rysujemy PRZYPIĘTE WIDMA z innych obrazów (jako tło porównawcze)
        # =========================================================================
        for label, (pinned_E, pinned_dNdE, orig_color) in self.vm.pinned_spectra.items():
            # Rysujemy je przerywaną linią '--', żeby odróżniały się od aktywnych śladów
            self.spectrum_frame.plot_series(
                x=pinned_E, 
                y=pinned_dNdE, 
                color=orig_color, 
                label=label, 
                draw_points=False # Sama linia przerywana
            )
            # Stylizujemy linię referencyjną na przerywaną bezpośrednio w osiach:
            self.spectrum_frame.ax.lines[-1].set_linestyle("--")
            self.spectrum_frame.ax.lines[-1].set_alpha(0.7) # Delikatnie przezroczysta
            
        for idx, p in enumerate(self.vm.parabolas_list):
            color = self.color_palette[idx % len(self.color_palette)]
            
            # MCP dostaje nakładkę linii
            if p.cached_line_x is not None:
                self.plot_frame.draw_parabola_overlay(p.cached_line_x, p.cached_line_y, color, p.name)
                print(f"LOG 110 {idx}")
            
            # Spektrum 1D dostaje serię punktów
            if p.cached_spec_E is not None and len(p.cached_spec_E) > 0:
                self.spectrum_frame.plot_series(p.cached_spec_E, p.cached_spec_dNdE, color, p.name, draw_points=True)
                print(f"LOG 115 {idx}")

            if p.cached_tof_t is not None and len(p.cached_tof_t) > 0:
                self.tof_frame.plot_series(p.cached_tof_t, p.cached_tof_signal, color, p.name, draw_points=False)
                print(f"LOG 138 {idx}")

        # 4. Finalizujemy i odświeżamy ekrany
        self.spectrum_frame.finalize_plot()
        
        self.plot_frame.draw()
        self.spectrum_frame.draw()
        self.tof_frame.draw()
        self.bottom_control.refresh_parabola_list(self.color_palette)

    def _on_plot_click(self, event):
        """Wywoływane przy każdym kliknięciu na obszarze wykresu Matplotlib."""
        # Sprawdzamy czy kliknięto wewnątrz osi oraz czy aktywny jest tryb wyboru w VM
        if event.inaxes == self.plot_frame.ax and self.vm.is_selecting_start:
            x_m = event.xdata
            y_m = event.ydata
            
            if x_m is not None and y_m is not None:
                # Przekazujemy fizyczne koordynaty w metrach bezpośrednio do VM!
                self.vm.set_start_point(x_m, y_m)
                
                # Wyłączamy tryb wyboru
                self.vm.is_selecting_start = False
                self.top_bar.reset_zero_button()