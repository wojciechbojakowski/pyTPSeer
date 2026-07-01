import cv2

def load_image(path):
        """Load and normalize image"""
        try:
            img_bgr = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img_bgr is None:
                raise FileNotFoundError
            
            return img_bgr / 255.0
        
        except Exception:
            print(text="No image found at the specified path.")

def load_grayscale_tif(path):
        """Load a grayscale TIF image and normalize it"""
        return load_image(path)