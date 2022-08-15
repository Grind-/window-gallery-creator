import dash
import dash_core_components as dcc
import dash_html_components as html

from flask import Flask, Response
import cv2
from threading import Thread
import numpy as np
import time 
from dash import Dash, dcc, html, Input, Output

class recordThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.video_nr = 0

    def run(self):
        self.running = True
    
    def record(self):
        self.running = True
        cap = cv2.VideoCapture(0)                                       # start camera stream
        video = np.zeros((720,1280,1))                                  # create initial frame being all black
        times = round(time.time() * 1000000)

        while self.running:
            # Capture frame-by-frame
            times = np.append(times, round(time.time() * 1000000))      # capture times stamp
            ret, frame = cap.read()                                     # capture a frame
            frameGray = np.expand_dims(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY), axis=2) # convert frame to grayscale (converts from 3D to 2D)
            video = np.append(video,frameGray,axis=2)                   # write current grayscale frame to video object

        print("Thread stopped")                             
        np.save(f'video_{self.video_nr}.npy',video)                     # save the video 
        np.save(f'time_stamps_{self.video_nr}.npy',times)               # save time stamps
        cap.release()                                                   # stop camera stream
        self.video_nr += 1                                              # add one to the video itterator                                                        

    def terminate(self):
        self.running = False
        print(self.running)

app = dash.Dash(__name__)
app.layout = html.Div(
    children=[
        html.H1(children="Video Recording",),
        html.P(
            children="Analyze the behavior of avocado prices"
            " and the number of avocados sold in the US"
            " between 2015 and 2018", 
        ),
        html.Div([
            html.P(children="Not recording",id="rec-string"),
            html.Button('Start Video', id="rec-button",n_clicks=0, className = "graphButtons")
        ]),dcc.Store(id="rec-store"),dcc.Store(id="recording"),
    ]
)


@app.callback([
    Output("rec-button","children"),
    Output("rec-store","value")],
    [Input("rec-button", 'n_clicks')]
)
def rec_button(n_clicks):
    click = n_clicks%2
    if click == 0:
        data = False
        return f"Start recording", data
    elif click == 1:
        data = True
        return f"Stop recording", data

@app.callback([
    Output("rec-string","children")],
    [Input("rec-store","value"),Input("rec-button", 'n_clicks')]
    )
def recordVideo(rec,n_clicks):
    if rec:
        print("video start")
        recording.record()
        print("running")
        return "Now Recording"

    elif n_clicks > 1 and n_clicks%2 == 0:
        print("terminating")
        recording.terminate()
        return "Not Recording"

if __name__ == "__main__":
    recording = recordThread()
    recording.start()
    app.run_server(debug=True)