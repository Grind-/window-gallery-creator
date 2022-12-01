'''
Created on 29.11.2022

@author: jhirte
'''
from os import listdir, makedirs, path, remove
from apps.creator.mqtt import MqttCore

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
        mqtt_client.publish(config['topic_sequence'] + frame_id, self.username + '/' + sequence_name + '#' + hash)
        mqtt_client.stop(config['topic_frame_connected'])
        
        return f'Sent Sequence {sequence_name} to frame {frame_id}'
    
    @classmethod
    def derive_folder_path(cls, username):
        return path.join('apps', 'sequences', username)
    
    @classmethod
    def derive_temp_folder_path(cls, username):
        return path.join('apps', 'sequences')