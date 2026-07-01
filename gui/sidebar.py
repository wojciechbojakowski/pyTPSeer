# gui/sidebar.py

import customtkinter as ctk

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

        self.sep = ctk.CTkLabel(self.result_frame, text="-----------------------------------", text_color="gray")
        self.sep.pack(pady=5)

        self.lbl_info = ctk.CTkLabel(
            self.result_frame, 
            text="[ (TEST function) current point ]", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_info.pack(pady=2)
        
        self.lbl_coords = ctk.CTkLabel(
            self.result_frame, 
            text="X: --- , Y: ---", 
            font=ctk.CTkFont(size=14)
        )
        self.lbl_coords.pack(pady=2)
        
        self.lbl_value = ctk.CTkLabel(
            self.result_frame, 
            text="Value: ---", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_value.pack(pady=2)

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
        self.lbl_coords.configure(text=f"X: {x_m:.5f} m\nY: {y_m:.5f} m")
        self.lbl_value.configure(text=f"Value: {value:.4f}")

    def reset_ui_labels(self):
        """Restores the initial state of the labels (e.g., after loading a new TIF file)"""
        self.lbl_start_coords.configure(text="X: --- , Y: --- (Value: ---)")
        self.lbl_coords.configure(text="X: --- , Y: ---")
        self.lbl_value.configure(text="Value: ---")

    def set_status(self, text):
        """Sets the informational text at the bottom of the sidebar"""
        self.lbl_status.configure(text=text)