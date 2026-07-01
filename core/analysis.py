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