# models/mcp_image.py
from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple
import cv2
from config import PX_TO_METER

@dataclass
class MCPImage:
    raw_matrix:      np.ndarray #numpy matrix; value 0.0-1.0         
    file_path:   str        #filepath to orginal file
    
    start_point: Optional[Tuple[float, float]] = None #starting point in meters
    background_threshold = 0.0

    @property
    def shape(self) -> Tuple[int, int]:
        return self.raw_matrix.shape

    @property
    def height(self) -> int:
        return self.raw_matrix.shape[0]

    @property
    def width(self) -> int:
        return self.raw_matrix.shape[1]
    
    @property
    def matrix(self) -> np.ndarray:
        """
        Zwraca macierz obrazu po odcięciu tła.
        Wszystkie wartości poniżej background_threshold są zerowane.
        """
        if self.background_threshold <= 0.0:
            return self.raw_matrix
            
        # Tworzymy kopię i zerujemy szum poniżej progu
        filtered = self.raw_matrix.copy()
        filtered[filtered < self.background_threshold] = 0.0
        return filtered
    
    @classmethod
    def load_and_normalize(cls, path:str) -> Optional['MCPImage']:
        try:
            img_bgr = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img_bgr is None:
                raise FileNotFoundError
            
            normalized_matrix = img_bgr / 255.0
            
            return cls(raw_matrix=normalized_matrix, file_path=path)
        
        except Exception as e:
            print(f"No image found at the specified path. Error: {e}")
            return None

    def get_pixel_value_at_meters(self, x_meters, y_meters, px_to_meter=PX_TO_METER):
        px_x = int(round(x_meters / px_to_meter))
        px_y = int(round(y_meters / px_to_meter))
        
        h, w = self.shape
        img_y = h - 1 - px_y
        if 0 <= px_x < w and 0 <= img_y < h:
            return self.raw_matrix[img_y, px_x], px_x, img_y
        return None, None, None
