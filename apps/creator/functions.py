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


# def gen_frames_from_youtube(url=None, folder='/home/cc/projects/'):
#     # Log start time
#     time_start = time.time()
#
#     # To make a directory for saving video automatically considering all the existing foldernames
#     reg = re.compile(r'^video_')
#     lst = sorted(os.listdir(folder))
#     newlist = filter(reg.match, lst)
#     numbers = [reg.sub('', x).strip() for x in newlist]
#     results = map(int, numbers)
#     results = sorted(results)
#     newfile = results[-1] + 1
#     # Make a directory for the video
#     # If no video's exist as of now, create a folder.
#     if(results == None):
#         os.mkdir("video_1")
#     # Create a folder according to the files that are already present.   
#     os.mkdir("video_" + str(newfile))
#
#     file_loc = folder + "video_" + str(newfile) + "/video_" + str(newfile) + ".mp4"
#     # Download from local video file
#     if (url):
#         print("Downloading Youtube Video")
#         os.system("youtube-dl -o " + file_loc + " -f mp4 " + url)
#         cap = cv2.VideoCapture(file_loc)
#     else:
#         print("This is where I should raise an error. --EXCEPTION HANDLING--")
#
#     video_length = int(cap.get(cv2.CV_CAP_PROP_FRAME_COUNT)) - 1
#     print("Number of frames: ", video_length)
#     count = 0
#     print ("Converting video..\n")
#     while cap.isOpened():
#         ret,frame = cap.read()
#
#         cv2.imwrite(folder + "video_" + str(newfile) + "/%d.jpg" % (count+1), frame)
#         count = count + 1
#         if (count > (video_length-1)):
#             time_end = time.time()
#             cap.release()
#             print "Done extracting frames.\n%d frames extracted" %count
#             print "It took %d seconds for conversion." %(time_end-time_start)
#             break
            

# def capture_from_youtube(capture_time):
#
#     video = pafy.new(url)
#     best  = video.getbest(preftype="mp4")
#     #documentation: https://pypi.org/project/pafy/
#
#     cap = cv2.VideoCapture(best.url)
#     check, frame = cap.read()
#     frame_rate = cap.get(cv2.CAP_PROP_FPS)
#     print ('check, frame, frame_rate: ', check, frame, frame_rate)
#
#
#     if cap is None or not cap.isOpened():
#         print('Warning: unable to open video source: ', url)
#
#     # (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
#     # if int(major_ver) < 3:
#     #     fps = cap.get(cv2.cv.CV_CAP_PROP_FPS)
#     #     print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
#     # else:
#     #     fps = cap.get(cv2.CAP_PROP_FPS)
#     #     print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))
#
#     frameCount = int(frame_rate * capture_time)
#     print(f'frame count is {frameCount}')
#
#     # enhancer = ImageEnhance.Contrast(image)
#     # image = enhancer.enhance(contrast_factor)
#     # array = np.array(image)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
#
#     frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#
#     print(f'camera resolution is: {frameWidth} x {frameHeight}')
#
#     led_array = []
#     fc = 0
#     ret = True
#
#     # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
#     # cv2.resizeWindow('image', 600, 600)
#     while (fc < frameCount and ret):
#
#         ret, frame = cap.read()
#         if mirrow == True:
#             frame = cv2.flip(frame, 1)
#         if frame is None:
#             print('no frame captured, aborting')
#             break
#         resized = np.array(cv2.resize(frame, dsize=(led_hor, led_ver), interpolation=cv2.INTER_CUBIC))
#         # im_1_22 = 255.0 * (resized / 255.0)**(1 / 2.2)
#         # im_22 = 255.0 * (resized / 255.0)**2.2
#         # resized = np.concatenate((im_1_22, resized, im_22), axis=1)
#
#         # image_yuv = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV)
#         # image_yuv[:, :, 0] = cv2.equalizeHist(image_yuv[:, :, 0])
#         # resized = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)
#
#         resized = apply_brightness_contrast(resized, 0, 64)
#         line_up = resized[0, :]
#         line_down = resized[led_ver - 1, :]
#         line_left = resized[:, 0]
#         line_right = resized[:, led_hor - 1]
#
#         # cv2.imshow('original', frame)
#         # cv2.imshow('image', white_image)
#
#         actual_led_array = np.concatenate((line_right[::-1], line_up[::-1], line_left[::1], line_down[::1]))
#         led_array.append(actual_led_array)
#
#         if live:
#             for i in range(0, num_pixels - 1):
#                 pixels[i] = actual_led_array[i].astype(int)
#             pixels.show()
#         fc += 1
#         print (fc)
#
#     cap.release()
#     cv2.destroyAllWindows()
#
#     return np.array(led_array)

def gen_frames():  # generate frame by frame from video
    video = pafy.new(url)
    best  = video.getbest(preftype="mp4")
    #documentation: https://pypi.org/project/pafy/

    
    while True:
        cap = cv2.VideoCapture(best.url)
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

def generate_frames_from_youtube(url='https://www.youtube.com/watch?v=wr-rIz1-VG4'):
    video = pafy.new(url)
    best  = video.getbest(preftype="mp4")
    #documentation: https://pypi.org/project/pafy/
    
    cap = cv2.VideoCapture(best.url)
    
    # Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")
    
    # Read until video is completed
    while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            
            # Display the resulting frame
            # cv2.imshow('Frame',frame)
            
            # transform to jpeg
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            
    
        # Break the loop
        else: 
            break
    
    cap.release()
    cv2.destroyAllWindows()
        
generate_frames_from_youtube(url='https://www.youtube.com/watch?v=wr-rIz1-VG4')