import numba
numba.config.DISABLE_JIT = True
import customtkinter as ctk
import config
from gui.main_window import MainWindow
from gui.main_window_legency import MainWindow_legency

def main():
    ctk.set_appearance_mode(config.APPEARANCE_MODE)
    ctk.set_default_color_theme(config.THEME_COLOR)
    
    if(config.LEGENCY_LOOK):
        app = MainWindow_legency()
    else:
        app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()