# core/numerical_engine.py
import numpy as np
import math
from numba import njit
import config

# =========================================================================
# I. PUBLICZNE PUNKTY WEJŚCIA DLA VIEWMODELU (POBIERAJĄ MODELE DATACLASS)
# =========================================================================

def draw_parabole_jit(tps, p_config, x_zero: float, y_zero: float, rotation_deg: float):
    """
    Publiczny wrapper Pythona wywoływany przez ViewModel.
    Pobiera czyste instancje modeli TPSParameters oraz ParabolaConfig,
    wyciąga z nich surowe wartości liczbowe i przekazuje do szybkiego silnika JIT.
    """
    sampling_mode_code = p_config.sampling_mode.code  # Pobranie kodu int z Enuma
    print("LOG STARTING DRAW_PARABOLE_JIT 18")
    # Wywołanie skompilowanego rdzenia
    x_points, y_points, E_sampling = _calculate_parabola_points(
        B=tps.B_field,
        E_field=tps.E_field,
        Zm1=tps.Zm1, Zm2=tps.Zm2,
        Ze1=tps.Ze1, Ze2=tps.Ze2,
        d1=tps.d1, d2=tps.d2, Zd=tps.Zd,
        x_zero=x_zero,
        y_zero=y_zero,
        A=p_config.A,
        Q=p_config.Q,
        E_min=p_config.E_min,
        E_max=p_config.E_max,
        rotation_deg=rotation_deg,
        sampling_mode_code=sampling_mode_code
    )
    print("LOG STARTING DRAW_PARABOLE_JIT 35")
    return x_points, y_points, E_sampling


def extract_tps_spectrum_jit(img_matrix, x_m, y_m, E_arr, parabola_config, tps_params, threshold_grey=0.1, method="FlatBox"):
    """
    Publiczny wrapper Pythona dla analizatora widma energii.
    Odpytuje modele o niezbędną geometrię i uruchamia optymalizowaną pętlę.
    """
    # Mapowanie wybranej metody w GUI na flagę numeryczną dla Numby
    method_mapping = {"FlatBox": 0, "Gaussian": 1, "PinholeBackground": 2}
    scan_mode_flag = method_mapping.get(method, 0)
    print("LOG extract_tps_spectrum_JIT 47")
    
    # Wyciągamy surowe dane fizyczne z modeli dataclass
    mass_u = float(parabola_config.A)
    pin_d_m = float(tps_params.pin_d) * 0.001       # mm -> m
    pin_target = float(tps_params.pin_target)       # m
    
    pixels_per_m = 1.0 / config.PX_TO_METER
    solid_angle = (math.pi * (pin_d_m / 2.0) ** 2) / (pin_target ** 2)
    
    # Wywołanie wielowątkowego, skompilowanego rdzenia analizy obrazu
    energy_spectrum, dnde_spectrum = _extraction_core_loop(
        x_m=x_m,
        y_m=y_m,
        ep=E_arr,
        img_matrix=img_matrix,
        mass_u=mass_u,
        solid_angle=solid_angle,
        pixels_per_m=pixels_per_m,
        threshold_grey=threshold_grey,
        pinhole_m=pin_d_m,
        scan_mode_flag=scan_mode_flag
    )
    print("LOG extract_tps_spectrum_JIT 70")
    return energy_spectrum, dnde_spectrum


# =========================================================================
# II. SKOMPILOWANY SILNIK INTEGRACJI TRAJEKTORII (NUMBA JIT)
# =========================================================================

@njit(fastmath=True, nogil=True)
def _calculate_parabola_points(
    B, E_field, Zm1, Zm2, Ze1, Ze2, d1, d2, Zd,
    x_zero, y_zero, A, Q, E_min, E_max, rotation_deg, sampling_mode_code, gamma=1.0
):
    m_ion = A * config.M_ION
    q = Q * config.Q_ION

    # Współczynniki klinowych okładzin elektrycznych
    if abs(Ze2 - Ze1) > 1e-12:
        Ae = (d2 - d1) / (Ze2 - Ze1)
    else:
        Ae = 0.0
    Be = d1 - Ae * Ze1

    t = np.linspace(0.0, 1.0, config.MAX_PTS)
    E = np.zeros(config.MAX_PTS)

    # Wybór algorytmu próbkowania energii na podstawie kodu Enuma
    if sampling_mode_code == 0:    # LINEAR
        E = E_min + t * (E_max - E_min)
    elif sampling_mode_code == 1:  # QUADRATIC
        E = E_min + (t ** 2) * (E_max - E_min)
    elif sampling_mode_code == 2:  # POWER
        E = E_min + (t ** gamma) * (E_max - E_min)
    else:
        E = E_min + (t ** 2) * (E_max - E_min)

    # Integracja równań ruchu (Pusher)
    x_E, y_E = _particle_pusher_jit(
        E, E_field, m_ion, q, Zm1, Zm2, Ze1, Ze2, Zd, Ae, Be, B, config.MAX_TIME_STEPS, config.MAX_PTS, config.MeV_TO_J
    )

    # Przesunięcie do fizycznego punktu zero spektrometru
    x_E += x_zero
    y_E += y_zero

    # Transformacja obrotu wokół punktu zero (start point)
    rot = rotation_deg * (-0.0174532925)  # stopnie -> radiany
    dx = x_E - x_zero
    dy = y_E - y_zero

    xr = dx * math.cos(rot) - dy * math.sin(rot) + x_zero
    yr = dx * math.sin(rot) + dy * math.cos(rot) + y_zero

    return xr, yr, E


