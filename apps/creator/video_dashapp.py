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
import dash_html_components as html
import threading

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

APP_ID = 'user_large_video'
URL_BASE = '/dashapp/'
MIN_HEIGHT = 600
n_streams=1
led_hor = 30
led_ver = 30
video_to_led = VideoToLed()
video_to_led.open_youtube_video(url='https://www.youtube.com/watch?v=wr-rIz1-VG4')

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

        
def get_layout():
    layout = dbc.Container([
        dcc.Store(id=f'{APP_ID}_large_upload_fn_store'),
        du.Upload(id=f'{APP_ID}_large_upload', max_file_size=5120),
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label('Subclip Start (s)'),
                    dbc.Input(id=f'{APP_ID}_t_start_input', type='number')
                ]),
                dbc.FormGroup([
                    dbc.Label('Crop Bottom (px)'),
                    dbc.Input(id=f'{APP_ID}_crop_bot_input', type='number', value=0)
                ])
            ]),
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label('Subclip End(s)'),
                    dbc.Input(id=f'{APP_ID}_t_end_input', type='number')
                ]),
                dbc.FormGroup([
                    dbc.Label('Crop Top (px)'),
                    dbc.Input(id=f'{APP_ID}_crop_top_input', type='number', value=0)
                ])
            ]),
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label('Video Width (px)'),
                    dbc.Input(id=f'{APP_ID}_vid_w_input', type='number')
                ])
            ])
    
        ]), 
        dbc.ButtonGroup([
            dbc.Button('Process Video', id=f'{APP_ID}_process_video_button', color='primary', disabled=True),
            html.A(
                dbc.Button('Download Video', id=f'{APP_ID}_download_button', color='primary', disabled=True),
                id=f'{APP_ID}_download_link',
                href=''
            )
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                   # html.Div(id=f'{APP_ID}_image_div')
                    html.Div([
                        html.Div(id=f'{APP_ID}_video_feed')
                        # html.Img(src="/dashapp/video_feed", style={'width': '40%', 'padding': 10})
                    ])
                ),
            ]),
            dbc.Col(
                dcc.Loading(
                    html.Div(id=f'{APP_ID}_video_div')
                ),
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
            Output(f'{APP_ID}_process_video_button', 'disabled'),
            Output(f'{APP_ID}_t_start_input', 'value'),
            Output(f'{APP_ID}_t_end_input', 'value'),
            Output(f'{APP_ID}_vid_w_input', 'value')
        ],
        [
            Input(f'{APP_ID}_large_upload_fn_store', 'data'),
        ],
    )
    def upload_video(dic_of_names):
        if dic_of_names is None:
            return True, 0., None, None

        clip_1 = mpy.VideoFileClip(dic_of_names[list(dic_of_names)[0]])

        return False, 0., clip_1.duration, clip_1.size[0]
    
    
    @dash_app.callback(Output(f'{APP_ID}video_feed', 'children'),
            [
                Input(f'{APP_ID}_vid_w_input', 'value'),
                Input(f'{APP_ID}_large_upload_fn_store', 'data'),
                Input(f'{APP_ID}_t_start_input', 'value'),
                Input(f'{APP_ID}_t_end_input', 'value'),
                Input(f'{APP_ID}_crop_bot_input', 'value'),
                Input(f'{APP_ID}_crop_top_input', 'value'),
            ])
    def video_feed(video_width, dic_of_names, clip_1_start, clip_1_end, crop_bot, crop_top):
        video_to_led.set_start_sec(clip_1_start)
        return html.Img(src=f'{URL_BASE}video_feed/reset', style={'width': '40%', 'padding': 10})
        
    @dash_app.server.route(f'{URL_BASE}video_feed/<reset_value>')
    def video_feed_endpoint():
        if video_to_led.is_playing:
            video_to_led.restart()
        return Response(video_to_led.generate_frames(),
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
    ]
    
    # Setup Dash app
    dash_app = Dash(__name__, server=server, 
                    url_base_pathname=URL_BASE,
                    external_stylesheets=external_stylesheets)
    dash_app.config['suppress_callback_exceptions'] = True
    du.configure_upload(dash_app, Path.cwd() / Path("temp"), True, URL_BASE+"API/resumable")
    
    dash_app.layout = get_layout()
    dash_app = add_video_editing_dashboard(dash_app)
    
    return dash_app.server


