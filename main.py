# main.py
import customtkinter as ctk
import config
from viewmodels.workspace_vm import WorkspaceViewModel
from views.main_window import MainWindow

def main():
    workspace_viewmodel = WorkspaceViewModel()
    
    ctk.set_appearance_mode(config.APPEARANCE_MODE)
    ctk.set_default_color_theme(config.THEME_COLOR)
    
    app = MainWindow(viewmodel=workspace_viewmodel)
    app.mainloop()

if __name__ == "__main__":
    main()