@njit(fastmath=True, nogil=True)
def _particle_pusher_jit(E, E_field, m_ion, q, Zm1, Zm2, Ze1, Ze2, Zd, Ae, Be, B, max_time_steps, max_pts, mev_to_j):
    """Czysty numeryczny algorytm integracji Verlet/Euler równań ruchu cząstki."""
    x_ret = np.zeros(max_pts)
    y_ret = np.zeros(max_pts)

    for j in range(max_pts):
        z = 0.0
        vx = 0.0
        vy = 0.0
        
        # Zabezpieczenie przed ujemną lub zerową energią (unikamy dzielenia przez zero i pierwiastka z ujemnej)
        safe_E = max(E[j], 1e-6)
        vz = math.sqrt(2.0 * mev_to_j * safe_E / m_ion)
        vz = max(vz, 1e-12)

        Tp = Zd / vz
        dt = Tp / float(max_time_steps)

        x_E = 0.0
        y_E = 0.0
        
        for i in range(max_time_steps):
            z += vz * dt

            Fx = 0.0
            Fy = 0.0

            # Siła Lorentza w polu magnetycznym (oś Y)
            if Zm1 < z < Zm2:
                Fy = q * vz * B
                
            # Siła w klinowym polu elektrycznym (oś X)
            if Ze1 < z < Ze2:
                spacing = Ae * z + Be
                if abs(spacing) > 1e-12:
                    El = E_field / spacing
                    Fx = q * El

            ax = Fx / m_ion
            ay = Fy / m_ion

            vx += ax * dt
            vy += ay * dt

            x_E += vx * dt
            y_E += vy * dt

        x_ret[j] = x_E
        y_ret[j] = y_E

    return x_ret, y_ret


# =========================================================================
# III. SKOMPILOWANY SILNIK ANALIZY OBRAZU (NUMBA EXTRACTOR)
# =========================================================================

@njit(fastmath=True, nogil=True)
def _psl_from_grey(grey01):
    """Konwersja znormalizowanej jasności (0.0 - 1.0) na jednostki PSL."""
    return (25.0 / 100.0) * (25.0 / 100.0) * (10.0 ** (5.0 * (grey01 - 0.5)))


@njit(fastmath=True, nogil=True)
def _psl_scaling(e_mev, mass_u):
    """Charakterystyka czułości detektora obrazu (IP) dla różnych jonów."""
    if mass_u == 1.0:
        return 0.151 * (e_mev ** 0.6) if e_mev < 1.6 else 0.284 * (e_mev ** -0.75)
    if mass_u == 12.0:
        if e_mev <= 73.6:
            return (2.51e-3 + 4.56e-4 * e_mev - 8.9e-6 * e_mev**2 + 4.61e-8 * e_mev**3) * e_mev
        return 4.55 * (e_mev ** -0.533)
    return 1.0


@njit(fastmath=True, nogil=True)
def _get_trace_half_width(e_mev, pinhole_px):
    """Modeluje poszerzenie geometryczne śladu jonowego na MCP."""
    broadening = (2.0 / max(e_mev, 0.1)) ** 0.35
    w = 0.5 * pinhole_px * (1.0 + 0.35 * broadening)
    return min(max(w, 2.0), 120.0)


# --- METODY PRÓBKOWANIA PIKSELI ---

@njit(fastmath=True, nogil=True)
def _scan_method_flat_box(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background):
    """Metoda A: Prosty, prostokątny kadr całkujący o płaskim profilu."""
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


@njit(fastmath=True, nogil=True)
def _scan_method_gaussian_profile(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background):
    """Metoda B: Całkowanie z wagowaniem odległości rozkładem Gaussa."""
    y_pixels, x_pixels = img_matrix.shape
    signal_psl = 0.0
    signal_n = 0
    
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
                    gaussian_weight = math.exp(-0.5 * (float(w) / sigma) ** 2)
                    signal_psl += psl * gaussian_weight
                    signal_n += 1
                    
    return signal_psl, signal_n


