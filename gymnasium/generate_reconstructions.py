import tensorflow as tf
from BVAE import BVAE

def encode_state(self, left, right):
    left = tf.convert_to_tensor(left, dtype=tf.float32)
    right = tf.convert_to_tensor(right, dtype=tf.float32)
    left, right = tf.reshape(left, (128, 128, 1)), tf.reshape(right, (128, 128, 1))
    inputs = tf.stack([left, right], axis=0)  # Shape: (2, 128, 128, 1)
    mu, logvar, sigma, _ = self.bvae_model.encode(inputs)
    self.index += 1
    sampled_z = self.bvae_model.sampler([mu, sigma])
    decoded_x = self.bvae_model.decode(sampled_z)
    # plot the decoded image
    print("SHowing decoded image for left viewport:")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(8, 4))
    axs[0].imshow(left[:, :, 0], cmap='gray')
    axs[0].set_title('Original Left')
    axs[0].axis('off')
    axs[1].imshow(decoded_x[0, :, :, 0], cmap='gray')
    axs[1].set_title('Reconstructed Left')
    axs[1].axis('off')
    plt.savefig(f'decoded_left_viewport_{self.index}.png')
    plt.close(fig)

    mu_left, mu_right = mu[0], mu[1]
    return mu_left, mu_right

