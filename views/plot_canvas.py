# views/plot_canvas.py
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk

from models.sampling_mode import SmoothingMode

# =========================================================================
# 1. BAZOWA KLASA (Wspólna kuchnia Tkintera i Matplotlib)
# =========================================================================
class BasePlotCanvas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        """Wspólny fundament dla każdego wykresu w aplikacji."""
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Tworzenie ciemnego okna wykresu
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor="#2b2b2b", tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e1e")
        
        # Rejestracja backendu Tkintera
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.config(bg="#2b2b2b", highlightthickness=0)
        self.canvas_widget.pack(side="top", fill="both", expand=True)
        
        self._apply_dark_theme_styles()

    def _apply_dark_theme_styles(self):
        """Ujednolicony ciemny motyw dla wszystkich osi."""
        theme_color = "white"
        grid_color = "#444444"

        self.ax.tick_params(colors=theme_color, which='both', labelsize=9)
        self.ax.xaxis.label.set_color(theme_color)
        self.ax.yaxis.label.set_color(theme_color)
        self.ax.title.set_color(theme_color)
        
        for spine in self.ax.spines.values():
            spine.set_color(grid_color)
            
        self.ax.grid(True, which="both", linestyle="--", color=grid_color, alpha=0.3)

    def draw(self):
        """Odświeżenie rysunku na ekranie."""
        self.canvas.draw()


# =========================================================================
# 2. WIDGET SPECJALISTYCZNY: MCPCanvas (Obraz 2D + Nakładki)
# =========================================================================
class MCPCanvas(BasePlotCanvas):
    def __init__(self, master, **kwargs):
        """Dedykowany do wyświetlania kadru MCP z paskiem narzędzi."""
        super().__init__(master, **kwargs)
        self.cbar = None

        self.fig.set_layout_engine('none') 
        self.fig.subplots_adjust(left=0.15, bottom=0.15, right=0.82, top=0.90)

        self.grid_rowconfigure(0, weight=1)  # Rząd 0 (Wykres) - bierze całą przestrzeń
        self.grid_rowconfigure(1, weight=0)  # Rząd 1 (Toolbar) - ma stałą wysokość
        self.grid_columnconfigure(0, weight=1)
        
        # Osadzamy wykres w rzędzie 0
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")
        
        # Tworzymy dedykowaną, odizolowaną ramkę na toolbar
        # Dzięki temu wewnętrzne pack() toolbara nie zepsują nam głównego okna!
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=35)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Inicjalizujemy toolbar wewnątrz jego prywatnej ramki
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        
        for child in self.toolbar.winfo_children():
            try:
                child.config(background="#2b2b2b")
            except Exception:
                pass 
                
            try:
                child.config(foreground="white")
            except Exception:
                pass 
                
        self.toolbar.pack(side="bottom", fill="x")

    def draw_detector_frame(self, img_matrix, cmap, extent_sizes: list, start_point=None):
        """Czyści tło i nanosi surowy obraz z detektora wraz ze skalą intensywności."""
        old_xlim = self.ax.get_xlim()
        old_ylim = self.ax.get_ylim()
        
        first_time = (old_xlim == (0.0, 1.0) and old_ylim == (0.0, 1.0))

        self.ax.clear()
        self._apply_dark_theme_styles()

        if isinstance(cmap, str):
            quantized_cmap = plt.colormaps[cmap].resampled(20)
        else:
            quantized_cmap = cmap.resampled(20)

        im = self.ax.imshow(img_matrix, cmap=quantized_cmap, extent=extent_sizes, vmin=1e-6)
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        
        if self.cbar is None:
            self.cbar = self.fig.colorbar(im, ax=self.ax, fraction=0.046, pad=0.05)
            self.cbar.ax.set_ylabel("Jasność / Sygnał [a.u.]", color='white', labelpad=10)
            self.cbar.outline.set_edgecolor('#444444')
        else:
            self.cbar.update_normal(im)

        if not first_time:
            self.ax.set_xlim(old_xlim)
            self.ax.set_ylim(old_ylim)
            
        self.cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
        
        if start_point is not None:
            x_zero, y_zero = start_point
            self.ax.plot(x_zero, y_zero, 'rx', markersize=5, markeredgewidth=2, label="Pinhole")

    def draw_parabola_overlay(self, x, y, color: str, label: str):
        """Nanosi teoretyczną linię paraboli bezpośrednio na zdjęcie."""
        self.ax.plot(x, y, '-', color=color, linewidth=1.5, label=label)


# =========================================================================
# 3. WIDGET SPECJALISTYCZNY: PlotCanvas1D (Wykresy Liniowe/Spektra)
# =========================================================================
class PlotCanvas1D(BasePlotCanvas):
    def __init__(self, master, is_log_y: bool = False, **kwargs):
        """Dedykowany do wykresów funkcyjnych (Widmo energii, TOF)."""
        super().__init__(master, **kwargs)
        self.is_log_y = is_log_y

    def clear_and_setup(self, title: str, xlabel: str, ylabel: str):
        """Przygotowuje czystą przestrzeń pod nowe serie danych."""
        self.ax.clear()
        self._apply_dark_theme_styles()
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

    def plot_series(self, x, y, color: str, label: str, draw_points: bool = False):
        """Dodaje linię lub punkty serii danych."""
        style = '.-' if draw_points else '-'
        markersize = 3 if draw_points else 0
        
        self.ax.plot(
            x, y, 
            style, 
            color=color, 
            linewidth=1.5, 
            markersize=markersize, 
            label=label
        )

    def finalize_plot(self):
        """Nakłada legendę i wymusza skale (np. logarytmiczną) przed odświeżeniem."""
        if self.is_log_y:
            self.ax.set_yscale('log')
        
        # Wyświetlamy legendę tylko jeśli są jakieś serie z etykietami
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            legend = self.ax.legend(facecolor='#2b2b2b', edgecolor='#444444', loc='upper right')
            for text in legend.get_texts():
                text.set_color('white')
            
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

    def save_plot_png(self, filepath: str):
        """Zapisuje aktualny stan wykresu 1D do pliku PNG w wysokiej rozdzielczości."""
        try:
            self.fig.savefig(
                filepath, 
                dpi=300, 
                bbox_inches='tight', 
                facecolor=self.fig.get_facecolor(),
                edgecolor='none'
            )
            return True
        except Exception as e:
            print(f"Błąd zapisu obrazu PNG: {e}")
            return False


