import os
import pytube





fln = ''  # file name to be used while converting to MP3

class YoutubeDownloader:
    def __init__(self, url):
        self.destination = 'temp'
        self.video = pytube.YouTube(url)
        print('video description: ', self.video.description)
        print('rating', self.video.rating)
        print('length', self.video.length)
        print('views', self.video.views)
    
    def download_video(self, resolution):
        print('Fetching file ...')
        itag = self.choose_resolution(resolution)
        stream = self.video.streams.get_by_itag(itag)
        global fln
        fln = stream.default_filename
        try:
            print(f'Downloading: {fln}')
            stream.download(f'{self.destination }')
        except Exception as ex:
            print(f'{resolution} error {ex}, trying with low resolution ...')
            stream = self.video.streams.get_by_itag(18)
            stream.download(f'{self.destination }')
        print(f'Finished downloading: {fln}')
        return stream.default_filename

    
    def choose_resolution(self, resolution):
        if resolution in ["low", "360", "360p"]:
            itag = 18
        elif resolution in ["medium", "720", "720p", "hd"]:
            itag = 22
        elif resolution in ["high", "1080", "1080p", "fullhd", "full_hd", "full hd"]:
            itag = 137
        elif resolution in ["very high", "2160", "2160p", "4K", "4k"]:
            itag = 313
        else:
            itag = 18
        return itag
    
    def input_links(self):
        print("Enter the links of the videos (end by entering 'STOP'):")
    
        links = []
        link = ""
    
        while link != "STOP" and link != "stop":
            link = input()
            links.append(link)
    
        links.pop()
    
        return links
    
    
    def choose_destination(self, dest):
    
        if dest:
            self.destination = dest.replace(os.sep, '/')
            print(self.destination )
        else:
            self.destination  = self.destination  + '/'
            print(f'Choosing Default location {self.destination }')
    
        return self.destination  + '/'
