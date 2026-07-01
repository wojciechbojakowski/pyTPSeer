import customtkinter as ctk
import config
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class PlotCanvas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.fig, self.ax = plt.subplots(figsize=(5, 5), dpi=config.DPI)
        self.cbar = None
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(side="bottom", fill="x", expand=False)

        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
    def draw_image(self, img_norm, extent_sizes, start_point=None):
        old_xlim = self.ax.get_xlim()
        old_ylim = self.ax.get_ylim()
        
        first_time = (old_xlim == (0.0, 1.0) and old_ylim == (0.0, 1.0))

        self.ax.clear()
        im = self.ax.imshow(img_norm, cmap='jet', extent=extent_sizes)
        self.ax.axis('on')

        if self.cbar is None:
            self.cbar = self.fig.colorbar(im, ax=self.ax, label='Intensity')
        else:
            self.cbar.update_normal(im)

        if not first_time:
            self.ax.set_xlim(old_xlim)
            self.ax.set_ylim(old_ylim)
        
        if start_point:
            sx, sy = start_point
            self.ax.plot(sx, sy, 'x', markersize=5, markeredgewidth=2, color='purple')
            
        self.canvas.draw()