'''
Created on 06.08.2022

@author: jhirte
'''
# Imports
from io import BytesIO
import pickle
import platform
import string
import sys
import time

from PIL import Image, ImageEnhance
import cv2
import pafy
import requests

import numpy as np


my_os = platform.system()
print("OS in my system : ", my_os)


def returnCameraIndexes():
    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        if my_os == 'Windows':
            cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(camera)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
        i -= 1
    return arr


# Constants for LED strip and image processing
pixel_pin = 13
# pixel_pin = board.D18
num_pixels = 64
led_hor = 16  # horizontal number of LEDs
led_ver = 16  # vertical number of LEDs
reduce_color_bit = 17  # decrease color bits factor
contrast_factor = 10  # increase contrast
mirrow = True
frame_rate = 30
capture_time = 20  # length of video in seconds
camera = 0
live = False
resolution = (320, 240)

if len(sys.argv) > 1:
    if sys.argv[1]:
        camera = sys.argv[1]
if len(sys.argv) > 2:
    if sys.argv[2]:
        live_string = sys.argv[2]
        if live_string == 'true' or live_string == 'True':
            live = True
        else:
            live = False
# print('detected camera indexes', returnCameraIndexes())
# print('selected camera ', camera)


def apply_brightness_contrast(input_img, brightness = 0, contrast = 0):
    
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow)/255
        gamma_b = shadow
        
        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()
    
    if contrast != 0:
        f = 131*(contrast + 127)/(127*(131-contrast))
        alpha_c = f
        gamma_c = 127*(1-f)
        
        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf

def capture_from_youtube(capture_time, url):
   
    video = pafy.new(url)
    best  = video.getbest(preftype="mp4")
    #documentation: https://pypi.org/project/pafy/

    cap = cv2.VideoCapture(best.url)
    check, frame = cap.read()
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    print ('check, frame, frame_rate: ', check, frame, frame_rate)

    
    if cap is None or not cap.isOpened():
        print('Warning: unable to open video source: ', url)

    # (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    # if int(major_ver) < 3:
    #     fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
    #     print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    # else:
    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #     print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    frameCount = int(frame_rate * capture_time)
    print(f'frame count is {frameCount}')

    # enhancer = ImageEnhance.Contrast(image)
    # image = enhancer.enhance(contrast_factor)
    # array = np.array(image)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f'camera resolution is: {frameWidth} x {frameHeight}')

    led_array = []
    fc = 0
    ret = True

    # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    # cv2.resizeWindow('image', 600, 600)
    while (fc < frameCount and ret):

        ret, frame = cap.read()
        if mirrow == True:
            frame = cv2.flip(frame, 1)
        if frame is None:
            print('no frame captured, aborting')
            break
        resized = np.array(cv2.resize(frame, dsize=(led_hor, led_ver), interpolation=cv2.INTER_CUBIC))
        # im_1_22 = 255.0 * (resized / 255.0)**(1 / 2.2)
        # im_22 = 255.0 * (resized / 255.0)**2.2
        # resized = np.concatenate((im_1_22, resized, im_22), axis=1)

        # image_yuv = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV)
        # image_yuv[:, :, 0] = cv2.equalizeHist(image_yuv[:, :, 0])
        # resized = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)

        resized = apply_brightness_contrast(resized, 0, 64)
        line_up = resized[0, :]
        line_down = resized[led_ver - 1, :]
        line_left = resized[:, 0]
        line_right = resized[:, led_hor - 1]

        # cv2.imshow('original', frame)
        # cv2.imshow('image', white_image)

        actual_led_array = np.concatenate((line_right[::-1], line_up[::-1], line_left[::1], line_down[::1]))
        led_array.append(actual_led_array)

        if live:
            for i in range(0, num_pixels - 1):
                pixels[i] = actual_led_array[i].astype(int)
            pixels.show()
        fc += 1
        print (fc)

    cap.release()
    cv2.destroyAllWindows()

    return np.array(led_array)


