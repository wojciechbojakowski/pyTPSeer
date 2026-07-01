import cv2
import matplotlib.pyplot as plt

img_bgr = cv2.imread('../../dane/20240206-175820-60740-[Phosphor].tif', cv2.IMREAD_GRAYSCALE)
piks_mm = 40
piks_m = 1/(piks_mm*1000.0)

img_norm = img_bgr / 255.0

plt.imshow(img_norm, cmap='jet', extent=[0, img_norm.shape[1]*piks_m, img_norm.shape[0]*piks_m, 0])
plt.colorbar(label='Znormalizowana wartość pikseli')
plt.ticklabel_format(style='sci', scilimits=(0,0), axis='both')
punkty = plt.ginput(n=1, timeout=0)
print("\n--- Wybrane punkty ---")
for i, pt in enumerate(punkty):
    x, y = int(pt[0]), int(pt[1])
    wartosc = img_norm[y, x] 
    print(f"Punkt {i+1}: Współrzędne (X={x}, Y={y}) -> Znormalizowana jasność: {wartosc:.4f}")
plt.show()

def load_image(image_path):
    img_bgr = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img_norm = img_bgr / 255.0
    return img_norm
