
import os
import csv
import os.path
from os import listdir
from os.path import isfile, join
from PIL import Image

import numpy as np

def get_car_ids(img_names):
    car_ids = [ img_name.split('_')[0] for img_name in img_names ]
    car_ids = list(set(car_ids))
    print("There are {} car ids out of {} images. ".format(len(car_ids), len(img_names)))
    return car_ids

def get_img_names_from_car_ids(car_ids):
    img_names = []

    for car_id in car_ids:
        for i in range(1, 17):
            img_name = car_id + '_{:02d}'.format(i)
            img_names.append(img_name)

    return img_names

def load_imageset(imageset_path):
    img_names = []
    with open(imageset_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            img_names.append(row[0])

    img_names.sort()
    return img_names

def load_train_imageset():
    return load_imageset(const.TRAIN_IMAGESET_PATH)

def load_val_imageset():
    return load_imageset(const.VAL_IMAGESET_PATH)

def load_small_imageset():
    small_ids = [
        '00087a6bd4dc',
        '0495dcf27283',
        '0789bed99cb8',
    ]
    small_img_names = get_img_names_from_car_ids(small_ids)
    return small_img_names

def load_img(data_dir, img_name, img_ext):
    img_path = os.path.join(data_dir, img_name + '.' + img_ext)
    img = np.asarray(Image.open(img_path)) # img.shape: (height, width, 3)
    img = np.moveaxis(img, 2, 0) # img.shape: (3, height, width)
    # print('Image {} Shape: {}'.format(img_name, img.shape))
    return img

def load_target(data_dir, img_name, img_ext):
    img_path = os.path.join(data_dir, img_name + '.' + img_ext)
    img = np.asarray(Image.open(img_path)) # img.shape: (height, width)
    # print('Target {} Shape: {}'.format(img_name, img.shape))
    return img

def load_all_train_images(data_dir, img_names):
    img_ext = 'jpg'

    first_img_path = os.path.join(data_dir, img_names[0] + '.' + img_ext)
    img_height, img_width= get_img_shape(first_img_path)
    imgs = np.zeros((len(img_names), 3, img_height, img_width))

    for i, img_name in enumerate(img_names):
        img = load_img(data_dir, img_name, img_ext)
        imgs[i] = img

    return imgs

def load_all_train_masks(data_dir, img_names):
    img_names = [ img_name + '_mask' for img_name in img_names ]
    img_ext = 'gif'

    first_img_path = os.path.join(data_dir, img_names[0] + '.' + img_ext)
    img_height, img_width= get_img_shape(first_img_path)
    imgs = np.zeros((len(img_names), img_height, img_width))

    for i, img_name in enumerate(img_names):
        img = load_target(data_dir, img_name, img_ext)
        imgs[i] = img

    return imgs

def get_filename(path):
    base = os.path.basename(path)
    filename, ext = os.path.splitext(base)[0], os.path.splitext(base)[1]
    return filename, ext

def list_img_in_dir(dir):
    onlyfiles = [ f for f in listdir(dir) if isfile(join(dir, f))]
    onlyjpgs = [os.path.splitext(f)[0] for f in onlyfiles if os.path.splitext(f)[1] == '.jpg']
    return onlyjpgs

def list_csv_in_dir(dir):
    onlyfiles = [ f for f in listdir(dir) if isfile(join(dir, f))]
    onlyjpgs = [os.path.splitext(f)[0] for f in onlyfiles if os.path.splitext(f)[1] == '.csv']
    return onlyjpgs

def get_img_shape(image_path):
    im = Image.open(image_path)
    width, height =  im.size
    return (height, width)
