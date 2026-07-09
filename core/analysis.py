import math

import numpy as np
import config
from numba import njit

import config

def meter_to_pixel(val_meters):
    return int(val_meters / config.PX_TO_METER)

def get_pixel_value(img_matrix, x_meters, y_meters):
    """returns the pixel value at the given coordinates in meters, along with the pixel coordinatess"""
    px_x = meter_to_pixel(x_meters)
    px_y = meter_to_pixel(y_meters)
    
    h, w = img_matrix.shape
    if 0 <= px_x < w and 0 <= px_y < h:
        return img_matrix[px_y, px_x], px_x, px_y
    return None, None, None

def draw_parabole(controller, A, Q, E_max, E_min, sampling_mode="Quadratic", gamma=1.0):
    """Draws a parabola on the image based on the current parameters. based on draw_parabole in line 1205"""
    if controller.start_point is not None:
        x_zero, y_zero = controller.start_point
    else:
        x_zero, y_zero = 0.0, 0.0

    p = controller.tps_params
    B = float(p.get("B_field", 0.5))
    U = float(p.get("E_field", 100000))
    Zm1 = float(p.get("Zm1", 0.1))
    Zm2 = float(p.get("Zm2", 0.2))
    Ze1 = float(p.get("Ze1", 0.1))
    Ze2 = float(p.get("Ze2", 0.2))
    d1 = float(p.get("d1", 0.05))
    d2 = float(p.get("d2", 0.05))
    Zd = float(p.get("Zd", 0.5))
    pin_d = float(p.get("pin_d", 2.0))
    pin_target = float(p.get("pin_target", 0.1))

    mIon = A * config.M_ION
    q = Q * config.Q_ION

    pin_diameter_m = pin_d * 0.001  # Convert to m

    solid_angle = (math.pi *(pin_diameter_m / 2) ** 2) / (pin_target ** 2)

    Ae = (d2-d1)/(Ze2-Ze1)

    Be = d1 - Ae * Ze1

    max_pts = config.MAX_PTS
    t=np.linspace(0.0, 1.0, max_pts)

    E0 = E_min
    E1 = E_max

    E = E0

    if sampling_mode == "Linear":
        E = E0 + t *(E1-E0)
    if sampling_mode == "Quadratic":
        E = E0 + (t**2)*(E1-E0)
    if sampling_mode == "Exponential":
        E = E0 + (t**gamma)*(E1-E0)

    x_E, y_E = _particle_pusher(E, U, mIon, q, Zm1, Zm2, Ze1, Ze2, Zd, Ae, Be, B)

    # SHIFT TO ZERO
    x_E += x_zero
    y_E += y_zero

    rot = controller.rotation_deg * (-0.0174532925)
    dx = x_E - x_zero
    dy = y_E - y_zero

    xr = dx * np.cos(rot) - dy * np.sin(rot)
    yr = dx * np.sin(rot) + dy * np.cos(rot)

    return xr + x_zero, yr + y_zero, E

@njit(fastmath=True)
def _particle_pusher(E, E_field, mIon, q, Zm1, Zm2, Ze1, Ze2, Zd, Ae, Be, B, Max_time_points=config.MAX_Time_points, Max_pts=config.MAX_PTS, MeVTOJ = config.MeV_TO_J):
    
    x_ret = np.zeros(Max_pts)
    y_ret = np.zeros(Max_pts)

    for j in range(Max_pts):
        z = 0
        vx = 0
        vy = 0
        vz = np.sqrt(2.0 * MeVTOJ*E[j]/mIon)

        Tp = Zd/vz
        dt = Tp / float(Max_time_points)

        x_E = 0.0
        y_E = 0.0
        
        for i in range(Max_time_points):
            z += vz * dt

            Fx = 0.0
            Fy = 0.0

            if(z>Zm1 and z<Zm2):
                Fy = q * vz * B
            if(z>Ze1 and z<Ze2):
                El = E_field/(Ae * z + Be)
                Fx = q * El

            ax = Fx/mIon
            ay = Fy/mIon

            vx += ax * dt
            vy += ay * dt

            x_E += vx * dt
            y_E += vy * dt

        x_ret[j] = x_E
        y_ret[j] = y_E

    return x_ret, y_ret


def PSL_from_grey(grey01):
    """Converts a 16-bit grayscale value to PSL (Photo-Stimulated Luminescence) units based on the formula from the original code. LINE #1468"""
    return (25.0/100.0)*(25.0/100.0)*10.0**(5.0*(grey01/65534-0.5))

def PSL_Scaling(EMeV, mass):
    if(mass == 1.0):
        if(EMeV < 1.6):
            return 0.151 * EMeV**0.6
        return 0.284*EMeV**-0.75

    if(mass == 12.0):
        if(EMeV <= 73.6):
            return(
                    2.51e-3
                    +
                    4.56e-4*EMeV
                    -
                    8.9e-6*EMeV*EMeV
                    +
                    4.61e-8*EMeV*EMeV*EMeV
                )*EMeV
        return 4.55*EMeV**(-0.533)
    return 1.0

def traceHalfWidthPx(EMeV, d_pinhole):
    broadening = config.Eref/np.max(EMeV,0.1)**config.widthAlpha
    pinholePx = meter_to_pixel(d_pinhole*0.001)
    w = 0.5*pinholePx*(1.0+ broadening*config.widthGain)
    return np.clip(w, 2.0, 120.0)

def inside(px, py, x_pixels, y_pixels):
    return (0 <= px < x_pixels) and (0 <= py < y_pixels)

def filter_inside_points(px_array, py_array, x_pixels, y_pixels):
    mask = (px_array >= 0) & (px_array < x_pixels) & (py_array >= 0) & (py_array < y_pixels)
    return mask

@njit(fastmath=True)
def Energy_Graph(Ep, x, y, mass, d_phole, xPixels, yPixels, slice_Length = config.sliceLength , pixels_per_m=config.PX_TO_METER, pts_max = config.MAX_PTS):
    max_E = 0.0
    for i in range(pts_max):
        EMeV = Ep[i] / mass
        if(EMeV > max_E):
            max_E = EMeV
        dx = (x[i+1] - x[i-1])*pixels_per_m
        dy =(y[i+1] - y[i-1])*pixels_per_m
        norm = np.hypot(dx,dy)

        if(norm < 1e-12):
            continue

        nx = -dy / norm
        ny = dx / norm

        halfW = traceHalfWidthPx(EMeV, d_pinhole=d_phole)
        sliceHalfWidth = int(np.ceil(halfW))

        signalPSL = 0.0
        signalN = 0

        for j in range(start=-slice_Length, stop=slice_Length, step=1):
            for k in range(start=-sliceHalfWidth, stop=sliceHalfWidth, step=1):
                pxf = x[i]*pixels_per_m + j*(dx/norm) + k*nx
                pyf = y[i]*pixels_per_m + j*(dy/norm) + k*ny
                px = int(np.round(pxf))
                py = int(np.round(pyf))
                if(0>px>xPixels and 0>py>yPixels):
                    continue
                imgY = yPixels - 1 - py
                
