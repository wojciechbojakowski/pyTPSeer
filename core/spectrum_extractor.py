# core/spectrum_extractor.py
import numpy as np
import math
from numba import njit
import config

# =========================================================================
# 1. FUNKCJE KALIBRACYJNE I GEOMETRYCZNE (PODMODELE)
# =========================================================================

@njit
def _psl_from_grey(grey01):
    """Konwersja szarości 16-bit na liniową jednostkę PSL skanera."""
    return (25.0 / 100.0) * (25.0 / 100.0) * (10.0 ** (5.0 * (grey01 - 0.5)))

@njit
def _psl_scaling(e_mev, mass_u):
    """Funkcja odpowiedzi detektora IP dla H (1.0) oraz C (12.0)."""
    if mass_u == 1.0:
        return 0.151 * (e_mev ** 0.6) if e_mev < 1.6 else 0.284 * (e_mev ** -0.75)
    if mass_u == 12.0:
        if e_mev <= 73.6:
            return (2.51e-3 + 4.56e-4 * e_mev - 8.9e-6 * e_mev**2 + 4.61e-8 * e_mev**3) * e_mev
        return 4.55 * (e_mev ** -0.533)
    return 1.0

@njit
def _get_trace_half_width(e_mev, pinhole_px):
    """Model rozmycia śladu w zależności od energii jonu."""
    broadening = (2.0 / max(e_mev, 0.1)) ** 0.35
    w = 0.5 * pinhole_px * (1.0 + 0.35 * broadening)
    return min(max(w, 2.0), 120.0)


# =========================================================================
# 2. WYMIENNE METODY SKANOWANIA / PROFILE LINII (TUTAJ DODAJESZ NOWE MODELE)
# =========================================================================

@njit
def _scan_method_flat_box(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background):
    """
    METODA A: Klasyczny płaski kadr prostokątny (Oryginał z C++).
    Zwykła suma nieprzyciętych wagowo pikseli powyżej tła.
    """
    y_pixels, x_pixels = img_matrix.shape
    signal_psl = 0.0
    signal_n = 0
    
    for s in range(-slice_length, slice_length + 1):
        for w in range(-slice_half_width, slice_half_width + 1):
            pxf = x_center + s * (dx / norm) + w * nx
            pyf = y_center + s * (dy / norm) + w * ny
            
            px, py = int(round(pxf)), int(round(pyf))
            
            if 0 <= px < x_pixels and 0 <= py < y_pixels:
                img_y = y_pixels - 1 - py
                grey = float(img_matrix[img_y, px])
                psl = _psl_from_grey(grey) - psl_background
                
                if psl > 0.0:
                    signal_psl += psl
                    signal_n += 1
                    
    return signal_psl, signal_n


@njit
def _scan_method_gaussian_profile(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background):
    """
    METODA B: Model profilu Gaussowskiego.
    Piksele oddalone od środka paraboli (w) mają mniejszą wagę zgodnie z rozkładem Normalnym.
    """
    y_pixels, x_pixels = img_matrix.shape
    signal_psl = 0.0
    signal_n = 0
    
    # Założenie: half_w reprezentuje promień plamki (~2 * sigma)
    sigma = max(float(slice_half_width) / 2.0, 1.0)
    
    for s in range(-slice_length, slice_length + 1):
        for w in range(-slice_half_width, slice_half_width + 1):
            pxf = x_center + s * (dx / norm) + w * nx
            pyf = y_center + s * (dy / norm) + w * ny
            
            px, py = int(round(pxf)), int(round(pyf))
            
            if 0 <= px < x_pixels and 0 <= py < y_pixels:
                img_y = y_pixels - 1 - py
                grey = float(img_matrix[img_y, px])
                psl = _psl_from_grey(grey) - psl_background
                
                if psl > 0.0:
                    # Mnożymy sygnał przez gęstość prawdopodobieństwa Gaussa w punkcie 'w'
                    gaussian_weight = math.exp(-0.5 * (float(w) / sigma) ** 2)
                    signal_psl += psl * gaussian_weight
                    signal_n += 1
                    
    return signal_psl, signal_n