def capture(capture_time, live=False, arduino=False):
    if live:
        import board
        import neopixel
        pixel_pin = board.D18
        pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False)
    if my_os == 'Windows':
        cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera)

    if cap is None or not cap.isOpened():
        print('Warning: unable to open video source: ', camera)

    # (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    # if int(major_ver) < 3:
    #     fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
    #     print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    # else:
    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #     print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    cap.set(cv2.CAP_PROP_FPS, frame_rate)
    frameCount = int(frame_rate * capture_time)
    print(f'frame count is {frameCount}')

    # enhancer = ImageEnhance.Contrast(image)
    # image = enhancer.enhance(contrast_factor)
    # array = np.array(image)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f'camera resolution is: {frameWidth} x {frameHeight}')

    led_array = []
    fc = 0
    ret = True

    # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    # cv2.resizeWindow('image', 600, 600)
    while (fc < frameCount and ret):

        ret, frame = cap.read()
        if mirrow == True:
            frame = cv2.flip(frame, 1)
        if frame is None:
            print('no frame captured, aborting')
            break
        resized = np.array(cv2.resize(frame, dsize=(led_hor, led_ver), interpolation=cv2.INTER_CUBIC))
        # im_1_22 = 255.0 * (resized / 255.0)**(1 / 2.2)
        # im_22 = 255.0 * (resized / 255.0)**2.2
        # resized = np.concatenate((im_1_22, resized, im_22), axis=1)

        # image_yuv = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV)
        # image_yuv[:, :, 0] = cv2.equalizeHist(image_yuv[:, :, 0])
        # resized = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)

        resized = apply_brightness_contrast(resized, 0, 64)
        line_up = resized[0, :]
        line_down = resized[led_ver - 1, :]
        line_left = resized[:, 0]
        line_right = resized[:, led_hor - 1]

        # cv2.imshow('original', frame)
        # cv2.imshow('image', white_image)

        actual_led_array = np.concatenate((line_right[::-1], line_up[::-1], line_left[::1], line_down[::1]))
        led_array.append(actual_led_array)

        if live:
            for i in range(0, num_pixels - 1):
                pixels[i] = actual_led_array[i].astype(int)
            pixels.show()
        fc += 1
        print (fc)

    cap.release()
    cv2.destroyAllWindows()

    return np.array(led_array)


def play(filename: string, fps):
    # import neopixel
    pkl_file = open(filename, 'rb')
    array = pickle.load(pkl_file)
    pkl_file.close()

    led_num = array[1].size
    pixels = neopixel.NeoPixel(pixel_pin, led_num, brightness=0.2, auto_write=False)
    sec = 1 / fps

    fc = 0
    beginningOfTime = time.clock()
    start = time.clock()
    goAgainAt = start + sec
    while fc < len(array):
        print("Loop #%d at time %f" % (fc, time.clock() - beginningOfTime))
        print(array[i])
        for i in range(0, num_pixels - 1):
            pixels[i] = array[i]
        pixels.show()
        fc += 1
        if time.clock() > goAgainAt:
            print("Oops, missed an iteration")
            goAgainAt += sec
            continue
        # Otherwise, wait for next interval
        timeToSleep = goAgainAt - time.clock()
        goAgainAt += sec
        time.sleep(timeToSleep)


def main():
    # time = input("Enter the video time in seconds: ")
    time = 10
    print(time)
    first_round = True
    while True:
        array_actual = capture_from_youtube(capture_time=int(time), url='https://www.youtube.com/watch?v=e3con85nqLY')
        if first_round == True:
            array = array_actual
            first_round = False
        else:
            array = np.add(array, array_actual)
        #continue_capturing = input("Another round? Press Enter. If you got enough, enter 'q' and press enter: ")
        #if continue_capturing == 'q':
        #    break

    filename = input("Enter Filename: ")
    if filename != "":
        print('No filename given, will not save to disc')
        output = open(filename, 'wb')
        pickle.dump(array, output)
        output.close()

    # play(filename, frame_rate)


if __name__ == "__main__":
    main()