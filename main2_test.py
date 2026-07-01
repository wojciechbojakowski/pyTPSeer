import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import customtkinter as ctk
from tkinter import filedialog

# Ustawienia stylu aplikacji
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class TpsAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Analizator Obrazów TPS")
        self.geometry("1100x700")

        # Zmienne przechowujące dane obrazu
        self.img_norm = None
        self.cid = None  # Identyfikator połączenia kliknięć myszy

        self.start_point = None  # Przechowa krotkę (x, y)
        self.is_selecting_start = False  # Flaga trybu wyboru

        # --- Podział okna (Grid) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= PANEL BOCZNY (Sterowanie) =================
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.title_label = ctk.CTkLabel(self.sidebar, text="Panel Sterowania", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(padx=20, pady=20)

        self.btn_open = ctk.CTkButton(self.sidebar, text="Otwórz plik .tif", command=self.open_file_dialog)
        self.btn_open.pack(padx=20, pady=10, fill="x")

        self.btn_set_start = ctk.CTkButton(
            self.sidebar, 
            text="Zaznacz punkt początkowy", 
            fg_color="#2b9348",  # Zielony kolor wyróżniający działanie
            hover_color="#1b5e20",
            command=self.activate_start_selection
        )
        self.btn_set_start.pack(padx=20, pady=15, fill="x")

        # Kontenery na wyniki odczytu punktu
        self.result_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.result_frame.pack(padx=20, pady=30, fill="x")

        self.lbl_info = ctk.CTkLabel(self.result_frame, text="Kliknij na wykres, aby zbadać punkt", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_info.pack(pady=5)

        self.lbl_coords = ctk.CTkLabel(self.result_frame, text="X: --- , Y: ---", font=ctk.CTkFont(size=14))
        self.lbl_coords.pack(pady=5)

        self.lbl_value = ctk.CTkLabel(self.result_frame, text="Wartość: ---", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_value.pack(pady=5)

        # Ścieżka pliku na dole
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Brak załadowanego pliku", font=ctk.CTkFont(size=10), wraplength=240)
        self.lbl_status.pack(side="bottom", padx=20, pady=20)

        # ================= PANEL GŁÓWNY (Matplotlib) =================
        self.plot_frame = ctk.CTkFrame(self, corner_radius=10)
        self.plot_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Tworzenie obiektów Matplotlib (DPI=100 dla wydajności na słabszym sprzęcie)
        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.ax.axis('off')  # Domyślnie wyłączone osie
        self.fig.tight_layout()

        # Osadzenie wykresu w Tkinterze
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Dodanie paska narzędzi (Zoom, Przesuwanie, Zapis)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas_widget.pack(fill="both", expand=True)

        # Automatyczne próba załadowania Twojego pliku na start (jeśli istnieje)
        self.load_image_backend('../../dane/20240206-175820-60740-[Phosphor].tif')

    def load_image_backend(self, path):
        """Logika wczytywania i normalizacji obrazu"""
        try:
            img_bgr = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img_bgr is None:
                raise FileNotFoundError
            
            self.img_norm = img_bgr / 255.0
            self.lbl_status.configure(text=f"Plik: {path.split('/')[-1]}")
            self.display_image()
        except Exception:
            self.lbl_status.configure(text="Nie znaleziono pliku startowego. Wybierz plik ręcznie.")

    def display_image(self):
        """Wizualizacja obrazu na wykresie Matplotlib"""
        if self.img_norm is None:
            return

        self.ax.clear()
        
        # Tworzenie mapy ciepła 'jet'
        im = self.ax.imshow(self.img_norm, cmap='jet')
        self.ax.axis('off')

        # Usuwamy stary pasek boczny (colorbar), jeśli istniał, żeby nie rysować jednego na drugim
        if hasattr(self, 'cbar'):
            self.cbar.remove()
        self.cbar = self.fig.colorbar(im, ax=self.ax, label='Znormalizowana wartość pikseli')
        
        self.fig.tight_layout()
        self.canvas.draw()

        if self.start_point:
            sx, sy = self.start_point
            self.ax.plot(sx, sy, 'rx', markersize=10, markeredgewidth=2, label="Początek") # Czerwony krzyżyk X

        # Rejestracja zdarzenia kliknięcia myszką na wykresie
        if self.cid:
            self.fig.canvas.mpl_disconnect(self.cid)  # Rozłączenie starego eventu
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Obsługa kliknięcia na wykresie"""
        # Sprawdzamy czy kliknięcie nastąpiło wewnątrz obszaru wykresu i czy obraz jest załadowany
        if event.xdata is not None and event.ydata is not None and self.img_norm is not None:
            # Pobieramy współrzędne jako liczby całkowite (piksele)
            x, y = int(event.xdata), int(event.ydata)
            
            # Bezpiecznik przed kliknięciem na samej krawędzi (poza zakresem macierzy)
            h, w = self.img_norm.shape
            if 0 <= x < w and 0 <= y < h:
                # Odczyt wartości z macierzy [y, x]
                wartosc = self.img_norm[y, x]
                if self.is_selecting_start:
                    self.start_point = (x, y)
                    self.lbl_start_coords.configure(text=f"X: {x}, Y: {y} (Wartość: {wartosc:.4f})")
                    
                    self.is_selecting_start = False
                    self.btn_set_start.configure(text="Zaznacz punkt początkowy", fg_color="#2b9348", hover_color="#1b5e20")
                    
                    # Odświeżenie obrazu z nowym krzyżykiem
                    self.display_image()
                else:
                    # Aktualizacja etykiet tekstowych w GUI
                    self.lbl_coords.configure(text=f"X: {x} , Y: {y}")
                    self.lbl_value.configure(text=f"Wartość: {wartosc:.4f}")

                    # Opcjonalnie: rysowanie małego krzyżyka w miejscu kliknięcia
                    self.display_image() # Reset obrazu
                    self.ax.plot(x, y, 'ko', markersize=5) # 'ko' to czarna kropka w miejscu kliknięcia
                    self.canvas.draw()

    def open_file_dialog(self):
        """Okno dialogowe wyboru pliku dla użytkownika"""
        file_path = filedialog.askopenfilename(
            title="Wybierz obraz TPS (.tif)",
            filetypes=[("Pliki TIF", "*.tif *.tiff"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.load_image_backend(file_path)
    
    def activate_start_selection(self):
        """Uruchamiane po kliknięciu przycisku. Zmienia tryb aplikacji."""
        if self.img_norm is None:
            self.lbl_status.configure(text="Najpierw załaduj plik obrazu!")
            return
        
        self.is_selecting_start = True
        self.btn_set_start.configure(text="KLIKNIJ NA WYKRESIE...", fg_color="#d90429") # Zmiana koloru na czerwony (alert)

if __name__ == "__main__":
    app = TpsAnalyzerApp()
    app.mainloop()