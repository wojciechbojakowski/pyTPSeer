# core/signal_processing.py
import numpy as np
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d
from models.sampling_mode import SmoothingMode

def apply_spectrum_smoothing(dnde_array: np.ndarray, mode: SmoothingMode, param: float = 11.0) -> np.ndarray:
    """
    Aplikuje wybrane wygładzanie na tablicy dN/dE.
    """
    if len(dnde_array) < 5 or mode == SmoothingMode.NONE:
        return dnde_array.copy()

    if mode == SmoothingMode.SAVGOL:
        window_length = int(param)
        if window_length % 2 == 0:
            window_length += 1  # Wymóg Savitzky-Golay: długość okna musi być nieparzysta
            
        window_length = min(window_length, len(dnde_array))
        polyorder = 2
        
        if window_length <= polyorder:
            return dnde_array.copy()

        return savgol_filter(dnde_array, window_length=window_length, polyorder=polyorder)

    elif mode == SmoothingMode.GAUSSIAN:
        return gaussian_filter1d(dnde_array, sigma=param)

    return dnde_array.copy()