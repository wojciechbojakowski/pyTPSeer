# views/plot_canvas.py
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

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

    def draw_detector_frame(self, img_matrix, extent_sizes: list, start_point=None, cmap="inferno"):
        """Czyści tło i nanosi surowy obraz z detektora wraz ze skalą intensywności."""
        self.ax.clear()
        self._apply_dark_theme_styles()
        
        # Bezpieczne odświeżanie Colorbaru
        if self.cbar is not None:
            try:
                self.cbar.remove()
            except Exception:
                pass
            self.cbar = None

        im = self.ax.imshow(img_matrix, cmap=cmap, extent=extent_sizes, aspect='equal')
        self.ax.set_title("Kadr detektora MCP")
        self.ax.set_xlabel("Pozycja X [m]")
        self.ax.set_ylabel("Pozycja Y [m]")
        
        # Dodanie legendy barwnej
        self.cbar = self.fig.colorbar(im, ax=self.ax, fraction=0.046, pad=0.04)
        self.cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
        self.cbar.ax.set_ylabel("Jasność / Sygnał [a.u.]", color='white', labelpad=10)
        self.cbar.outline.set_edgecolor('#444444')
        
        # Rysowanie celownika punktu zero
        if start_point is not None:
            x_zero, y_zero = start_point
            self.ax.plot(x_zero, y_zero, 'rx', markersize=12, markeredgewidth=2, label="Pinhole")

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