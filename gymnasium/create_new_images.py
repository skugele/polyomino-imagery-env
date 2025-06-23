import numpy as np
import matplotlib.pyplot as plt

all_white = np.full((128, 128), 255, dtype=np.uint8)
all_black = np.zeros((128, 128), dtype=np.uint8)

plt.imsave('all_white.png', all_white, cmap='gray', vmin=0, vmax=255)
plt.imsave('all_black.png', all_black, cmap='gray', vmin=0, vmax=255)
