from flask import Flask, send_from_directory, Response
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from dash_uploader.configure_upload import decorate_server as du_service

import dash_bootstrap_components as dbc
import dash_uploader as du
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, State, Trigger

import asyncio
import base64
import cv2
import threading
import os.path
from dash.dependencies import Output, Input
from quart import Quart, websocket
from dash_extensions import WebSocket

import numpy as np
from pathlib import Path
import uuid
import io
from base64 import b64encode
from PIL import Image

import moviepy.editor as mpy
from quart import Quart, websocket
import pafy
from apps.creator.functions import VideoToLed

APP_ID = 'windwow_gallery_creator'
URL_BASE = '/dashapp/'
MIN_HEIGHT = 600
n_streams=1
led_hor = 30
led_ver = 30
video_to_led = VideoToLed()
video_to_led.open_video_from_file(path=os.path.join('apps', 'static', 'assets', 'videos'), filename="color stripes.mp4")
# (url='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler')

        
def get_layout():
    layout = dbc.Container([
        
        dbc.FormGroup([
            dbc.Row([
                dbc.Label('Paste a Youtube Link here and press load (max 5 min):  '),
                dcc.Input(id=f'{APP_ID}_youtube_url', type='url', 
                          placeholder='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler',
                          debounce=True),
                dbc.Button('load', id=f'{APP_ID}_youtube_load_button', color='primary', 
                           disabled=False, n_clicks=0),
                ]),
        ]),
        dbc.Row([html.P(id=f'{APP_ID}_status'),]),
        dbc.Label('or drag and drop a video file here'),
        dcc.Store(id=f'{APP_ID}_large_upload_fn_store'),
        du.Upload(id=f'{APP_ID}_large_upload', max_file_size=5120),
        dbc.Row([

        ]), 
        
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    html.Div(
                        html.Div(id=f'{APP_ID}_udate_video')
                    )
                ),
            ]),
        
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label('Rect Bottom (px)'),
                    dcc.Slider(0, video_to_led.clip_height, 1, 
                               id=f'{APP_ID}_rect_bot_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=4,),
                ]),
            dbc.FormGroup([
                    dbc.Label('Rect Top (px)'),
                    dcc.Slider(0, video_to_led.clip_height, 1, 
                               id=f'{APP_ID}_rect_top_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=4,),
                ]), 
            dbc.FormGroup([
                    dbc.Label('Rect Left (px)'),
                    dcc.Slider(0, video_to_led.clip_width - video_to_led.rect_right, 1, 
                               id=f'{APP_ID}_rect_left_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=4,),
                ]),   
            dbc.FormGroup([
                    dbc.Label('Rect Right (px)'),
                    dcc.Slider(0, video_to_led.clip_width, 1,
                                id=f'{APP_ID}_rect_right_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=4),
                ]),
            dbc.FormGroup([
                    dbc.Label('Clip Start (sec)'),
                    dcc.Slider(0, video_to_led.clip_width, 1, 
                               id=f'{APP_ID}_t_start_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=0,),
                ]),
            dbc.FormGroup([
                    dbc.Label('Clip End (sec)'),
                    dcc.Slider(0, video_to_led.clip_duration, 1, 
                               id=f'{APP_ID}_t_end_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False}, 
                                value=video_to_led.clip_duration),
                ]),
            dbc.FormGroup([
                dbc.Label('Thickness (px)'),
                dcc.Slider(0, 20, 1, id=f'{APP_ID}_thickness_input', marks=None, value=4,
                            tooltip={"placement": "bottom", "always_visible": False}, 
                            disabled=True),
                ])
            ]),
        ]),
        dbc.ButtonGroup([
            dbc.Button('Record', id=f'{APP_ID}_record_button', color='primary', disabled=False),
            html.A(
                dbc.Button('Download Sequence', id=f'{APP_ID}_download_button', color='primary', disabled=False),
                id=f'{APP_ID}_download_link',
                href=''
            )
        ]),
    ])
    return layout


def add_video_editing_dashboard(dash_app):

    @du.callback(
        output=Output(f'{APP_ID}_large_upload_fn_store', 'data'),
        id=f'{APP_ID}_large_upload',
    )
    def get_a_list(filenames):
        return {i: filenames[i] for i in range(len(filenames))}


    @dash_app.callback(
        [
            # Output(f'{APP_ID}_process_video_button', 'disabled'),
            Output(f'{APP_ID}_t_start_input', 'value'),
            Output(f'{APP_ID}_t_end_input', 'value'),
            Output(f'{APP_ID}_thickness_input', 'value')
        ],
        [
            Input(f'{APP_ID}_large_upload_fn_store', 'data'),
        ],
    )
    def upload_video(dic_of_names):
        if dic_of_names is None:
            return True, 0., None, None

        clip = mpy.VideoFileClip(dic_of_names[list(dic_of_names)[0]])

        return False, 0., clip.duration, clip.size[0]
    
    
    @dash_app.callback(Output(f'{APP_ID}_udate_video', 'children'),
            [
                Input(f'{APP_ID}_thickness_input', 'value'),
                Input(f'{APP_ID}_large_upload_fn_store', 'data'),
                Input(f'{APP_ID}_t_start_input', 'value'),
                Input(f'{APP_ID}_t_end_input', 'value'),
                Input(f'{APP_ID}_rect_bot_input', 'value'),
                Input(f'{APP_ID}_rect_top_input', 'value'),
                Input(f'{APP_ID}_rect_left_input', 'value'),
                Input(f'{APP_ID}_rect_right_input', 'value'),
            ])
    def update_video(thickness, dic_of_names, clip_start, clip_end, rect_bot, rect_top, rect_left, rect_right):
        video_to_led.pause()
        video_to_led.set_start_end_sec(clip_start, clip_end)
        video_to_led.set_rectangle(rect_bot, rect_top, rect_left, rect_right, thickness)
        video_to_led.play()
        return html.Img(src=f'{URL_BASE}video_feed/{thickness}', style={'width': '500px'})
    
    
    
    @dash_app.callback(Output(f'{APP_ID}_status', 'children'),
                Input(f'{APP_ID}_youtube_load_button', 'n_clicks'),
                State(f'{APP_ID}_youtube_url', 'value')
                )
    def load_youtube_video(nclicks:int, url: str):
        if url:
            video_to_led.pause()
            status = video_to_led.open_youtube_video(url=url)
            video_to_led.play()
        return status
    
        
    @dash_app.server.route(f'{URL_BASE}video_feed/<value>')
    def video_feed(value):
        if video_to_led.is_playing:
            video_to_led.restart()
        return Response(video_to_led.start(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
        
        
    @dash_app.server.route('/downloads/<path:path>')
    def serve_static(path):
        return send_from_directory(
            Path("downloads"), path, as_attachment=True
        )


    return dash_app   



def init_dash(server):
    
    external_stylesheets = [
        dbc.themes.BOOTSTRAP,
        dbc.themes.SLATE
    ]
    
    # Setup Dash app
    dash_app = Dash(__name__, server=server, 
                    url_base_pathname=URL_BASE,
                    external_stylesheets=external_stylesheets)
    dash_app.config['suppress_callback_exceptions'] = True
    du.configure_upload(dash_app, Path.cwd() / Path("video_temp"), use_upload_id=False, upload_api=URL_BASE+"API/resumable")
    
    dash_app.layout = get_layout()
    dash_app = add_video_editing_dashboard(dash_app)
    
    return dash_app.server

