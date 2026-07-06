# gui/tps_params_window.py

import customtkinter as ctk

class TpsParamsWindow(ctk.CTkToplevel):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        
        self.controller = controller
        self.title("Parametry wejściowe spektrometru TPS")
        self.geometry("650x450")
        
        self.lift()
        self.focus_set()
        self.grab_set()
        
        self.grid_columnconfigure((0, 1), weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        self.lbl_sec1 = ctk.CTkLabel(self.left_frame, text="Pola i Cząstka", font=ctk.CTkFont(weight="bold"))
        self.lbl_sec1.pack(anchor="w", pady=(0, 10))

        self.entries = {}
        
        self.param_specs = {
            "B_field": (" B [T]", "0.2"),
            "E_field": (" E [V", "2.6e+03"),
            "Zm1": (" Zm1 ", "0.0205"),
            "Zm2": (" Zm2 ", "0.0985"),
            "Ze1": (" Ze1 ", "0.106"),
            "Ze2": ("Ze2", "0.189"),
            "d1": ("d1", "0.0021"),
            "d2": ("d2", "0.012"),
            "Zd": ("Zd", "0.269"),
            "pin_d": ("pinhole diameter[mm]", "0.157"),
            "pin_target": ("pinhole-target[m]", "1.0")
        }

        left_keys = list(self.param_specs.keys())[:6]
        for key in left_keys:
            label_text, default_val = self.param_specs[key]
            self.create_input_field(self.left_frame, key, label_text, default_val)

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        self.lbl_sec2 = ctk.CTkLabel(self.right_frame, text="Geometria układu", font=ctk.CTkFont(weight="bold"))
        self.lbl_sec2.pack(anchor="w", pady=(0, 10))

        right_keys = list(self.param_specs.keys())[6:]
        for key in right_keys:
            label_text, default_val = self.param_specs[key]
            self.create_input_field(self.right_frame, key, label_text, default_val)

        # --- DOLNY PANEL: Przyciski ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
        self.bottom_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_cancel = ctk.CTkButton(self.bottom_frame, text="Anuluj", fg_color="gray", hover_color="#555555", command=self.destroy)
        self.btn_cancel.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_save = ctk.CTkButton(self.bottom_frame, text="Zapisz parametry", fg_color="#2b9348", hover_color="#1b5e20", command=self.save_params)
        self.btn_save.grid(row=0, column=1, padx=5, sticky="ew")

    def create_input_field(self, parent, key, label_text, default_val):
        """render par label and entry field for a given parameter"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        lbl = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=11))
        lbl.pack(side="left", anchor="w")
        
        entry = ctk.CTkEntry(frame, width=120, height=24)
        entry.pack(side="right", anchor="e")
        
        current_val = getattr(self.controller.tps_params, key, default_val) if hasattr(self.controller, 'tps_params') else default_val
        entry.insert(0, str(current_val))
        
        self.entries[key] = entry

    def save_params(self):
        """Save the parameters from the input fields to the controller's tps_params object."""
        parsed_data = {}
        has_error = False

        for key, entry in self.entries.items():
            try:
                val = float(entry.get())
                entry.configure(border_color=["#979da2", "#565b5e"]) 
                parsed_data[key] = val
            except ValueError:
                entry.configure(border_color="red")
                has_error = True

        if has_error:
            return 
        
        self.controller.update_tps_parameters(parsed_data)
        self.destroy()