@njit(fastmath=True, nogil=True)
def _scan_method_pinhole_background(img_matrix, x_center, y_center, dx, dy, norm, nx, ny, slice_half_width, slice_length):
    """Metoda C: Inteligentny pomiar lokalnego szumu i tła w skrzydłach przesłony."""
    y_pixels, x_pixels = img_matrix.shape
    
    bg_gap = 4     # Bezpieczny odstęp
    bg_width = 10  # Pasek pomiarowy tła
    
    bg_sum = 0.0
    bg_count = 0
    
    # Próbkowanie tła w lewym i prawym skrzydle śladu
    for s in range(-slice_length, slice_length + 1):
        # Lewe skrzydło
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
                
        # Prawe skrzydło
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

    avg_bg_psl = bg_sum / bg_count if bg_count > 0 else 0.0

    # Całkowanie sygnału po odjęciu dynamicznego tła
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
                psl = _psl_from_grey(grey) - avg_bg_psl
                
                if psl > 0.0:
                    signal_psl += psl
                    signal_n += 1
                    
    return signal_psl, signal_n


# --- GŁÓWNA PĘTLA ANALIZATORA ---

@njit(fastmath=True, nogil=True)
def _extraction_core_loop(x_m, y_m, ep, img_matrix, mass_u, solid_angle, pixels_per_m, threshold_grey, pinhole_m, scan_mode_flag):
    """Ciężki silnik wycinania i analizy spektralnej."""
    max_pts = len(x_m)
    psl_background = _psl_from_grey(threshold_grey)
    pinhole_px = pinhole_m * pixels_per_m
    
    out_E = np.zeros(max_pts)
    out_dNdE = np.zeros(max_pts)
    valid_count = 0
    
    for i in range(1, max_pts - 1):
        e_mev = ep[i] / mass_u
        
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
        
        if scan_mode_flag == 0:
            signal_psl, signal_n = _scan_method_flat_box(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background
            )
            effective_width = 2.0 * half_w + 1.0
        elif scan_mode_flag == 1:
            signal_psl, signal_n = _scan_method_gaussian_profile(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length, psl_background
            )
            sigma = max(half_w / 2.0, 1.0)
            effective_width = math.sqrt(2.0 * math.pi) * sigma
        elif scan_mode_flag == 2:
            signal_psl, signal_n = _scan_method_pinhole_background(
                img_matrix, x_center_px, y_center_px, dx, dy, norm, nx, ny, slice_half_width, slice_length
            )
            effective_width = 2.0 * half_w + 1.0
        else:
            signal_psl, signal_n = 0.0, 0
            effective_width = 1.0
            
        # Zabezpieczenie dla słabych śladów na krawędziach
        if signal_n < 1:
            continue
            
        scale = _psl_scaling(e_mev, mass_u)
        if scale <= 0.0:
            continue
            
        particles = signal_psl / scale / effective_width

        dE = abs(ep[i+1] - ep[i-1]) / (2.0 * mass_u)
        if dE <= 0.0:
            continue
            
        dNdEdOmega = particles / dE / solid_angle
        
        if math.isfinite(dNdEdOmega) and dNdEdOmega > 0.0:
            out_E[valid_count] = e_mev
            out_dNdE[valid_count] = dNdEdOmega
            valid_count += 1
            
    return out_E[:valid_count], out_dNdE[:valid_count]

def calculate_tof_spectrum(E_array_MeV: np.ndarray, dNdE_array: np.ndarray, A: float, L_path_m: float = 1.0):
    """
    Konwertuje widmo energii (E vs dN/dE) na widmo czasu przelotu TOF (t [ns] vs Signal).
    
    :param E_array_MeV: Tablica energii jonów w MeV/u
    :param dNdE_array: Sygnał różniczkowy dN/dE
    :param A: Liczba masowa (u)
    :param L_path_m: Długość drogi lotu jonów od tarczy do MCP [m]
    :return: (t_ns, signal_tof)
    """
    if len(E_array_MeV) == 0:
        return np.array([]), np.array([])

    # Przeliczenie energii z MeV na Dżule [J]
    m_kg = A * config.M_ION  # Masa w kg
    E_joules = E_array_MeV * A * config.MeV_TO_J

    # Prędkość jonów v = sqrt(2E/m) [m/s]
    velocity = np.sqrt(2 * E_joules / m_kg)

    # Czas przelotu t = L / v [s] -> konwersja na nanosekundy [ns]
    t_seconds = L_path_m / velocity
    t_ns = t_seconds * 1e9

    # Sygnał w czasie: S(t) = dN/dE * |dE/dt|
    # Ponieważ E = 1/2 m (L/t)^2 -> |dE/dt| = m * L^2 / t^3
    dE_dt = (m_kg * (L_path_m ** 2)) / (t_seconds ** 3)
    signal_tof = dNdE_array * (dE_dt / config.MeV_TO_J)

    # Sortujemy dane według rosnącego czasu t (bo wyższe energie docierają wcześniej!)
    sort_idx = np.argsort(t_ns)
    return t_ns[sort_idx], signal_tof[sort_idx]