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
