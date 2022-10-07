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
import struct
import serial
import time
import numpy as np
from apps.util.youtube_downloader import YoutubeDownloader
from scipy.ndimage import interpolation
from json import dumps, JSONEncoder
import os.path
import paho.mqtt.client as mqtt
from matplotlib.colors import rgb2hex
from apps.creator.mqtt import MqttCore

download_destination = 'apps/static/assets/.temp'

config = {}
config['frame_id'] = '0000001'
config['topic_sequence'] = '/frame/' + config['frame_id'] + '/sequence/'
config['topic_frame_connected'] = '/frame_connected/'
config['client_id'] = 'window_gallery'
config['password'] = 'password'
mqtt_client = MqttCore()
mqtt_client.start(config['topic_frame_connected'], None)

class VideoToLed():
    def __init__(self):
        self.led_array = np.array([])
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
        self.led_hor = 50
        self.led_ver = 70
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
            
    def load_youtube_video(self, url: str):
        video = pafy.new(url)
        video_length = video.length
        if video_length > 300:
            return 'video is too long, choose one with less than 5 minutes'
        downloader = YoutubeDownloader()
        downloader.choose_destination(download_destination)
        self.video_name = downloader.download_video(url, 'low')
        return self.video_name
        
    def open_video_from_file(self, path, filename):
        filepath = os.path.join(path, filename)
        self.cap = cv2.VideoCapture(filepath)
        self.video_name = filename
        self.open_video()
        
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
        print('start')
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
        # print('generate_led_arrays')
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
        
        
            
            #resized_ver_hex = [ rgb2hex(resized_ver[i,:]) for i in range(resized_ver.shape[0]) ]
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
            self.led_array.append(np.vstack([np.flip(line_bot), 
                                           np.flip(line_left), 
                                           line_top,   
                                           line_right]))
        
        array = [line_top, line_bot, line_left, line_right]

        return array
     
    def generate_led_image(self, led_arrays: []):
        # print('generate_led_image')
        size_horizontal = led_arrays[0].shape[0]
        size_vertical = led_arrays[2].shape[0]
        img = np.zeros([size_vertical,size_horizontal,3],dtype=np.uint8)
        img.fill(5) # or img[:] = 255
        
        # adding light effect to shine into the center of the image
        for i in range (2):
            img[-1-i, :] =  led_arrays[0]/(i+1)
            img[i, :] = led_arrays[1]/(i+1)
            img[:, -1-i] = led_arrays[3]/(i+1)
            img[:, i] = led_arrays[2]/(i+1)
        
        img = cv2.resize(img[1:size_vertical-1, 1:size_horizontal-1], 
                         dsize=(self.clip_width, self.clip_height), interpolation=cv2.INTER_CUBIC)
        return img
    
    def stream_to_arduino(self):
        sequence_array = self.get_sequence_array()
        sec = 1 / self.fps
        strand = NeoPixel('COM8')
        fc = 0
        led = 1
        beginningOfTime = time.process_time()
        start = time.process_time()
        goAgainAt = start + sec
        led_count = self.led_hor*2 + self.led_ver*2
        
        while True:
            print("Loop #%d at time %f" % (fc, time.process_time() - beginningOfTime))
            while led < (2*self.led_hor+2*self.led_ver):
                strand.setPixelColor(led, sequence_array[fc][led][0], sequence_array[fc][led][1], sequence_array[fc][led][2])
                # strand.show()
                led += 1
                if led >= led_count:
                    led = 1
                    break
            fc += 1
            if time.process_time() > goAgainAt:
                print("Oops, missed an iteration")
                goAgainAt += sec
                continue
            # Otherwise, wait for next interval
            timeToSleep = goAgainAt - time.process_time()
            goAgainAt += sec
            time.sleep(timeToSleep)
            print(f'time to sleep: {timeToSleep}')

            if fc == len(sequence_array):
                fc = 0
    
    def get_sequence_array(self, hex: bool=False):
        sequence_array = []
        while True:
            if self.frame_counter >= self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                self.frame_counter = self.clip_start_frame #Or whatever as long as it is the same as next line
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                break
            self.frame_counter += 1
            ret, video_frame = self.cap.read()
            if cv2.waitKey(25) & 0xFF == ord('q'):
                pass
            # if mirrow == True:
            #     frame = cv2.flip(frame, 1) 
            print(self.frame_counter)
            if ret == True:
                # create led arrays and frame
                led_arrays = self.generate_led_arrays(video_frame)
                
                led_array = np.concatenate((led_arrays), axis=0)
                led_array_hex = [ rgb2hex(led_array[i,:]/255) for i in range(led_array.shape[0]) ]
                # led_array_pack = struct.pack('%ss' % len(led_array_hex), led_array_hex)
                if hex:
                    # sequence_array = np.concatenate((sequence_array, led_array_hex), axis=None)
                    sequence_array.append(led_array_hex)
                else:
                    # sequence_array = np.concatenate((sequence_array, led_array), axis=None)
                    sequence_array.append(led_arrays)

            else: 
                print(f'lost frame nr {self.frame_counter}')
                continue
        return np.array(sequence_array)
    
    def send_over_mqtt(self, frame_id):
        print('send')
        # sequence_array = self.get_sequence_array()
        # sequence_array = np.array([0]*5000)
        # mqtt_client.publish(config['topic_sequence'], bytearray(sequence_array))
        # mqtt_client.publish(config['topic_sequence'], sequence_array.tobytes())
        mqtt_client.publish(config['topic_sequence'], frame_id)
        
    def save_to_file(self):
        print('send')
        sequence_array = self.get_sequence_array()
        bin_file = os.path.join('apps', 'sequences', 'sequence.bin')
        np_file = os.path.join('apps', 'sequences', 'sequence.npy')
        np.save(np_file, sequence_array)
        with open(bin_file, "wb") as f:
            f.write(sequence_array.tobytes())
            f.close()
        return f
        
    def download_arduino_code(self):
        print('download')
        sequence_array = self.get_sequence_array()
        index = 2
        json_string = dumps(sequence_array, cls=NumpyArrayEncoder)
        
        ino_template_file = os.path.join('apps', 'static', 'assets', 'arduino_template.ino')
        with open(ino_template_file, "r") as f:
            contents = f.readlines()
        
        contents.insert(index, json_string)

        return contents
    
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)
    
class NeoPixel(object):
    # from https://github.com/mdaffin/PyNeoPixel
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(self.port, 115200, timeout=60)
        self.command_count = 0
        

    def setPixelColor(self, pixel, red, green, blue):
        message = struct.pack('>HBBB', pixel, red, green, blue)
        self.command_count += 1
        if self.command_count >=255:
            self.command_count = 0
        #print(f'message: {message}')
        self.ser.write(message)
        #response = self.ser.readline()
        #print(f'response: {response}')
    

    def show(self):
        message = struct.pack('BBB', ord(':'), self.command_count, ord('s'))
        self.command_count += 1
        # print(message)
        self.ser.write(message)
        # response = self.ser.readline()
        # print(response)

