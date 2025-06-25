import tensorflow as tf
import pandas as pd
import numpy as np
from time import time
from tensorflow.keras.layers import Conv2D, MaxPool2D, Flatten, Dense, Lambda, Reshape, Conv2DTranspose, BatchNormalization

# PARAMETERS
INPUT_HEIGHT = 128
INPUT_WIDTH = 128

INPUT_SHAPE = (INPUT_HEIGHT, INPUT_WIDTH, 1)

latent_dims = 16

class Preprocessor(tf.keras.Model):
  def __init__(self):
    super().__init__(name="preprocessor")
    self.resizer = tf.keras.layers.Resizing(INPUT_HEIGHT, INPUT_WIDTH, name=f"{self.name}_resizer")
    self.rescaler = tf.keras.layers.Rescaling(scale=1./255, name=f"{self.name}_rescaler")

  def call(self, inputs):
    return self.rescaler(
        self.resizer(inputs)
    )


class Encoder(tf.keras.layers.Layer):
  def __init__(self, latent_dims):
    super().__init__(name="encoder")

    self.latent_dims = latent_dims

    # layers
    self.preprocess = Preprocessor()
    # 128 x 128 x 1
    self.conv1 = Conv2D(filters=32, kernel_size=3, strides=1, padding='same', activation='relu', name='encoder_conv1')
    self.bnorm1 = BatchNormalization(name="encoder_bnorm1")
    self.mpool1 = MaxPool2D(name='encoder_mpool1')

    # 64 x 64 x 32
    self.conv2 = Conv2D(filters=64, kernel_size=3, strides=1, padding='same', activation='relu', name='encoder_conv2')
    self.bnorm2 = BatchNormalization(name="encoder_bnorm2")
    self.mpool2 = MaxPool2D(name='encoder_mpool2')

    # 32 x 32 x 64
    self.conv3 = Conv2D(filters=128, kernel_size=3, strides=1, padding='same', activation='relu', name='encoder_conv3')
    self.bnorm3 = BatchNormalization(name="encoder_bnorm3")
    self.mpool3 = MaxPool2D(name='encoder_mpool3')

    # 16 x 16 x 128
    self.conv4 = Conv2D(filters=256, kernel_size=3, strides=1, padding='same', activation='relu', name='encoder_conv4')
    self.bnorm4 = BatchNormalization(name="encoder_bnorm4")
    self.mpool4 = MaxPool2D(name='encoder_mpool4')

    # 8 x 8 x 256
    self.conv5 = Conv2D(filters=512, kernel_size=3, strides=1, padding='same', activation='relu', name='encoder_conv5')
    self.bnorm5 = BatchNormalization(name="encoder_bnorm5")
    self.mpool5 = MaxPool2D(name='encoder_mpool5')

    # 4 x 4 x 512
    self.flatten = Flatten(name='encoder_flatten')

    self.dense1 = Dense(2 * self.latent_dims, name='encoder_dense1')
    # 2 x self.latent_dims


    self.logvar = Dense(self.latent_dims, name='encoder_logvar')
    self.mu = Dense(self.latent_dims, name='encoder_mu')
    self.sigma = Lambda(lambda x: tf.exp(0.5*x), name='encoder_sigma')
    self.logvar_clip = Lambda(lambda x: tf.clip_by_value(x, -20.0, 5.0), name='logvar_clip')


  def encode(self, inputs, preprocess=True):
    # print the shape of the input
    # print(f"Shape of input to encoder: {inputs.shape}")
    p = self.preprocess(inputs) if preprocess else inputs
    x=self.conv1(p); x=self.bnorm1(x); x=self.mpool1(x)
    x=self.conv2(x); x=self.bnorm2(x);  x=self.mpool2(x)
    x=self.conv3(x); x=self.bnorm3(x);  x=self.mpool3(x)
    x=self.conv4(x); x=self.bnorm4(x);  x=self.mpool4(x)
    x=self.conv5(x); x=self.bnorm5(x);  x=self.mpool5(x)
    x=self.flatten(x)
    x=self.dense1(x)
    # print(f"Shape of output from encoder: {x.shape}")

    logvar = self.logvar(x)
    logvar = self.logvar_clip(logvar)

    return self.mu(x), logvar, self.sigma(logvar), p


  def call(self, inputs):
    return self.encode(inputs)

  def summary(self, input_shape):
    x = tf.keras.layers.Input(shape=input_shape)
    model = tf.keras.Model(inputs=[x], outputs=self.call(x))
    return model.summary()