class SpectrumPlotCanvas(PlotCanvas1D):
    def __init__(self, master, viewmodel, is_log_y: bool = True, **kwargs):
        """
        Dedykowane płótno wykresu widma (1D) w pełni kompatybilne z PlotCanvas1D,
        wzbogacone o interaktywne menu kontekstowe (prawy przycisk myszy).
        """
        # Inicjalizacja klasy bazowej PlotCanvas1D
        super().__init__(master, is_log_y=is_log_y, **kwargs)
        self.vm = viewmodel

        # 🖱️ Bindowanie prawego przycisku myszy na płótnie Tkinter Matplotlib
        self.canvas.get_tk_widget().bind("<Button-3>", self._show_context_menu)

        
        # Tworzymy menu kontekstowe
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#2b73b5")
        self.context_menu.add_command(label="🔍 Ustaw zakresy osi (Limits)...", command=self._popup_axis_limits)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📈 Skala Y: Liniowa", command=lambda: self._set_y_scale('linear'))
        self.context_menu.add_command(label="📊 Skala Y: Logarytmiczna (log10)", command=lambda: self._set_y_scale('log'))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="↺ Resetuj widok (Autoscale)", command=self._reset_view)

        self.smooth_menu = tk.Menu(self.context_menu, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#2b73b5")
        self.smooth_menu.add_radiobutton(label="Brak (Surowy sygnał)", command=lambda: self._set_smoothing(SmoothingMode.NONE))
        self.smooth_menu.add_radiobutton(label="Savitzky-Golay", command=lambda: self._set_smoothing(SmoothingMode.SAVGOL))
        self.smooth_menu.add_radiobutton(label="Gauss", command=lambda: self._set_smoothing(SmoothingMode.GAUSSIAN))

        self.context_menu.add_cascade(label="🧹 Wygładzanie (Smoothing)", menu=self.smooth_menu)
        self.context_menu.add_separator()

        
    def _show_context_menu(self, event):
        """Wyświetla menu kontekstowe w miejscu kliknięcia kursora."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _set_y_scale(self, scale_type: str):
        """Zmienia skalę osi Y (linear / log) i flaga logarytmiczna."""
        self.is_log_y = (scale_type == 'log')
        self.ax.set_yscale(scale_type)
        self.canvas.draw_idle()

    def _reset_view(self):
        """Resetuje zakresy osi (Autoskalowanie)."""
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def _popup_axis_limits(self):
        """Otwiera okno dialogowe do ręcznego wpisania limitów osi."""
        dialog = AxisLimitsDialog(self, current_xlim=self.ax.get_xlim(), current_ylim=self.ax.get_ylim())
        self.wait_window(dialog)  # Czekamy na zamknięcie okna
        if dialog.result:
            xlim, ylim = dialog.result
            if xlim: 
                self.ax.set_xlim(xlim)
            if ylim: 
                self.ax.set_ylim(ylim)
            self.canvas.draw_idle()

    def _set_smoothing(self, mode: SmoothingMode):
        """GUI jedynie przekazuje intencję użytkownika do ViewModelu."""
        self.vm.set_spectrum_smoothing(mode)

class AxisLimitsDialog(ctk.CTkToplevel):
    def __init__(self, master, current_xlim, current_ylim):
        super().__init__(master)
        self.title("Zakresy osi")
        self.geometry("280x220")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        # Pola E_min, E_max, dN/dE_min, dN/dE_max z wpisanymi obecnymi granicami
        self.entry_xmin = self._add_row("E min:", f"{current_xlim[0]:.3f}")
        self.entry_xmax = self._add_row("E max:", f"{current_xlim[1]:.3f}")
        self.entry_ymin = self._add_row("dN/dE min:", f"{current_ylim[0]:.2e}")
        self.entry_ymax = self._add_row("dN/dE max:", f"{current_ylim[1]:.2e}")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=15)

        btn_apply = ctk.CTkButton(btn_frame, text="Zastosuj", command=self._apply, fg_color="#2b73b5", hover_color="#225c91")
        btn_apply.pack(side="right", padx=2)

        btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=self.destroy, fg_color="#444444", hover_color="#555555", width=70)
        btn_cancel.pack(side="right", padx=2)

    def _add_row(self, label, val):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=3)
        ctk.CTkLabel(f, text=label, width=90, anchor="w").pack(side="left")
        e = ctk.CTkEntry(f, height=26)
        e.insert(0, val)
        e.pack(side="right", fill="x", expand=True)
        return e

    def _apply(self):
        try:
            xlim = (float(self.entry_xmin.get()), float(self.entry_xmax.get()))
            ylim = (float(self.entry_ymin.get()), float(self.entry_ymax.get()))
            self.result = (xlim, ylim)
        except ValueError:
            pass
        self.destroy()