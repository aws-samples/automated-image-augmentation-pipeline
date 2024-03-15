# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Importing Relevant Libraries and Packages
import boto3
import numpy as np
import scipy
from scipy.ndimage import rotate
from PIL import Image
import io
import urllib.parse
import os


def show_img(img, ax):
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.imshow(img)


def plot_grid(imgs, nrows, ncols, figsize=(10, 10)):
    assert len(imgs) == nrows * ncols, f"Number of images should be {nrows}x{ncols}"
    # _, axs = plt.subplots(nrows, ncols, figsize=figsize)
    axs = axs.flatten()
    for img, ax in zip(imgs, axs):
        show_img(img, ax)


def random_crop(img, crop_size=(10, 10)):
    assert (
        crop_size[0] <= img.shape[0] and crop_size[1] <= img.shape[1]
    ), "Crop size should be less than image size"
    img = img.copy()
    w, h = img.shape[:2]
    x, y = np.random.randint(h - crop_size[0]), np.random.randint(w - crop_size[1])
    img = img[y : y + crop_size[0], x : x + crop_size[1]]
    return img


def rotate_img(img, angle, bg_patch=(5, 5)):
    assert len(img.shape) <= 3, "Incorrect image shape"
    rgb = len(img.shape) == 3
    if rgb:
        bg_color = np.mean(img[: bg_patch[0], : bg_patch[1], :], axis=(0, 1))
    else:
        bg_color = np.mean(img[: bg_patch[0], : bg_patch[1]])
    img = rotate(img, angle, reshape=False)
    mask = [img <= 0, np.any(img <= 0, axis=-1)][rgb]
    img[mask] = bg_color
    return img


def gaussian_noise(img, mean=0, sigma=0.03):
    img = img.copy()
    noise = np.random.normal(mean, sigma, img.shape)
    mask_overflow_upper = img + noise >= 1.0
    mask_overflow_lower = img + noise < 0
    noise[mask_overflow_upper] = 1.0
    noise[mask_overflow_lower] = 0
    img += noise
    return img


def distort(img, orientation="horizontal", func=np.sin, x_scale=0.05, y_scale=5):
    assert orientation[:3] in [
        "hor",
        "ver",
    ], "dist_orient should be 'horizontal'|'vertical'"
    assert func in [np.sin, np.cos], "supported functions are np.sin and np.cos"
    assert 0.00 <= x_scale <= 0.1, "x_scale should be in [0.0, 0.1]"
    assert (
        0 <= y_scale <= min(img.shape[0], img.shape[1])
    ), "y_scale should be less then image size"
    img_dist = img.copy()

    def shift(x):
        return int(y_scale * func(np.pi * x * x_scale))

    for c in range(3):
        for i in range(img.shape[orientation.startswith("ver")]):
            if orientation.startswith("ver"):
                img_dist[:, i, c] = np.roll(img[:, i, c], shift(i))
            else:
                img_dist[i, :, c] = np.roll(img[i, :, c], shift(i))

    return img_dist


def generate_augmented_images(original_img, NUM_OF_IMAGES_GENERATED):

    # Insert your image augmentation logic here 

    print("Image augmentation completed!")
    return imgs_distorted


def upload_results(augmented_image_array, OUTPUT_BUCKET, file_name):
    for i in range(0, len(augmented_image_array) - 1):
        filename = file_name.split(".")[0] + "-augmented-" + str(i) + ".jpg"
        new_image = augmented_image_array[i]
        new_image = new_image[:, :, ::-1]
        im = Image.fromarray(new_image)
        im.save("/tmp/" + filename)

        with open("/tmp/" + filename, "rb") as f:
            a = f.read()
            byte_stream = io.BytesIO(a)
            s3 = boto3.client("s3")
            s3.upload_fileobj(byte_stream, OUTPUT_BUCKET, filename)
            print("Uploaded image: ", filename)


def lambda_handler(event, context):
    if event:
        key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
        file_name = key.split("/")[-1]
        bucket = event["Records"][0]["s3"]["bucket"]["name"]

        s3 = boto3.resource("s3")
        bucket = s3.Bucket(bucket)
        image = bucket.Object(key)
        img_data = image.get().get("Body").read()
        local_image = Image.open(io.BytesIO(img_data))
        local_path = "/tmp/" + key
        local_image.save(local_path, "JPEG")
        img = np.asarray(Image.open(local_path))

        augmented_image_array = generate_augmented_images(
            img, int(os.environ["NUM_OF_IMAGES_GENERATED"])
        )
        upload_results(augmented_image_array, os.environ["OUTPUT_BUCKET"], file_name)

        print("Image Augmentation Completed!")
