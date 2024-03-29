'''
Created on 10.08.2022

@author: jhirte
'''
import hashlib
from os import listdir, makedirs, path, remove
import time

from PIL import Image
import cv2

from apps.creator.mqtt import MqttCore
from apps.util.video_utils import set_brightness
from apps.util.youtube_downloader import YoutubeDownloader
import numpy as np


download_destination = 'apps/static/assets/.temp'
(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

config = {}
config['frame_id'] = '0000001'
config['topic_sequence'] = '/sequence'#  + config['frame_id']
config['topic_frame_connected'] = '/frame_connected'
config['client_id'] = 'window_gallery'
config['password'] = 'password'
config['topic_config'] = '/config'
config['topic_led_count'] = '/led_count'


class VideoToLed():
    def __init__(self, username):
        self.username = username
        self.led_array = np.array([])
        self.is_playing = False
        self.restart_flag = False
        self.stop_flag = False
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
        self.led_hor = 65
        self.led_ver = 85
        self.hash = ''
        self.brightness = 0
        self.contrast = 0
        self.pause_flag = False
        self.record_flag = False
        self.black = 0
        
        self.spot_keyframes = None
        
    def get_clip_duration(self):
        return self.clip_duration   
    
    def set_spot_keyframes(self, bl, tl, tr, br):
        int_spot_arrays = self.interpolate_spot_arrays(bl, tl, tr, br)
        self.spot_keyframes = [int_spot_arrays[0], int_spot_arrays[1], int_spot_arrays[2], int_spot_arrays[3]]    
            
    def load_youtube_video(self, url: str):
        downloader = YoutubeDownloader(url)
        video_length = downloader.video.length
        if video_length > 12000:
            return 'video is too long, choose one with less than 5 minutes'
        downloader.choose_destination(download_destination)
        self.video_name = downloader.download_video('low')
        return self.video_name
        
    def open_video_from_file(self, filepath, filename):
        filepath = path.join(filepath, filename)
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(filepath)
        self.video_name = filename
        self.clip_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.clip_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) 
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) 
        self.frame_count = int(self.cap.get(cv2. CAP_PROP_FRAME_COUNT))
        self.clip_duration = self.frame_count/self.fps
        if (self.cap.isOpened()== False): 
            print("Error opening video stream or file")
        
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
            self.clip_start_frame = int(self.fps*start_sec)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.clip_start_frame)
        # from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
        # ffmpeg_extract_subclip(download_destination+'/'+self.video_name, self.clip_start_frame/self.fps, 
        #                        self.clip_end_frame/self.fps, targetname=download_destination+'/cut'+self.video_name)
        # self.open_video_from_file(download_destination, 'cut'+self.video_name)
        
    def set_brightness_contrast(self, brightness: int, contrast: int, black: int):
        self.brightness = brightness
        self.contrast = contrast
        self.black = black
        
    def set_led_count(self, led_hor: int, led_ver: int):
        self.led_hor = led_hor
        self.led_ver = led_ver
        pass

    def calibrate(self, led_hor: int, led_ver: int, frame_id: str):
        led_array_seq = []
        for lp in range(100):
            line_top = np.full((led_hor, 3), [255, 0, 0])
            line_bot = np.full((led_hor, 3), [0, 0, 255])
            line_left = line_right = np.full((led_ver, 3), [0, 0, 0])
            led_arrays = [line_top, line_bot, line_left, line_right]
            spot_array = [0, 0, 0, 0]
            led_array_seq = np.concatenate([led_array_seq,
                                            np.concatenate(np.flipud(led_arrays[0])),
                                            np.concatenate(np.flipud(led_arrays[2])),
                                            np.concatenate(led_arrays[1]),
                                            np.concatenate(led_arrays[3]),
                                            spot_array])
        led_strip_array = np.array(led_array_seq)
        led_strip_array = led_strip_array.astype(np.uint8)
        print((len(led_strip_array)-(4*(self.clip_end_frame-self.clip_start_frame)))/(2*(self.led_hor + self.led_ver))/3)
        filename_led_strip = frame_id + ".bin"
        led_strip_bin_file = path.join(FileUtils.derive_temp_folder_path(self.username), filename_led_strip)
        self.save_to_file(led_strip_array, led_strip_bin_file)
        print(f'Sending calibration sequence with horizontal: {led_hor} and vertical: {led_ver}')
        mqtt_client = MqttCore()
        mqtt_client.start(config['topic_frame_connected'], None)
        mqtt_client.publish(frame_id + config['topic_sequence'], frame_id + '#' + self.hash)
        mqtt_client.stop(config['topic_frame_connected'])
        return f'Successfully sent Calibration Sequence to frame {frame_id}'
    
    def start(self):
        print('start')
        # Capture frame-by-frame
        if not self.spot_keyframes:
            self.spot_keyframes = np.zeros((4,self.frame_count))
        last_frame_time = time.time()
        self.is_playing = True
        while True:
            if self.pause_flag == False:
                last_frame_time = time.time()
                if self.stop_flag:
                        self.release()
                        break
                if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.clip_end_frame-1 or self.restart_flag:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.clip_start_frame)
                    self.restart_flag = False
                    
                
  
                ret, video_frame = self.cap.read()
                
                
                if ret == True:
                    # adjust contrast and brightness
                    video_frame = cv2.convertScaleAbs(video_frame, alpha=self.contrast)
                    video_frame = set_brightness(video_frame, self.brightness)

                    # create led/spot arrays and frame
                    led_arrays = self.generate_led_arrays(video_frame)
                    spot_dict =  self.get_spot_dict_for_frame(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))-self.clip_start_frame)
                    
                    led_frame = self.generate_led_frame_image(led_arrays, spot_dict)
                    led_linear = self.generate_led_linear_image(led_arrays)
                    separator = Image.new('RGB', (self.clip_width, 10), (39, 43, 48))

                    # create rectangle
                    rect_start_point = (self.rect_left, self.rect_top)
                    rect_end_point = (self.clip_width - self.rect_right, self.clip_height - self.rect_bot)
                    rect_thickness = self.rect_thickness
                    color = (255, 0, 0)
                    overlay = video_frame.copy()
                    alpha = 0.4
                    overlay = cv2.rectangle(overlay, rect_start_point, rect_end_point, color, rect_thickness)
                    video_frame = cv2.addWeighted(overlay, alpha, video_frame, 1 - alpha, 0)
                    
                    # stacking all frames
                    frame = np.vstack((video_frame, separator, led_frame, separator, led_linear))
                    
                    # transform to jpeg
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    
                    sleep_time = 1/self.fps*1000 - (time.time() - last_frame_time)*1000
                    if sleep_time <= 0:
                        sleep_time = 0
                    # print('now: ' + str(time.time()))
                    # print('last frame time: ' + str(last_frame_time))
                    # print('sleep time: ' + str(sleep_time))
                    # print('fps: ' + str(self.fps)) 
                    # print('frame number: ' + str(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
                    # print('time per frame: ' + str(1/self.fps*1000))
                    # print('time per frame calcualted: ' + str((time.time() - last_frame_time) *1000))
                    # print('                ')      
                    time.sleep(sleep_time*0.001)
                    
                    
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
        
        
        resized_hor[resized_hor < self.black] = 0
        resized_ver[resized_ver < self.black] = 0

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
     
    def generate_led_frame_image(self, led_arrays: list, spot_dict: dict):
        # print('generate_led_frame_image')
        size_horizontal = led_arrays[0].shape[0]
        size_vertical = led_arrays[2].shape[0]
        img = np.zeros([size_vertical,size_horizontal,3],dtype=np.uint8)
        # img.fill(5) # or img[:] = 255
        
        # adding light effect to shine into the center of the image
        for i in range (2):
            img[-1-i, :] =  led_arrays[0]/(i+1)
            img[i, :] = led_arrays[1]/(i+1)
            img[:, -1-i] = led_arrays[3]/(i+1)
            img[:, i] = led_arrays[2]/(i+1)
            
        factor = self.clip_width/size_horizontal
            
        img = cv2.resize(img[1:size_vertical-1, 1:size_horizontal-1], 
                         dsize=(self.clip_width, int(factor*size_vertical)), interpolation=cv2.INTER_CUBIC)
        
        

        spotlight_top_left = cv2.imread(path.join('apps', 'static', 'assets', 'img', 'preview', 'top_left.png'))
        spotlight_top_left = cv2.resize(spotlight_top_left, 
                         dsize=(self.clip_width, int(factor*size_vertical)), interpolation=cv2.INTER_CUBIC)
        
        spotlight_top_right = cv2.imread(path.join('apps', 'static', 'assets', 'img', 'preview', 'top_right.png'))
        spotlight_top_right = cv2.resize(spotlight_top_right, 
                         dsize=(self.clip_width, int(factor*size_vertical)), interpolation=cv2.INTER_CUBIC)
        
        spotlight_bottom_left = cv2.imread(path.join('apps', 'static', 'assets', 'img', 'preview', 'bottom_left.png'))
        spotlight_bottom_left = cv2.resize(spotlight_bottom_left, 
                         dsize=(self.clip_width, int(factor*size_vertical)), interpolation=cv2.INTER_CUBIC)
        
        spotlight_bottom_right = cv2.imread(path.join('apps', 'static', 'assets', 'img', 'preview', 'bottom_right.png'))
        spotlight_bottom_right = cv2.resize(spotlight_bottom_right, 
                         dsize=(self.clip_width, int(factor*size_vertical)), interpolation=cv2.INTER_CUBIC)
        
        alpha = 1
        img = cv2.addWeighted(src1=img, alpha=alpha, src2=spotlight_top_left, beta=spot_dict['top_left']/255, gamma=0)
        img = cv2.addWeighted(src1=img, alpha=alpha, src2=spotlight_top_right, beta=spot_dict['top_right']/255, gamma=0)
        img = cv2.addWeighted(src1=img, alpha=alpha, src2=spotlight_bottom_left, beta=spot_dict['bottom_left']/255, gamma=0)
        img = cv2.addWeighted(src1=img, alpha=alpha, src2=spotlight_bottom_right, beta=spot_dict['bottom_right']/255, gamma=0)
        
        return img
    
    def generate_led_linear_image(self, led_arrays: []):
        linear_array = np.concatenate([np.flipud(led_arrays[2]), 
                                      (led_arrays[1]), 
                                      led_arrays[3],   
                                      np.flipud(led_arrays[0])])
        # print('generate_led_frame_image')
        size_horizontal = linear_array.shape[0]
        size_vertical = 20
        img = np.zeros([size_vertical,size_horizontal,3],dtype=np.uint8)
        img.fill(5) # or img[:] = 255
        
        # adding light effect to shine into the center of the image
        for i in range (10):
            img[-1-i,:] = linear_array/(i+1)
        
        img = cv2.resize(img[1:size_vertical-1, 1:size_horizontal-1], 
                         dsize=(self.clip_width, size_vertical*2), interpolation=cv2.INTER_CUBIC)
        return img
    
    def get_sequence_array(self):
        led_array_seq = []
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.clip_start_frame)
        while True:
            # print(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.clip_end_frame-1:
                # self.frame_counter = self.clip_start_frame
                # self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.clip_start_frame)
                break
            ret, video_frame = self.cap.read()
            # if mirrow == True:
            #     frame = cv2.flip(frame, 1) 
            if ret == True:
                # create led arrays and frame
                video_frame = cv2.convertScaleAbs(video_frame, alpha=self.contrast)
                video_frame = set_brightness(video_frame, self.brightness)
                led_arrays = self.generate_led_arrays(video_frame)
                spot_dict =  self.get_spot_dict_for_frame(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))-self.clip_start_frame)
                spot_array = [spot_dict['bottom_left'], spot_dict['top_left'], spot_dict['top_right'], spot_dict['bottom_right']]            
                # new_array_seq = np.concatenate([np.concatenate(np.flipud(led_arrays[2])),
                #                       np.concatenate(led_arrays[1]),
                #                       np.concatenate(led_arrays[3]),
                #                       np.concatenate(np.flipud(led_arrays[0])),
                #                       spot_array])
                # print(new_array_seq.shape)
                led_array_seq = np.concatenate([led_array_seq,
                                                np.concatenate(np.flipud(led_arrays[0])),
                                                np.concatenate(np.flipud(led_arrays[2])),
                                                np.concatenate(led_arrays[1]),
                                                np.concatenate(led_arrays[3]),
                                                spot_array])
                # spot_array_seq = np.concatenate([spot_array_seq,
                #                       spot_array])
            else: 
                print(f'Lost frame No {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}')
                break
        return np.array(led_array_seq) #, np.array(spot_array_seq)
    
    def interpolate_spot_arrays(self,
                        bottom_left: list, 
                        top_left: list, 
                        top_right: list, 
                        bottom_right: list):
        def interpolate(inp, fi):
            i, f = int(fi // 1), fi % 1  # Split floating-point index into whole & fractional parts.
            j = i+1 if f > 0 else i  # Avoid index error.
            return (1-f) * inp[i] + f * inp[j]

        new_len = self.clip_end_frame - self.clip_start_frame
        
        delta = (len(bottom_left)-1) / (new_len-1)
        bottom_left = [interpolate(bottom_left, i*delta) for i in range(new_len-1)]
        top_left = [interpolate(top_left, i*delta) for i in range(new_len-1)]
        top_right = [interpolate(top_right, i*delta) for i in range(new_len-1)]
        bottom_right = [interpolate(bottom_right, i*delta) for i in range(new_len-1)] 
        return np.array([bottom_left, top_left,top_right, bottom_right])

    def get_spot_dict_for_frame(self, frame_number: int):
        spot_dict = {}
        spot_dict['bottom_left'] = self.spot_keyframes[0][frame_number - 1]
        spot_dict['top_left'] = self.spot_keyframes[1][frame_number - 1]
        spot_dict['top_right'] = self.spot_keyframes[2][frame_number - 1]
        spot_dict['bottom_right'] = self.spot_keyframes[3][frame_number - 1]
        return spot_dict
    
    def send_over_mqtt(self, frame_id: str):
        self.save_temp_sequence(frame_id)
        print('send')
        mqtt_client = MqttCore()
        mqtt_client.start(config['topic_frame_connected'], None)
        mqtt_client.publish(frame_id + config['topic_sequence'], frame_id + '#' + self.hash)
        mqtt_client.stop(config['topic_frame_connected'])
        return f'Successfully sent Sequence to frame {frame_id}'
    
    def save_temp_sequence(self, frame_id: str):
        
        led_strip_array = self.get_sequence_array()
        led_strip_array = led_strip_array.astype(np.uint8)
        # spot_array = spot_array.astype(np.uint8)
        print((len(led_strip_array)-(4*(self.clip_end_frame-self.clip_start_frame)))/(2*(self.led_hor + self.led_ver))/3)
        filename_led_strip = frame_id + ".bin"
        # filename_spot = frame_id + "_spot.bin"
        led_strip_bin_file = path.join(FileUtils.derive_temp_folder_path(self.username), filename_led_strip)
        # spot_bin_file = path.join(FileUtils.derive_temp_folder_path(self.username), filename_spot)
        self.save_to_file(led_strip_array, led_strip_bin_file)
        # self.save_to_file(spot_array, spot_bin_file)
        return 'success'
        
    def save_sequence(self, sequence_name: str):
        
        led_strip_array = self.get_sequence_array()
        led_strip_array = led_strip_array.astype(np.uint8)
        # spot_array = spot_array.astype(np.uint8)
        # print((len(sequence_array)-(4*(self.clip_end_frame-self.clip_start_frame)))/(2*(self.led_hor + self.led_ver))/3)
        filename_led_strip = f"{sequence_name}_{self.led_hor}_{self.led_ver}.bin"
        # filename_spot = sequence_name + "_spot.bin"
        led_strip_bin_file = path.join(FileUtils.derive_folder_path(self.username), filename_led_strip)
        # spot_bin_file = path.join(FileUtils.derive_folder_path(self.username), filename_spot)
        self.save_to_file(led_strip_array, led_strip_bin_file)
        # self.save_to_file(spot_array, spot_bin_file)
        return f'Successfully Saved Sequence to {led_strip_bin_file}'
    
    def save_to_file(self, sequence_array, bin_file: str):
        
        h = hashlib.sha256()
        h.update(sequence_array)
        print(h.hexdigest())
        with open(bin_file, "wb") as file:
            file.write(sequence_array.tobytes())
            file.close()
        
        h  = hashlib.sha256()
        with open(bin_file, "rb", buffering=0) as file:    
            while True:
                chunk = file.read(h.block_size)
                if not chunk:
                    break
                h.update(chunk)
            file.close()
        self.hash = f'{h.hexdigest()}'
        print('saved file hash: ' + self.hash)
        print('saved file to: ' + bin_file)
        return True

    def validate_settings(self):
        return 'ok'
    
class Configurator():
    @classmethod
    def send_config(cls, frame_id: str, led_count: int):
        print('send config')
        mqtt_client = MqttCore()
        mqtt_client.start()
        mqtt_client.publish(f"{frame_id}{config['topic_config']}{config['topic_led_count']}", str(led_count))
        mqtt_client.stop()
        return f'Successfully sent Config to frame {frame_id}'

class FileUtils():
    def __init__(self, username):
        self.sequences_listed = []
        self.username = username
        self.folder_path = self.derive_folder_path(username)
        if not path.exists(self.folder_path):
            makedirs(self.folder_path)
        self.temp_path = self.derive_temp_folder_path(username)
        if not path.exists(self.temp_path):
            makedirs(self.temp_path)
        
    def list_movies(self):
        filenames = [f for f in listdir(self.folder_path) if path.isfile(path.join(self.folder_path, f))]
        return filenames
    
    def delete_sequence(self, sequence_name: str):
        bin_file = path.join(FileUtils.derive_folder_path(self.username), sequence_name)
        if path.isfile(bin_file):
            remove(bin_file)
        else:
            print("Error: %s file not found" % bin_file)
        return f'Deleted Sequence {sequence_name}'
            
    def send_saved_sequence(self, sequence_file: str, frame_id: str):
        bin_file = path.join(FileUtils.derive_folder_path(self.username), sequence_file)
        print(f'sending {bin_file}')
        h  = hashlib.sha256()
        with open(bin_file, "rb", buffering=0) as file:    
            while True:
                chunk = file.read(h.block_size)
                if not chunk:
                    break
                h.update(chunk)
            file.close()
        hash = f'{h.hexdigest()}'
        
        sequence_name = sequence_file.split('.')[0]
        mqtt_client = MqttCore()
        mqtt_client.start(config['topic_frame_connected'], None)
        mqtt_client.publish(frame_id + config['topic_sequence'], self.username + '/' + sequence_name + '#' + hash)
        mqtt_client.stop(config['topic_frame_connected'])
        
        return f'Sent Sequence {sequence_name} to frame {frame_id}'
    
    @classmethod
    def derive_folder_path(cls, username):
        return path.join('apps', 'sequences', username)
    
    @classmethod
    def derive_temp_folder_path(cls, username):
        return path.join('apps', 'sequences')

    
    
    
    # def stream_to_arduino(self):
    #     sequence_array = self.get_sequence_array()
    #     sec = 1 / self.fps
    #     strand = NeoPixel('COM8')
    #     fc = 0
    #     led = 1
    #     beginningOfTime = time.process_time()
    #     start = time.process_time()
    #     goAgainAt = start + sec
    #     led_count = self.led_hor*2 + self.led_ver*2
    #
    #     while True:
    #         print("Loop #%d at time %f" % (fc, time.process_time() - beginningOfTime))
    #         while led < (2*self.led_hor+2*self.led_ver):
    #             strand.setPixelColor(led, sequence_array[fc][led][0], sequence_array[fc][led][1], sequence_array[fc][led][2])
    #             # strand.show()
    #             led += 1
    #             if led >= led_count:
    #                 led = 1
    #                 break
    #         fc += 1
    #         if time.process_time() > goAgainAt:
    #             print("Oops, missed an iteration")
    #             goAgainAt += sec
    #             continue
    #         # Otherwise, wait for next interval
    #         timeToSleep = goAgainAt - time.process_time()
    #         goAgainAt += sec
    #         time.sleep(timeToSleep)
    #         print(f'time to sleep: {timeToSleep}')
    #
    #         if fc == len(sequence_array):
    #             fc = 0        
    # def download_arduino_code(self):
    #     print('download')
    #     sequence_array = self.get_sequence_array()
    #     index = 2
    #     json_string = dumps(sequence_array, cls=NumpyArrayEncoder)
    #
    #     ino_template_file = join('apps', 'static', 'assets', 'arduino_template.ino')
    #     with open(ino_template_file, "r") as f:
    #         contents = f.readlines()
    #
    #     contents.insert(index, json_string)
    #
    #     return contents
    #

# class NumpyArrayEncoder(JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         return JSONEncoder.default(self, obj)
#
# class NeoPixel(object):
#     # from https://github.com/mdaffin/PyNeoPixel
#     def __init__(self, port):
#         self.port = port
#         self.ser = serial.Serial(self.port, 115200, timeout=60)
#         self.command_count = 0
#
#
#     def setPixelColor(self, pixel, red, green, blue):
#         message = struct.pack('>HBBB', pixel, red, green, blue)
#         self.command_count += 1
#         if self.command_count >=255:
#             self.command_count = 0
#         #print(f'message: {message}')
#         self.ser.write(message)
#         #response = self.ser.readline()
#         #print(f'response: {response}')
#
#
#     def show(self):
#         message = struct.pack('BBB', ord(':'), self.command_count, ord('s'))
#         self.command_count += 1
#         # print(message)
#         self.ser.write(message)
#         # response = self.ser.readline()
#         # print(response)

