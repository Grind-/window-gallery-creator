'''
Created on 10.08.2022

@author: jhirte
'''
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
import os
import re
from threading import Thread, Event

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
url = 'https://www.youtube.com/watch?v=wr-rIz1-VG4'

stop_play_event = Event()
reset_play_event = Event()

frame_out = b''

def capture_from_youtube(capture_time):

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

class VideoToLed():
    def __init__(self):
        self.is_playing = False
        self.restart_flag = False
        self.stop_flag = False
        self.frame_counter = 0
        self.clip_start_frame = 0
        self.clip_end_frame = 100000
        self.clip_duration = 0
        self.cap = cv2.VideoCapture()
    
    def open_youtube_video(self, url: str):
        self.release()
        video = pafy.new(url)
        best  = video.getbest(preftype="mp4")
        all_streams = video.allstreams  
        mp4_list = [] 
        for stream in all_streams:
            if stream.extension=="mp4" and stream.mediatype=="normal":
                mp4_list.append(stream)
        lowest = getlowest(videostreams=mp4_list, preftype="mp4")
        self.clip_duration = video.length       
        #documentation: https://pypi.org/project/pafy/
        
        self.cap = cv2.VideoCapture(lowest.url)
        if (self.cap.isOpened()== False): 
            print("Error opening video stream or file")
        
    def stop(self):
        self.stop_flag = True
        self.is_playing = False
        self.cap.release()
        
    def restart(self):
        self.restart_flag = True
     
    def release(self):   
        self.cap.release()
        
    def set_start_sec(self, sec: int):
        frame_duration = self.clip_duration / self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.clip_start_frame = sec/frame_duration
    
    def generate_frames(self):
        # Capture frame-by-frame
        self.is_playing = True
        while True:
            self.frame_counter += 1
            ret, frame = self.cap.read()
            if ret == True:
                if self.stop_flag:
                    self.release()
                    break
                if self.frame_counter == self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or self.frame_counter == self.clip_end_frame or self.restart_flag:
                    self.frame_counter = self.clip_start_frame #Or whatever as long as it is the same as next line
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.restart_flag = False
                # transform to jpeg
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                
                yield  (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            else: 
                return None

def getlowest(videostreams, preftype="any", ftypestrict=True, vidonly=False):
        """
        Return the highest resolution video available.

        Select from video-only streams if vidonly is True
        """
        streams = videostreams

        if not streams:
            return None

        def _sortkey(x, key3d=0, keyres=0, keyftype=0):
            """ sort function for max(). """
            key3d = "3D" not in x.resolution
            keyres = int(x.resolution.split("x")[0])
            keyftype = preftype == x.extension
            strict = (key3d, keyftype, keyres)
            nonstrict = (key3d, keyres, keyftype)
            return strict if ftypestrict else nonstrict

        r = min(streams, key=_sortkey)

        if ftypestrict and preftype != "any" and r.extension != preftype:
            return None

        else:
            return r    