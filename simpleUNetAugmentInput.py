#macro to produce several plots to help understand this dataset.
#thanks to:
#-Kjetil Amdal-Saevik and his Kernel "Keras U-Net starter - LB 0.277"
#-the github repo unet-tensorflow-keras
import os
import sys
import random
import warnings

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from tqdm import tqdm
from itertools import chain
from skimage.io import imread, imshow, imread_collection, concatenate_images
from skimage.transform import resize
from skimage.morphology import label
from skimage.color import rgb2gray

from keras.models import Model, load_model
from keras.layers import Input
from keras.layers.core import Dropout, Lambda
from keras.layers.convolutional import Conv2D, Conv2DTranspose
from keras.layers.pooling import MaxPooling2D
from keras.layers.merge import concatenate
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from keras import backend as K

import tensorflow as tf

from modelZoo import UNet

def combineGenerator(gen1, gen2):
    while True:
        yield(gen1.next(),gen2.next())


# Load np array for input data and masks
X_train = np.load('inputImagesHRes.npy')
Y_train = np.load('inputMaskHRes.npy')

batch=4

np.random.seed(1337)
np.random.shuffle(X_train)
np.random.seed(1337)
np.random.shuffle(Y_train)

# Create a generator to applt data augmentations as we train

# we create two instances with the same arguments
data_gen_args = dict(horizontal_flip=True,
                     vertical_flip=True,
                     #rotation_range=45.,
                     cval=0,
                     #shear_range=0.2,
                     #width_shift_range=0.1,
                     #height_shift_range=0.1,
                     zoom_range=[0.8,1],
                     fill_mode='constant')


seed=1
image_datagen = ImageDataGenerator(**data_gen_args)
mask_datagen = ImageDataGenerator(**data_gen_args)
image_datagen_val = ImageDataGenerator()
mask_datagen_val = ImageDataGenerator()

# Provide the same seed and keyword arguments to the fit and flow methods
image_generator = image_datagen.flow(X_train[:int(X_train.shape[0]*0.9)], batch_size=batch, seed=seed)
print (X_train[:int(X_train.shape[0]*0.9)].shape)
mask_generator = mask_datagen.flow(Y_train[:int(X_train.shape[0]*0.9)], batch_size=batch, seed=seed)
image_generator_val = image_datagen_val.flow(X_train[int(X_train.shape[0]*0.9):], seed=seed)
mask_generator_val = mask_datagen_val.flow(Y_train[int(X_train.shape[0]*0.9):], seed=seed)

# Combine generators into one which yields image and masks
train_generator = combineGenerator(image_generator, mask_generator)
validation_generator = combineGenerator(image_generator_val, mask_generator_val)

# Compile the model
model = UNet().create_model(img_shape=X_train[0].shape, num_class=1)
model.compile(optimizer='adam', loss='binary_crossentropy')
model.summary()

# Fit model
earlystopper = EarlyStopping(patience=100, verbose=1)
checkpointer = ModelCheckpoint('model-dsbowl2018-1-augment.h5', verbose=1, save_best_only=True)
results = model.fit_generator(train_generator,
                              validation_data=validation_generator, steps_per_epoch=len(X_train)/batch,
                              epochs=5000, validation_steps=0.1*len(X_train),
                              callbacks=[earlystopper, checkpointer])
