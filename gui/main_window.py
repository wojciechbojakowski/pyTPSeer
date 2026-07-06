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
        self.rotation_deg = 0.3 #TODO: Add GUI element to change rotation angle

        #Config of layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #Init GUI components
        #Sidebar
        self.sidebar = SidebarFrame(master=self, controller=self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        #Plot canvas
        self.plot_frame = PlotCanvas(master=self)
        self.plot_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

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
            self.sidebar.reset_ui_labels()
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

    def draw_parabola(self):
        x, y, Ep = analysis.draw_parabole(
            controller=self,
            A=1,#TODO: Add GUI element to change A
            Q=1,#TODO: Add GUI element to change Q
            E_max=1.67,
            E_min=0.57,
            sampling_mode="Quadratic"
        )

        self.plot_frame.ax.plot(x, y, 'r-', linewidth=1.5, label='Parabola')
        self.plot_frame.canvas.draw()
