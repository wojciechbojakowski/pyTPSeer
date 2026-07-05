# gui/main_window.py

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class MainWindow_legency(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Legency look")
        self.geometry("1400://850")

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.col1_frame = ctk.CTkFrame(self)
        self.col1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.plot_frame1 = ctk.CTkFrame(self.col1_frame)
        self.plot_frame1.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_frame1)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True)

        self.next_prev_box = ctk.CTkFrame(self.col1_frame)
        self.next_prev_box.pack(fill="x", padx=10, pady=5)

        self.btn_load = ctk.CTkButton(self.next_prev_box, text="Wczytaj", width=80, command=self.load_image)
        self.btn_load.pack(side="left", padx=5, pady=5)
        
        self.btn_draw = ctk.CTkButton(self.next_prev_box, text="Rysuj", width=80, command=self.draw_image)
        self.btn_draw.pack(side="left", padx=5, pady=5)

        self.lbl_rot = ctk.CTkLabel(self.next_prev_box, text="Kąt skręcenia [°]:")
        self.lbl_rot.pack(side="left", padx=5, pady=5)
        
        self.rotation_line = ctk.CTkEntry(self.next_prev_box, width=60)
        self.rotation_line.pack(side="left", padx=5, pady=5)

        self.btn_prev = ctk.CTkButton(self.next_prev_box, text="Poprzedni", width=90, command=self.prev_image)
        self.btn_prev.pack(side="left", padx=5, pady=5)
        
        self.btn_next = ctk.CTkButton(self.next_prev_box, text="Następny", width=90, command=self.next_image)
        self.btn_next.pack(side="left", padx=5, pady=5)
        
        self.btn_save_mcp = ctk.CTkButton(self.next_prev_box, text="Zapisz", width=80, command=self.save_mcp)
        self.btn_save_mcp.pack(side="left", padx=5, pady=5)

        self.slider_box = ctk.CTkFrame(self.col1_frame)
        self.slider_box.pack(fill="x", padx=10, pady=5)

        self.lbl_px_mm = ctk.CTkLabel(self.slider_box, text="Ilość pikseli / mm:")
        self.lbl_px_mm.pack(side="left", padx=5, pady=5)
        
        self.pixels_per_mm_line = ctk.CTkEntry(self.slider_box, placeholder_text="px/mm", width=80)
        self.pixels_per_mm_line.pack(side="left", padx=5, pady=5)

        self.lbl_cutoff = ctk.CTkLabel(self.slider_box, text="Ustaw odcięcie tła:")
        self.lbl_cutoff.pack(side="left", padx=5, pady=5)
        
        self.cutoff_slider = ctk.CTkSlider(self.slider_box, from_=0, to=50, command=self.cutoff_setup)
        self.cutoff_slider.set(2)
        self.cutoff_slider.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        self.cutoff_slider.bind("<ButtonRelease-1>", lambda event: self.cutoff_released())

        self.cutoff_field_line = ctk.CTkEntry(self.slider_box, width=60)
        self.cutoff_field_line.insert(0, "0.02")
        self.cutoff_field_line.pack(side="left", padx=5, pady=5)

        self.current_file_name_line = ctk.CTkEntry(self.col1_frame, placeholder_text="Nazwa wczytanego obrazu")
        self.current_file_name_line.pack(fill="x", padx=10, pady=5)


        self.col2_frame = ctk.CTkFrame(self)
        self.col2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.tps_setting_box = ctk.CTkFrame(self.col2_frame)
        self.tps_setting_box.pack(fill="x", padx=10, pady=5)

        self.btn_tps_settings = ctk.CTkButton(self.tps_setting_box, text="Parametry TPS", command=self.tps_setting_show)
        self.btn_tps_settings.pack(fill="x", padx=5, pady=2)

        self.btn_set_zero = ctk.CTkButton(self.tps_setting_box, text="Ustaw początek układu współrzędnych", command=self.set_zero)
        self.btn_set_zero.pack(fill="x", padx=5, pady=2)

        self.btn_new_parabola = ctk.CTkButton(self.tps_setting_box, text="Dodaj nową parabolę", command=self.add_parabola)
        self.btn_new_parabola.pack(fill="x", padx=5, pady=2)

        self.btn_del_parabola = ctk.CTkButton(self.tps_setting_box, text="Usuń ostatnią parabolę", command=self.delete_last_parabola)
        self.btn_del_parabola.pack(fill="x", padx=5, pady=2)

        self.chk_tof_combined = ctk.CTkCheckBox(self.tps_setting_box, text="Pokaż symulację TOF z detektora", command=self.show_tof_combined)
        self.chk_tof_combined.pack(anchor="w", padx=10, pady=5)

        # --- Tytuł Histogramu ---
        self.lbl_histo_title = ctk.CTkLabel(self.col2_frame, text="Podaj tytuł histogramu:")
        self.lbl_histo_title.pack(anchor="w", padx=10, pady=2)
        
        self.histogram_title_line = ctk.CTkEntry(self.col2_frame, placeholder_text="Tytuł...")
        self.histogram_title_line.pack(fill="x", padx=10, pady=2)
        self.histogram_title_line.bind("<Return>", lambda event: self.histo_title_changed())

        # --- Wykres nr 2 (Drugi QRootCanvas) ---
        self.plot_frame2 = ctk.CTkFrame(self.col2_frame)
        self.plot_frame2.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.fig2, self.ax2 = plt.subplots(figsize=(5, 2), dpi=100)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_frame2)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)

        # --- Menu zapisu/wczytywania histogramów ---
        self.histo_menu_box = ctk.CTkFrame(self.col2_frame)
        self.histo_menu_box.pack(fill="x", padx=10, pady=5)

        self.chk_keep_histo = ctk.CTkCheckBox(self.histo_menu_box, text="Zachowaj aktualny histogram")
        self.chk_keep_histo.pack(anchor="w", padx=10, pady=2)

        self.chk_save_root = ctk.CTkCheckBox(self.histo_menu_box, text="Zapisz pliki .ROOT")
        self.chk_save_root.pack(anchor="w", padx=10, pady=2)

        self.btn_save_histo = ctk.CTkButton(self.histo_menu_box, text="Zapisz histogram", command=self.save_histo)
        self.btn_save_histo.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.btn_load_histo = ctk.CTkButton(self.histo_menu_box, text="Wczytaj histogram", command=self.load_saved_histo)
        self.btn_load_histo.pack(side="right", fill="x", expand=True, padx=5, pady=5)

        # --- Wykres nr 3 (Trzeci QRootCanvas na dane TOF) ---
        self.plot_frame3 = ctk.CTkFrame(self.col2_frame)
        self.plot_frame3.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.fig3, self.ax3 = plt.subplots(figsize=(5, 2), dpi=100)
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self.plot_frame3)
        self.canvas3.get_tk_widget().pack(fill="both", expand=True)

        self.chk_keep_tof = ctk.CTkCheckBox(self.col2_frame, text="Nie zeruj wykresu")
        self.chk_keep_tof.pack(anchor="w", padx=10, pady=2)

        self.btn_save_tof = ctk.CTkButton(self.col2_frame, text="Zapisz obraz sygnału TOF", command=self.save_tof)
        self.btn_save_tof.pack(fill="x", padx=10, pady=5)

        # --- REPLICATE QTimer (Odświeżanie procesów w tle, np. ROOT, co 100ms) ---
        self.after(100, self.handle_root_events)

    # =========================================================================
    # SLOTY / METODY (Miejsca na implementację Twojej logiki naukowej)
    # =========================================================================
    def load_image(self): print("Wczytaj obraz...")
    def draw_image(self): print("Rysuj obraz...")
    def tps_setting_show(self): print("Pokaż okno parametrów TPS...")
    def add_parabola(self): print("Dodaj parabolę...")
    def set_zero(self): print("Ustawianie punktu zero...")
    def histo_title_changed(self): print(f"Zmieniono tytuł: {self.histogram_title_line.get()}")
    def rotation_changed(self): print("Zmieniono rotację...")
    def save_histo(self): print("Zapisywanie histogramu...")
    def save_tof(self): print("Zapisywanie TOF...")
    def save_mcp(self): print("Zapisywanie obrazu MCP...")
    def delete_last_parabola(self): print("Usuwanie ostatniej paraboli...")
    
    def cutoff_setup(self, value):
        # Aktualizuje pole tekstowe podczas przesuwania suwaka
        self.cutoff_field_line.delete(0, "end")
        self.cutoff_field_line.insert(0, f"{float(value)/100:.2f}")

    def cutoff_released(self): print("Puszczono suwak, przeliczam tło...")
    def next_image(self): print("Następny obraz...")
    def prev_image(self): print("Poprzedni obraz...")
    def show_tof_combined(self): print("Przełączono widok TOF...")
    def load_saved_histo(self): print("Wczytywanie zapisanego histogramu...")
    
    def handle_root_events(self):
        # To jest odpowiednik QTimer z C++. Wykonuje się co 100ms w tle bez zamrażania GUI.
        # Tutaj możesz wrzucić sprawdzanie procesów.
        self.after(100, self.handle_root_events) # Ponowne zakolejkowanie