class Decoder(tf.keras.Model):
    def __init__(self, latent_dims):
        super().__init__(name='decoder')

        self.latent_dims = latent_dims

        # layers
        self.dense1 = Dense(4 * 4 * 512, activation='relu', name='decoder_dense1')
        self.reshape1 = Reshape((4, 4, 512), name='decoder_reshape1')

        # 4 x 4 x 512 -> 8 x 8 x 256
        self.convT1 = Conv2DTranspose(filters=256, kernel_size=3, strides=2, padding='same', activation='relu', name='decoder_convT1')
        self.bnorm1 = BatchNormalization(name="decoder_bnorm1")

        # 8 x 8 x 256 -> 16 x 16 x 128
        self.convT2 = Conv2DTranspose(filters=128, kernel_size=3, strides=2, padding='same', activation='relu', name='decoder_convT2')
        self.bnorm2 = BatchNormalization(name="decoder_bnorm2")

        # 16 x 16 x 128 -> 32 x 32 x 64
        self.convT3 = Conv2DTranspose(filters=64, kernel_size=3, strides=2, padding='same', activation='relu', name='decoder_convT3')
        self.bnorm3 = BatchNormalization(name="decoder_bnorm3")

        # 32 x 32 x 64 -> 64 x 64 x 32
        self.convT4 = Conv2DTranspose(filters=32, kernel_size=3, strides=2, padding='same', activation='relu', name='decoder_convT4')
        self.bnorm4 = BatchNormalization(name="decoder_bnorm4")

        # 64 x 64 x 32 -> 128 x 128 x 1
        self.convT5 = Conv2DTranspose(filters=1, kernel_size=3, strides=2, padding='same', activation='sigmoid', name='decoder_convT5')


        # binary output
        # self.binaryOutput = Lambda(lambda x: tf.cast(x > 0.5, tf.float32), name="decoder_binary_lambda")

    def decode(self, z):
        x = self.dense1(z)
        x = self.reshape1(x)

        x = self.convT1(x)
        x = self.convT2(x)
        x = self.convT3(x)
        x = self.convT4(x)
        x = self.convT5(x)
        # x = self.binaryOutput(x)


        return x

    def call(self, inputs):
        return self.decode(inputs)

    def summary(self, input_shape):
        x = tf.keras.layers.Input(shape=input_shape)
        model = tf.keras.Model(inputs=[x], outputs=self.call(x))
        return model.summary()

class ReconstructionLoss(tf.keras.layers.Layer):
  def __init__(self):
    super(ReconstructionLoss, self).__init__(name="reconstruction_loss")

  def call(self, inputs):
    x = inputs[0]
    recon_x = inputs[1]

    recon_loss = tf.reduce_sum(tf.keras.losses.binary_crossentropy(x, recon_x), axis=[1,2])
    recon_loss = tf.reduce_mean(recon_loss)

    self.add_loss(recon_loss)

    return recon_loss

class KLLoss(tf.keras.layers.Layer):
  def __init__(self, beta=4.0):
    super(KLLoss, self).__init__()

    self.beta = beta

  def call(self, inputs):
    mu = inputs[0]
    logvar = inputs[1]

    kl_loss = -0.5 * tf.reduce_sum(1 + logvar - tf.square(mu) - tf.exp(logvar), axis=1)
    kl_loss = kl_loss * self.beta

    self.add_loss(kl_loss)
    return kl_loss

