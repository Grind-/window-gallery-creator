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
import cv2
import pafy

import numpy as np
from apps.util.youtube_downloader import YoutubeDownloader
from scipy.ndimage import interpolation
import os.path

# Constants for LED strip and image processing
pixel_pin = 13
# pixel_pin = board.D18
num_pixels = 64
led_hor = 16  # horizontal number of LEDs
led_ver = 16  # vertical number of LEDs
reduce_color_bit = 17  # decrease color bits factor
contrast_factor = 10  # increase contrast
mirrow = False
frame_rate = 30
capture_time = 20  # length of video in seconds
camera = 0
live = False
resolution = (320, 240)
download_destination = 'apps/static/assets/.temp'


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
        self.led_array = []
        self.is_playing = False
        self.restart_flag = False
        self.stop_flag = False
        self.frame_counter = 0
        self.clip_start_frame = 0
        self.clip_end_frame = 100000
        self.clip_width = 0
        self.clip_height = 0
        self.rect_top = 0
        self.rect_bot = 0
        self.rect_left = 0
        self.rect_right = 0
        self.rect_thickness = 2
        self.clip_duration = 0
        self.frame_count = 0
        self.fps = 0
        self.cap = cv2.VideoCapture()
        self.video_name = ''
        self.led_hor = 25
        self.led_ver = 30
        self.pause_flag = False
        self.record_flag = False
        
    def get_clip_duration(self):
        return self.clip_duration
    
    def open_video(self):
        
        self.clip_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.clip_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) 
        self.fps = self.cap.get(cv2. CAP_PROP_FPS) # OpenCV2 version 2 used "CV_CAP_PROP_FPS"
        self.frame_count = int(self.cap.get(cv2. CAP_PROP_FRAME_COUNT))
        self.clip_duration = self.frame_count/self.fps
        if (self.cap.isOpened()== False): 
            print("Error opening video stream or file")
            
    def open_youtube_video(self, url: str):
        video = pafy.new(url)
        video_length = video.length
        if video_length > 300:
            return 'video is too long, choose one with less than 5 minutes'
        downloader = YoutubeDownloader()
        downloader.choose_destination(download_destination)
        self.video_name = downloader.download_video(url, 'low')
        self.release()
        self.cap = cv2.VideoCapture(download_destination+'/'+self.video_name)
        self.open_video()
        
    def open_video_from_file(self, path, filename):
        filepath = os.path.join(path, filename)
        self.cap = cv2.VideoCapture(filepath)
        self.video_name = filename
        self.open_video()
        
    def record(self):
        self.led_array = []
        self.record_flag = True
        
    def stop_record(self):
        self.pause()
        self.record_flag = False
        
    def pause(self):
        self.pause_flag = True
        
    def play(self):
        self.pause_flag = False
        
    def stop(self):
        self.record_flag = False
        self.stop_flag = True
        self.is_playing = False
        self.cap.release()
        
    def restart(self):
        self.restart_flag = True
     
    def release(self):   
        self.cap.release()
        
    def set_rectangle(self, bot: int, top: int, left: int, right: int, thickness: int):
        if top < self.clip_height - self.rect_bot:
            self.rect_top = top + int(self.rect_thickness/2)
        if self.clip_height + bot > self.rect_top:
            self.rect_bot = bot + int(self.rect_thickness/2)
        if self.clip_width - right > self.rect_left:
            self.rect_right = right + int(self.rect_thickness/2)
        if left < self.clip_width - self.rect_right:
            self.rect_left = left + int(self.rect_thickness/2)
        if thickness and thickness > 2:
            self.rect_thickness = thickness
 
    def set_start_end_sec(self, start_sec: int, end_sec: int):
        if end_sec and end_sec > start_sec:
            self.clip_end_frame = int(self.fps*end_sec)-1
        if start_sec and start_sec < end_sec:
            self.clip_start_frame = self.fps*start_sec
        from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
        ffmpeg_extract_subclip(download_destination+'/'+self.video_name, self.clip_start_frame/self.fps, 
                               self.clip_end_frame/self.fps, targetname=download_destination+'/cut'+self.video_name)

        self.cap = cv2.VideoCapture(download_destination+'/cut'+self.video_name)
        self.frame_count = int(self.cap.get(cv2. CAP_PROP_FRAME_COUNT))
        self.clip_duration = self.frame_count/self.fps
    
    def start(self):
        # Capture frame-by-frame
        self.is_playing = True
        while True:
            if self.pause_flag == False:
                if self.stop_flag:
                        self.release()
                        break
                if self.frame_counter >= self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or self.frame_counter >= self.clip_end_frame-1 or self.restart_flag:
                    self.frame_counter = self.clip_start_frame #Or whatever as long as it is the same as next line
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.restart_flag = False
                        
                time.sleep(1/self.fps)
                self.frame_counter += 1
                ret, video_frame = self.cap.read()
                
                if ret == True:
                    
                    # create led arrays and frame
                    led_arrays = self.generate_led_arrays(video_frame)
                    led_frame = self.generate_led_image(led_arrays)

                    # create rectangle
                    rect_start_point = (self.rect_left, self.rect_top)
                    rect_end_point = (self.clip_width - self.rect_right, self.clip_height - self.rect_bot)
                    rect_thickness = self.rect_thickness
                    color = (255, 0, 0)
                    overlay = video_frame.copy()
                    alpha = 0.4
                    overlay = cv2.rectangle(overlay, rect_start_point, rect_end_point, color, rect_thickness)
                    video_frame = cv2.addWeighted(overlay, alpha, video_frame, 1 - alpha, 0)
                    
                    # stacking both frames
                    frame = np.vstack((video_frame, led_frame))
                    
                    # transform to jpeg
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    
                    yield  (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
                else: 
                    return None
            
    def generate_led_arrays(self, frame):
        rt = self.rect_thickness
        
        if self.rect_bot - rt/2 >= 0:
            frame_crop_bot = int(self.rect_bot + rt/2)
        else:
            frame_crop_bot = 0
            
        if self.clip_height - self.rect_top + rt/2 <= self.clip_height:
            frame_crop_top = int(self.clip_height - self.rect_top + rt/2)
        else:
            frame_crop_top = self.clip_height
            
        if self.rect_left - rt/2 >= 0:
            frame_crop_left = int(self.rect_left - rt/2)
        else:
            frame_crop_left = 0
            
        if self.clip_width - self.rect_right + rt/2 <= self.clip_width:
            frame_crop_right = int(self.clip_width - self.rect_right + rt/2)
        else:
            frame_crop_right = self.clip_width
        
        frame = frame[int(self.clip_height - frame_crop_top-rt/2) : int(self.clip_height - frame_crop_bot+rt/2), 
                          int(frame_crop_left+rt/2) : int(frame_crop_right-rt/2)]

        
        resized_hor = np.array(cv2.resize(frame, 
                                          dsize=(self.led_hor, int(self.clip_height/self.rect_thickness)), 
                                          interpolation=cv2.INTER_CUBIC))
        resized_ver = np.array(cv2.resize(frame, 
                                          dsize=(int(self.clip_width/self.rect_thickness), self.led_ver), 
                                          interpolation=cv2.INTER_CUBIC))

        # cv2.namedWindow('hor')
        # cv2.imshow( 'hor', resized_hor)
        # cv2.namedWindow('ver')
        # cv2.imshow( "ver", resized_ver)
        # cv2.namedWindow('Frame')
        # cv2.imshow( "Frame", frame)
        # if cv2.waitKey(25) & 0xFF == ord('q'):
        #     pass
        # if mirrow == True:
        #     frame = cv2.flip(frame, 1) 


        line_top = resized_hor[-1, :]
        line_bot = resized_hor[0, :]
       
        line_left = resized_ver[:, 0]
        line_right = resized_ver[:, -1]
        
        if self.record_flag == True:
            self.led_array.append(np.stack([np.flip(line_bot), 
                                           np.flip(line_left), 
                                           line_top,   
                                           line_right]))
            
        return [line_top, line_bot, line_left, line_right]
     
    def generate_led_image(self, led_arrays: []):
        size_horizontal = led_arrays[0].shape[0]
        size_vertical = led_arrays[2].shape[0]
        img = np.zeros([size_vertical,size_horizontal,3],dtype=np.uint8)
        img.fill(5) # or img[:] = 255
        
        # adding light effect to shine into the center of the image
        for i in range (2):
            img[-1-i, :] =  led_arrays[0]/i
            img[i, :] = led_arrays[1]/i
            img[:, -1-i] = led_arrays[3]/i
            img[:, i] = led_arrays[2]/i
        
        img = cv2.resize(img[1:size_vertical-1, 1:size_horizontal-1], 
                         dsize=(self.clip_width, self.clip_height), interpolation=cv2.INTER_CUBIC)
        return img