# def frame_out(video_width, dic_of_names, clip_1_start, clip_1_end, crop_bot, crop_top):
#         if any([v is None for v in [video_width, dic_of_names, crop_bot, crop_top]]):
#             raise PreventUpdate
#
#         clip_1 = mpy.VideoFileClip(dic_of_names[list(dic_of_names)[0]])
#         clip_1 = clip_1.fx(mpy.vfx.resize, width=video_width)
#         clip_1 = clip_1.subclip(t_start=clip_1_start, t_end=clip_1_end)
#         clip_1 = clip_1.fx(mpy.vfx.crop, y1=crop_top, y2=clip_1.size[1]-crop_bot)
#         # for image export in memory using PIL (for base64 convert), need to apply mask manually
#         f = clip_1.fx(mpy.vfx.resize, width=540).get_frame(t=0)
#
#         im = Image.fromarray(f)
#         rawBytes = io.BytesIO()
#         im.save(rawBytes, "PNG")
#         rawBytes.seek(0)
#
#         return html.Img(src=f"data:image/PNG;base64, {b64encode(rawBytes.read()).decode('utf-8')}")
#
#
#
#     @dash_app.callback(
#         [
#             Output(f'{APP_ID}_video_div', 'children'),
#             Output(f'{APP_ID}_download_link', 'href'),
#             Output(f'{APP_ID}_download_button', 'disabled'),
#          ],
#         [
#             Input(f'{APP_ID}_process_video_button', 'n_clicks'),
#         ],
#         [
#             State(f'{APP_ID}_large_upload_fn_store', 'data'),
#             State(f'{APP_ID}_t_start_input', 'value'),
#             State(f'{APP_ID}_t_end_input', 'value'),
#             State(f'{APP_ID}_vid_w_input', 'value'),
#             State(f'{APP_ID}_crop_bot_input', 'value'),
#             State(f'{APP_ID}_crop_top_input', 'value'),
#         ]
#     )
#     def process_pre_video(n_clicks, dic_of_names, clip_1_start, clip_1_end, video_width, crop_bot, crop_top):
#         if n_clicks is None:
#             raise PreventUpdate
#
#         if dic_of_names is None:
#             return None
#         clip_1 = mpy.VideoFileClip(dic_of_names[list(dic_of_names)[0]])
#         clip_1 = clip_1.fx(mpy.vfx.resize, width=video_width)
#         clip_1 = clip_1.subclip(t_start=clip_1_start, t_end=clip_1_end)
#         clip_1 = clip_1.fx(mpy.vfx.crop, y1=crop_top, y2=clip_1.size[1]-crop_bot)
#
#         ffname = Path("downloads") / f'{str(uuid.uuid4())}.mp4'
#         Path.mkdir(ffname.parent, parents=True, exist_ok=True)
#         cvc = mpy.CompositeVideoClip([clip_1], bg_color=(255, 255, 255))
#         # preview video set to 540 width and 5 fps
#         fn_pre = '.'.join(str(ffname).split('.')[:-1]) + 'preview_.webm'
#         cvc.fx(mpy.vfx.resize, width=540).write_videofile(fn_pre, audio=False, fps=5)
#         # write full deal
#         cvc.write_videofile(str(ffname), audio=False, fps=clip_1.fps)
#
#         vid = open(fn_pre, 'rb')
#         base64_data = b64encode(vid.read())
#         base64_string = base64_data.decode('utf-8')
#         return [html.Video(src=f'data:video/webm;base64,{base64_string}', controls=True)], f'/{ffname}', False