import numpy as np
from PIL import Image

# Pobierz wymiary z istniejącej macierzy (np. 2048x2048)
height, width = 4504, 4504 #img_matrix.shape

# Tworzymy pustą macierz 16-bitową (same zera)
black_array = np.full((height, width), 2000, dtype=np.uint16)

# (Opcjonalnie) Jeśli chcesz stałe niskie tło zamiast bezwzględnego zera:
# black_array = np.full((height, width), 500, dtype=np.uint16)

# Zapisujemy jako plik TIFF
img = Image.fromarray(black_array)
img.save("05_test.tiff")
print("Zapisano plik 05_test.tiff")