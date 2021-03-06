
import os
import csv
import os.path
from os import listdir
from os.path import isfile, join
from PIL import Image
import matplotlib.pyplot as plt

import numpy as np

import util.const as const
import util.tile as tile
import util.color as color
import util.scale as scale
import util.fancy_pca as fancy_pca
import cv2
from random import randrange


def get_car_ids(img_names):
    '''
    parse car ids from full image names
    '''
    car_ids = [ img_name.split('_')[0] for img_name in img_names ]
    car_ids = list(set(car_ids))
    print("There are {} car ids out of {} images. ".format(len(car_ids), len(img_names)))
    return car_ids

def get_img_names_from_car_ids(car_ids):
    '''
    generate image names from car ids
    '''
    img_names = []

    for car_id in car_ids:
        for i in range(1, 17):
            img_name = car_id + '_{:02d}'.format(i)
            img_names.append(img_name)

    return img_names

def load_imageset(imageset_path):
    '''
    get a list of img names from the csv file at <imageset_path>
    '''
    img_names = []
    with open(imageset_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            img_names.append(row[0])

    img_names.sort()
    return img_names

def load_train_imageset():
    '''
    get the list of img names for train split
    '''
    return load_imageset(const.TRAIN_IMAGESET_PATH)

def load_val_imageset():
    '''
    get the list of img names for validation split
    '''
    return load_imageset(const.VAL_IMAGESET_PATH)

def load_small_imageset():
    small_ids = [
        '0d53224da2b7',
    ]
    small_img_names = get_img_names_from_car_ids(small_ids)
    return small_img_names

def load_train_image(data_dir, img_name,
                     is_hflip=False, hshift=0, vshift=0, rotate=0, scale_size=0,
                     is_color_trans=False, is_fancy_pca_trans=False, is_edge_enh_trans=False,
                     test_time_aug=None, paddings=None, tile_size=None):
    '''
    load a train image
    '''
    img_file_name = tile.get_img_name(img_name)
    img_ext = 'jpg'
    img = load_image_file(data_dir, img_file_name, img_ext, rotate)
    # img.shape: (height, width, 3)

    if is_color_trans :
        img = color.transform(img)
    if is_fancy_pca_trans:
        img = fancy_pca.rgb_shift(img)
    if is_edge_enh_trans:
        img = cv2.detailEnhance(img, sigma_s=5, sigma_r=0.1)

    img = np.moveaxis(img, 2, 0)
    # img.shape: (3, height, width)

    return preprocess(img, img_name, is_hflip, hshift, vshift, scale_size, paddings, tile_size, test_time_aug)

def load_train_mask(data_dir, img_name,
                    is_hflip=False, hshift=0, vshift=0, rotate=0, scale_size=0,
                    test_time_aug=None, paddings=None, tile_size=None):
    '''
    load a train image mask
    '''
    img_file_name = tile.get_img_name(img_name) + '_mask'
    img_ext = 'gif'
    img = load_image_file(data_dir, img_file_name, img_ext, rotate)
    # img.shape: (height, width)

    img = img[np.newaxis, :, :]
    # img.shape: (1, height, width)

    return preprocess(img, img_name, is_hflip, hshift, vshift, scale_size, paddings, tile_size)


def preprocess(img, img_name, is_hflip, hshift, vshift, scale_size, paddings, tile_size, test_time_aug=None):
    '''
    input:
      img: has shape (1, height, width) or (3, height, width)

    preprocess both image and label
    '''

    if test_time_aug:
        #plt.figure()
        #plt.subplot(1, 2, 1)
        #plt.imshow(np.swapaxes(img, 0, 2))
        img = test_time_aug(img)
        #print(img.shape)
        #plt.subplot(1, 2, 2)
        #plt.imshow(np.swapaxes(img, 0, 2))
        #plt.show()

    if is_hflip:
        img = np.swapaxes(img, 0, 2) # img.shape: (width, height, num of channels)

        img = np.flipud(img).copy() # reverse values in the first dimension
        # .copy() is added to fixed the following error:
        # https://discuss.pytorch.org/t/torch-from-numpy-not-support-negative-strides/3663/2

        img = np.swapaxes(img, 0, 2)  # img.shape: (num of channels, height, width)

    if hshift != 0:
        img = np.roll(img, hshift,axis=2).copy()

    if vshift != 0:
        img = np.roll(img, vshift, axis=1).copy()

    if scale_size > 0 :
        img = scale.resize_image(img, scale_size).copy()

    if paddings is not None:
        img = tile.pad_image(img, paddings)

    if tile_size is not None:
        img = tile.get_tile(img, img_name, tile_size)

    return img

def load_image_file(data_dir, img_name, img_ext, rotate):
    '''
    load image file (.gif or .jpg)
    '''
    img_path = os.path.join(data_dir, img_name + '.' + img_ext)
    img = Image.open(img_path).rotate(rotate)

    img = np.asarray(img) # img.shape: (height, width, 3) or (height, width) if mask

    return img

def get_filename(path):
    '''
    get only file name from file path
    '''
    base = os.path.basename(path)
    filename, ext = os.path.splitext(base)[0], os.path.splitext(base)[1]
    return filename, ext

def list_img_in_dir(dir):
    '''
    get a list of file names of all images in the directory
    '''
    onlyfiles = [ f for f in listdir(dir) if isfile(join(dir, f))]
    onlyjpgs = [os.path.splitext(f)[0] for f in onlyfiles if os.path.splitext(f)[1] == '.jpg']
    return onlyjpgs

def list_csv_in_dir(dir):
    '''
    get a list of file names of all csv files in the directory
    '''
    onlyfiles = [ f for f in listdir(dir) if isfile(join(dir, f))]
    onlycsvs = [os.path.splitext(f)[0] for f in onlyfiles if os.path.splitext(f)[1] == '.csv']
    return onlycsvs

def list_npy_in_dir(dir):
    '''
    get a list of file names of all .npy files in the directory
    '''
    onlyfiles = [ f for f in listdir(dir) if isfile(join(dir, f))]
    onlynpys = [os.path.splitext(f)[0] for f in onlyfiles if os.path.splitext(f)[1] == '.npy']
    return onlynpys

def get_img_shape(image_path):
    '''
    get the size of a image file
    '''
    im = Image.open(image_path)
    width, height =  im.size
    return (height, width)