@njit
def _scan_method_pinhole_background(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length):
    """
    METODA C: Dynamiczne próbkowanie tła ze skrzydeł paraboli.
    Mierzy tło tuż poza zasięgiem pinhole i odejmuje je od sygnału w środku.
    """
    y_pixels, x_pixels = img_matrix.shape
    
    # Parametry geometrii tła (zbieżne z oryginalnym kodem C++)
    bg_gap = 4     # Odstęp od krawędzi śladu, aby nie łapać jonów
    bg_width = 10  # Szerokość paska, z którego uśredniamy tło
    
    bg_sum = 0.0
    bg_count = 0
    
    # --- FAZA 1: Pomiar lokalnego tła w "skrzydłach" ---
    for s in range(-slice_length, slice_length + 1):
        # Lewe skrzydło tła
        left_bg_start = -(slice_half_width + bg_gap + bg_width)
        left_bg_end = -(slice_half_width + bg_gap)
        for w in range(left_bg_start, left_bg_end + 1):
            pxf = x_center + s * (dx / norm) + w * nx
            pyf = y_center + s * (dy / norm) + w * ny
            px, py = int(round(pxf)), int(round(pyf))
            
            if 0 <= px < x_pixels and 0 <= py < y_pixels:
                img_y = y_pixels - 1 - py
                grey = float(img_matrix[img_y, px])
                bg_sum += _psl_from_grey(grey)
                bg_count += 1
                
        # Prawe skrzydło tła
        right_bg_start = (slice_half_width + bg_gap)
        right_bg_end = (slice_half_width + bg_gap + bg_width)
        for w in range(right_bg_start, right_bg_end + 1):
            pxf = x_center + s * (dx / norm) + w * nx
            pyf = y_center + s * (dy / norm) + w * ny
            px, py = int(round(pxf)), int(round(pyf))
            
            if 0 <= px < x_pixels and 0 <= py < y_pixels:
                img_y = y_pixels - 1 - py
                grey = float(img_matrix[img_y, px])
                bg_sum += _psl_from_grey(grey)
                bg_count += 1

    # Obliczamy średnie PSL tła na 1 piksel w tej okolicy
    avg_bg_psl = bg_sum / bg_count if bg_count > 0 else 0.0

    # --- FAZA 2: Zbieranie czystego sygnału z rdzenia paraboli ---
    signal_psl = 0.0
    signal_n = 0
    
    for s in range(-slice_length, slice_length + 1):
        for w in range(-slice_half_width, slice_half_width + 1):
            pxf = x_center + s * (dx / norm) + w * nx
            pyf = y_center + s * (dy / norm) + w * ny
            px, py = int(round(pxf)), int(round(pyf))
            
            if 0 <= px < x_pixels and 0 <= py < y_pixels:
                img_y = y_pixels - 1 - py
                grey = float(img_matrix[img_y, px])
                
                # Odejmujemy dynamicznie wyliczone tło zamiast stałego suwaka!
                psl = _psl_from_grey(grey) - avg_bg_psl
                
                if psl > 0.0:
                    signal_psl += psl
                    signal_n += 1
                    
    return signal_psl, signal_n
# =========================================================================
# 3. GŁÓWNY SKOMPILOWANY SILNIK OBLICZENIOWY (NJIT LOOP)
# =========================================================================

