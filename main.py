import customtkinter as ctk
import config
from gui.main_window import MainWindow

def main():
    ctk.set_appearance_mode(config.APPEARANCE_MODE)
    ctk.set_default_color_theme(config.THEME_COLOR)
    
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()