import customtkinter as ctk
from tkinter import filedialog
import matplotlib.pyplot as plt

#IMPORT GUI COMPONENTS
from gui.sidebar import SidebarFrame
from gui.plot_canvas import PlotCanvas

#IMPORT CORE MODULES
import core.image_loader as loader
import core.analysis as analysis
import config
import core.spectrum_extractor as extractor

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(config.NAME)
        self.geometry(config.WINDOW_SIZE)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        #State variables
        self.img_norm = None
        self.start_point = None
        self.is_selecting_start = False
        self.tps_params = {}
        self.rotation_deg = 0.3
        #Parabola state 
        self.parabolas_list = []
        self.color_palette = ['#ff0054', '#390099', '#ffbd00', '#00b4d8', '#70e000', '#ff7000']

        #Config of layout
        self.grid_columnconfigure(1, weight=1, uniform="plots")
        self.grid_columnconfigure(2, weight=1, uniform="plots")
        self.grid_rowconfigure(0, weight=1)

        #Init GUI components
        #Sidebar
        self.sidebar = SidebarFrame(master=self, controller=self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        #Plot canvas
        self.plot_frame = PlotCanvas(master=self)
        self.plot_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.spectrum_frame = PlotCanvas(master=self)
        self.spectrum_frame.grid(row=0, column=2, padx=(10, 20), pady=20, sticky="nsew")

        self.spectrum_frame.ax.set_title("Widmo energii jonów")
        self.spectrum_frame.ax.set_xlabel("Energia [MeV/u]")
        self.spectrum_frame.ax.set_ylabel("dN/dE [MeV$^{-1}$ sr$^{-1}$]")
        self.spectrum_frame.ax.grid(True, which="both", linestyle="--", alpha=0.5)

        #Mouse click event
        self.plot_frame.fig.canvas.mpl_connect('button_press_event', self.on_plot_click)

        #Default image load (for testing purposes)
        self.load_image('../../dane/20240206-175820-60740-[Phosphor].tif')

    def load_image(self, path):
        """Load image"""
        img = loader.load_grayscale_tif(path)
        if img is not None:
            self.img_norm = img
            self.start_point = None
            self.sidebar.set_status(f"Plik: {path.split('/')[-1]}")
            self.refresh_interface()
        else:
            self.sidebar.set_status("Failed to load image. Please check the file path or format.")

    def open_file_dialog(self):
        """Open a file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select file (.tif)",
            filetypes=[("File TIF", "*.tif *.tiff"), ("All files", "*.*")]
        )
        if file_path:
            self.load_image(file_path)

    def trigger_start_point_selection(self):
        """Trigger the process of selecting a start point on the image"""
        if self.img_norm is None:
            self.sidebar.set_status("Fist load an image")
            return
        self.is_selecting_start = True

    def refresh_interface(self, current_pt_m=None):#TODO Change in future that size will be calculated in core
        """Refrash an image"""
        if self.img_norm is None:
            return

        h, w = self.img_norm.shape
        szerokosc_m = w * config.PX_TO_METER
        wysokosc_m = h * config.PX_TO_METER
        extent_sizes = [0, szerokosc_m, 0, wysokosc_m]

        self.plot_frame.draw_image(
            img_norm=self.img_norm, 
            extent_sizes=extent_sizes, 
            start_point=self.start_point
        )
        self.spectrum_frame.ax.clear()

        self.spectrum_frame.ax.set_title("Widmo różniczkowe energii jonów")
        self.spectrum_frame.ax.set_xlabel("Energia [MeV/u]")
        self.spectrum_frame.ax.set_ylabel("dN/dE [MeV$^{-1}$ sr$^{-1}$]")
        self.spectrum_frame.ax.grid(True, which="both", linestyle="--", alpha=0.3)
        self.spectrum_frame.ax.set_yscale("log")

        for idx, p_config in enumerate(self.parabolas_list):
            x, y, E_arr = analysis.draw_parabole(
                controller=self,
                A=p_config["A"],
                Q=p_config["Q"],
                E_max=p_config["E_max"],
                E_min=p_config["E_min"],
                sampling_mode="Quadratic"
            )
            
            color = self.color_palette[idx % len(self.color_palette)]
            
            self.plot_frame.ax.plot(x, y, '-', color=color, linewidth=1.5, label=p_config["name"])

            try:
                # Wybieramy domyślną metodę ("FlatBox", "Gaussian" lub "PinholeBackground")
                # Możesz potem połączyć to z wartością wybraną w boksie w GUI
                scan_method = "FlatBox" 
                
                energies, dnde = extractor.extract_tps_spectrum(
                    controller=self, 
                    x_m=x, 
                    y_m=y, 
                    E_arr=E_arr, 
                    parabola_config=p_config,
                    method=scan_method
                )
                
                # Jeśli silnik zwrócił poprawne punkty, nanosimy je na drugi wykres
                if len(energies) > 0:
                    self.spectrum_frame.ax.plot(
                        energies, dnde, '.-', 
                        color=color, linewidth=1.5, markersize=3,
                        label=f"{p_config['name']} ({scan_method})"
                    )

            except Exception as e:
                # Bezpiecznik, jeśli np. brak zmiennych kalibracyjnych w tps_params
                print(f"Błąd ekstrakcji spektrum dla {p_config['name']}: {e}")

        # 3. Blokada osi i odświeżenie canvasu (jeśli są narysowane linie)
        if self.parabolas_list:
            self.plot_frame.ax.set_xlim(0, szerokosc_m)
            self.plot_frame.ax.set_ylim(0, wysokosc_m)
            
            self.plot_frame.ax.legend(loc="upper right", fontsize=8)

        self.plot_frame.canvas.draw()
        self.spectrum_frame.canvas.draw()

    def on_plot_click(self, event):
        """Handle mouse click events on the plot canvas"""
        if event.xdata is None or event.ydata is None or self.img_norm is None:
            return

        x_m, y_m = event.xdata, event.ydata
        
        wartosc, px_x, px_y = analysis.get_pixel_value(self.img_norm, x_m, y_m)

        if wartosc is not None:
            if self.is_selecting_start:
                self.start_point = (x_m, y_m)
                self.sidebar.update_start_point_labels(x_m, y_m, wartosc)
                self.is_selecting_start = False
                self.sidebar.restore_start_button_state()
                self.refresh_interface()
            else:
                self.sidebar.update_current_point_labels(x_m, y_m, wartosc)
                self.refresh_interface(current_pt_m=(x_m, y_m))

    def on_closing(self):
        """Safe closing"""
        self.img_norm = None 
        
        for after_id in self.tk.eval('after info').split():
            self.after_cancel(after_id)
            
        plt.close('all')
        
        self.destroy()

    def update_tps_parameters(self, updated_dict):
        """Update TPS parameters"""
        self.tps_params = updated_dict
        print("Zaktualizowano parametry TPS w rdzeniu:", self.tps_params)
        self.sidebar.set_status("Zapisano 11 parametrów TPS.")

        # core.analysis.recalculate_trajectories(self.tps_params)

    def update_rotation_angle(self, new_angle):
        """Aktualizuje kąt i natychmiast przerysowuje cały interfejs wraz z parabolą"""
        self.rotation_deg = float(new_angle)
        
        self.refresh_interface()
        
    def draw_parabola(self):
        if self.start_point is None:
            return

        x, y, Ep = analysis.draw_parabole(
            controller=self,
            A=12,#TODO: Add GUI element to change A
            Q=6,#TODO: Add GUI element to change Q
            E_max=5,
            E_min=0.57,
            sampling_mode="Quadratic"
        )

        self.plot_frame.ax.plot(x, y, 'm-', linewidth=1, label='Parabola')

        self.plot_frame.canvas.draw()

    
    def add_new_parabola(self, parabola_config):
        """Dodaje nową konfigurację jona do listy i wyrysowuje ją na ekranie"""
        self.parabolas_list.append(parabola_config)
        self.sidebar.set_status(f"Dodano jona: {parabola_config['name']}")
        
        self.refresh_interface()
