# gui/sidebar.py

import customtkinter as ctk
from gui.tps_params_window import TpsParamsWindow
from gui.add_parabola_window import AddParabolaWindow

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        #def of size of sidebar
        super().__init__(master, width=280, corner_radius=0, **kwargs)
        
        #pointer to main window
        self.controller = controller

        self.title_label = ctk.CTkLabel(
            self, 
            text="lorem ipum", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(padx=20, pady=20)

        self.btn_open = ctk.CTkButton(
            self, 
            text="Open file .tif", 
            command=self.controller.open_file_dialog
        )
        self.btn_open.pack(padx=20, pady=10, fill="x")

        self.btn_set_start = ctk.CTkButton(
            self, 
            text="Select start point", 
            fg_color="#2b9348",
            hover_color="#1b5e20",
            command=self.handle_start_button_click
        )
        self.btn_set_start.pack(padx=20, pady=15, fill="x")
        self.btn_tps_settings = ctk.CTkButton(self, text="Parametry TPS", command=self.tps_setting_show)

        self.btn_tps_settings.pack(padx=20, pady=15, fill="x")

        self.btn_add_parabola = ctk.CTkButton(
            self, 
            text="➕ Dodaj parabolę", 
            fg_color="#0077b6", 
            hover_color="#0096c7",
            command=self._open_add_parabola_dialog
        )
        self.btn_add_parabola.pack(fill="x", padx=10, pady=10)

        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(padx=20, pady=20, fill="x")

        
        self.lbl_start_title = ctk.CTkLabel(
            self.result_frame, 
            text="[ Start point ]", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_start_title.pack(pady=2)
        
        self.lbl_start_coords = ctk.CTkLabel(
            self.result_frame, 
            text="X: --- , Y: --- (Value: ---)", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_start_coords.pack(pady=2)

        # --- SEKCJA OBROTU PARABOLI ---
        self.rot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rot_frame.pack(fill="x", padx=10, pady=10)

        self.rot_label = ctk.CTkLabel(self.rot_frame, text="Obrót układu [°]:", font=ctk.CTkFont(weight="bold"))
        self.rot_label.pack(anchor="w")

        # Kontenery na Input i Slider obok siebie
        self.rot_input_frame = ctk.CTkFrame(self.rot_frame, fg_color="transparent")
        self.rot_input_frame.pack(fill="x", pady=2)

        # Pole tekstowe do wpisania dokładnej wartości (np. -0.35)
        self.rot_entry = ctk.CTkEntry(self.rot_input_frame, width=70, height=25)
        self.rot_entry.insert(0, str(self.controller.rotation_deg))
        self.rot_entry.pack(side="left", padx=(0, 5))
        # Reakcja na kliknięcie Enter w polu tekstowym
        self.rot_entry.bind("<Return>", self._on_rot_entry_change)

        # Suwak do płynnego, szybkiego obracania myszką (od -15 do +15 stopni)
        self.rot_slider = ctk.CTkSlider(
            self.rot_input_frame, 
            from_=-15.0, 
            to=15.0, 
            number_of_steps=3000, # bardzo wysoka precyzja skoku suwaka
            command=self._on_rot_slider_move
        )
        self.rot_slider.set(self.controller.rotation_deg)
        self.rot_slider.pack(side="right", fill="x", expand=True)
        
        self.lbl_status = ctk.CTkLabel(
            self, 
            text="No file loaded", 
            font=ctk.CTkFont(size=10), 
            wraplength=240
        )
        self.lbl_status.pack(side="bottom", padx=20, pady=20)


    def handle_start_button_click(self):
        """Handle the click event for the "Select start point" button"""
        self.btn_set_start.configure(text="CLICK ON THE PLOT...", fg_color="#d90429")
        self.controller.trigger_start_point_selection()

    def restore_start_button_state(self):
        """Restores the original appearance of the start point button after a successful click"""
        self.btn_set_start.configure(text="Select start point", fg_color="#2b9348", hover_color="#1b5e20")

    def update_start_point_labels(self, x_m, y_m, value):
        """Updates the labels for the saved reference point"""
        self.lbl_start_coords.configure(text=f"X: {x_m:.5f}m, Y: {y_m:.5f}m\n(Value: {value:.4f})")

    def update_current_point_labels(self, x_m, y_m, value):
        """Updates the labels for the newly clicked point"""
        #self.lbl_coords.configure(text=f"X: {x_m:.5f} m\nY: {y_m:.5f} m")
        #self.lbl_value.configure(text=f"Value: {value:.4f}")

    def set_status(self, text):
        """Sets the informational text at the bottom of the sidebar"""
        self.lbl_status.configure(text=text)

    def tps_setting_show(self):
        """Otwiera wyskakujące okienko z 11 parametrami TPS"""
        TpsParamsWindow(master=self, controller=self.controller)
    
    def _on_rot_slider_move(self, value):
        """Wywoływane podczas przesuwania suwaka myszką"""
        # Aktualizacja tekstu w entry (zaokrąglone do 2 miejsc po przecinku)
        self.rot_entry.delete(0, "end")
        self.rot_entry.insert(0, f"{value:.2f}")
        # Przekazanie wartości do MainWindow i natychmiastowe przerysowanie
        self.controller.update_rotation_angle(value)

    def _on_rot_entry_change(self, event):
        """Wywoływane po wpisaniu wartości z klawiatury i wciśnięciu Enter"""
        try:
            val = float(self.rot_entry.get())
            if -15.0 <= val <= 15.0:
                self.rot_slider.set(val)
            self.controller.update_rotation_angle(val)
        except ValueError:
            self.rot_entry.configure(border_color="red")
    
    def _open_add_parabola_dialog(self):
        """Otwiera popup dodawania nowej krzywej jonowej"""
        if self.controller.start_point is None:
            self.set_status("Najpierw zaznacz punkt zero (start point)!")
            return
        AddParabolaWindow(master=self.controller, controller=self.controller)