class Sampler(tf.keras.layers.Layer):
  def __init__(self):
    super().__init__(name="sampler")

  def call(self, inputs):
    mu = inputs[0]
    sigma = inputs[1]

    batch = tf.shape(mu)[0]
    dim = tf.shape(mu)[1]
    epsilon = tf.random.normal(shape=(batch, dim))

    # reparameterize
    output =  mu + tf.multiply(sigma, epsilon)

    # print(f"Shape of output from sampler: {output.shape}")
    return output

class BVAE(tf.keras.Model):
  def __init__(self, latent_dims):
    super().__init__(name="bvae")

    self.latent_dims = latent_dims

    # layers
    self.encoder = Encoder(self.latent_dims)
    self.decoder = Decoder(self.latent_dims)

    self.sampler = Sampler()

    self.reconstruction_loss = ReconstructionLoss()
    self.kl_loss = KLLoss(beta=4.0)

    # trackers
    self.loss_tracker = tf.keras.metrics.Mean(name="loss")
    self.reconstruction_loss_tracker = tf.keras.metrics.Mean(name="reconstruction_loss")
    self.kl_loss_tracker = tf.keras.metrics.Mean(name="kl_loss")

  def get_config(self):
    config = super().get_config()
    config.update({
        "latent_dims": self.latent_dims,
    })
    return config

  @classmethod
  def from_config(cls, config):
    # Extract latent_dims from the config
      latent_dims = config.pop('latent_dims')
      # Remove other keys added by Keras during saving if they are not needed for __init__
      config.pop('name', None)
      config.pop('trainable', None)
      config.pop('dtype', None)
      # Create an instance of the class using the extracted latent_dims
      return cls(latent_dims=latent_dims, **config)



  def call(self, inputs):
    mu, logvar, sigma, x = self.encoder(inputs)
    z = self.sampler([mu, sigma])
    # print(f"Shape of z: {z.shape}")
    recon_x = self.decoder(z)

    kl_loss = self.kl_loss([mu, logvar])
    reconstruction_loss = self.reconstruction_loss([x, recon_x])

    return recon_x, kl_loss, reconstruction_loss

  @property
  def metrics(self):
      return [
          self.loss_tracker,
          self.reconstruction_loss_tracker,
          self.kl_loss_tracker,
      ]

  def train_step(self, data):
    # print(f"Shape of input data in train_step: {data.shape}")

    with tf.GradientTape() as tape:
      recon_x, kl_loss, reconstruction_loss = self(data)
      total_loss = reconstruction_loss + kl_loss

      # update the trackers
      self.loss_tracker.update_state(total_loss)
      self.reconstruction_loss_tracker.update_state(reconstruction_loss)
      self.kl_loss_tracker.update_state(kl_loss)

      # gradients
      grads = tape.gradient(total_loss, self.trainable_weights)
      self.optimizer.apply_gradients(zip(grads, self.trainable_weights))

    return {
        m.name: m.result() for m in self.metrics
    }

  def test_step(self, data):
    recon_x, kl_loss, reconstruction_loss = self(data)
    total_loss = reconstruction_loss + kl_loss
    self.loss_tracker.update_state(total_loss)
    self.reconstruction_loss_tracker.update_state(reconstruction_loss)
    self.kl_loss_tracker.update_state(kl_loss)
    return {
        m.name: m.result() for m in self.metrics
    }

  def encode(self, inputs, preprocess=True):
    return self.encoder.encode(inputs, preprocess=preprocess)

  def decode(self, inputs):
    return self.decoder.decode(inputs)

  def sample(self, mu, sigma):
    return self.sampler([mu, sigma])

  def calculate_reconstruction_loss(self, inputs):
    return self.reconstruction_loss(inputs)

  def calculate_kl_loss(self, inputs):
    return self.kl_loss(inputs)