@njit(fastmath=True)
def _extraction_core_loop(x_m, y_m, ep, img_matrix, mass_u, solid_angle, pixels_per_m, threshold_grey, pinhole_m, scan_mode_flag):
    """
    Ciężka pętla przetwarzania. Zamiast wolnego append, alokuje z góry tablice wynikowe 
    i wycina paski danych przy użyciu wybranej metody skanowania.
    """
    max_pts = len(x_m)
    psl_background = _psl_from_grey(threshold_grey)
    pinhole_px = pinhole_m * pixels_per_m
    
    # Alokacja pamięci z góry (maksymalny możliwy rozmiar to max_pts)
    out_E = np.zeros(max_pts)
    out_dNdE = np.zeros(max_pts)
    valid_count = 0
    
    for i in range(1, max_pts - 1):
        e_mev = ep[i] / mass_u
        
        # Geometria lokalnej pochodnej (styczna i normalna)
        dx = (x_m[i+1] - x_m[i-1]) * pixels_per_m
        dy = (y_m[i+1] - y_m[i-1]) * pixels_per_m
        norm = math.hypot(dx, dy)
        
        if norm < 1e-12:
            continue
            
        nx = -dy / norm
        ny = dx / norm
        
        half_w = _get_trace_half_width(e_mev, pinhole_px)
        slice_half_width = int(math.ceil(half_w))
        slice_length = 4
        
        x_center_px = x_m[i] * pixels_per_m
        y_center_px = y_m[i] * pixels_per_m
        
        # --- PODMIANA METODY SKANOWANIA (DISPATCHER) ---
        if scan_mode_flag == 0:
            signal_psl, signal_n = _scan_method_flat_box(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background
            )
            effective_width = 2.0 * half_w + 1.0
        elif scan_mode_flag == 1:
            signal_psl, signal_n = _scan_method_gaussian_profile(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background
            )
            # Dla rozkładu normalnego efektywna szerokość całki to sqrt(2*pi)*sigma
            sigma = max(half_w / 2.0, 1.0)
            effective_width = math.sqrt(2.0 * math.pi) * sigma
        elif scan_mode_flag == 2:
            # NOWOŚĆ: Wywołanie metody inteligentnego tła szumów przesłony
            signal_psl, signal_n = _scan_method_pinhole_background(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length
            )
            effective_width = 2.0 * half_w + 1.0
        else:
            signal_psl, signal_n = 0.0, 0
            effective_width = 1.0
            
        if signal_n < 5:
            continue
            
        scale = _psl_scaling(e_mev, mass_u)
        if scale <= 0:
            continue
            
        # Przeliczenie cząstek
        particles = signal_psl / scale / effective_width

        # Krok widmowy energii
        dE = abs(ep[i+1] - ep[i-1]) / (2.0 * mass_u)
        if dE <= 0:
            continue
            
        dNdEdOmega = particles / dE / solid_angle
        
        if math.isfinite(dNdEdOmega) and dNdEdOmega > 0:
            out_E[valid_count] = e_mev
            out_dNdE[valid_count] = dNdEdOmega
            valid_count += 1
            
    # Zwracamy tylko zapełnioną część tablic (obcięcie pustych elementów)
    return out_E[:valid_count], out_dNdE[:valid_count]


# =========================================================================
# 4. JEDNA GŁÓWNA FUNKCJA URUCHAMIAJĄCA KOMBAJN (PUBLIC ENTRY POINT)
# =========================================================================

def extract_tps_spectrum(controller, x_m, y_m, E_arr, parabola_config, method="FlatBox"):
    """
    Główna funkcja wywoływana z poziomu GUI.
    Pobiera wszystkie niezbędne zmienne ze stanu programu i uruchamia silnik Numba.
    """
    p = controller.tps_params
    img = controller.img_norm
    cut_off_treshhold = 0.1 #TODO controller with sidebar
    
    if img is None:
        raise ValueError("Brak wczytanego obrazu do ekstrakcji widma!")
        
    # Mapowanie nazwy metody na flagę całkowitą (wygodną dla Numby)
    method_mapping = {"FlatBox": 0, "Gaussian": 1}
    scan_mode_flag = method_mapping.get(method, 0)
    
    # Pobranie parametrów geometrycznych i stałych
    mass_u = float(parabola_config["A"])
    d1 = float(p.get("d1_field", 0.05))
    d2 = float(p.get("d2_field", 0.05))
    Ze1 = float(p.get("Ze1", 0.1))
    Ze2 = float(p.get("Ze2", 0.2))
    pin_d_m = float(p.get("pin_d", 2.0)) * 0.001
    pin_target = float(p.get("pin_target", 0.1))
    
    # Pobranie parametrów skanowania ze suwaków GUI (lub configu)
    threshold_grey = float(cut_off_treshhold)  # Wartość od 0 do 1 z suwaka tła
    pixels_per_m = 1.0 / config.PX_TO_METER

    # Obliczenia fizycznego kąta bryłowego pinu
    solid_angle = (math.pi * (pin_d_m / 2.0) ** 2) / (pin_target ** 2)
    
    # Wywołanie skompilowanego rdzenia
    energy_spectrum, dnde_spectrum = _extraction_core_loop(
        x_m=x_m,
        y_m=y_m,
        ep=E_arr,
        img_matrix=img,
        mass_u=mass_u,
        solid_angle=solid_angle,
        pixels_per_m=pixels_per_m,
        threshold_grey=threshold_grey,
        pinhole_m=pin_d_m,
        scan_mode_flag=scan_mode_flag
    )
    
    return energy_spectrum, dnde_spectrum