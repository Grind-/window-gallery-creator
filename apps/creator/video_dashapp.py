from flask import Flask, send_from_directory, Response
from dash import dcc, ctx
from dash import html
import dash_bootstrap_components as dbc
import dash_uploader as du
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, State, Trigger

import os.path
from dash.dependencies import Output, Input

from pathlib import Path

import moviepy.editor as mpy
from apps.creator.functions import VideoToLed
import base64
from distutils.dir_util import copy_tree

APP_ID = 'windwow_gallery_creator'
URL_BASE = '/dashapp/'
MIN_HEIGHT = 600

# copy subdirectory example
from_directory = "apps/static/assets/videos"
to_directory = "apps/static/assets/.temp"
# copy_tree(from_directory, to_directory)

video_to_led = VideoToLed()
video_to_led.open_video_from_file(path=os.path.join('apps', 'static', 'assets', 'videos'), filename="color stripes.mp4")
youtube_url='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler' 
        
def get_layout():
    layout = dbc.Container([

        dbc.Row([
            dbc.Label('Paste a Youtube Link here and press load (max 5 min):  ',),
            ], style={"margin-top":"50px", "margin":"20px 0px"}),
        dbc.Row([dcc.Input(id=f'{APP_ID}_youtube_url', type='url', 
                          placeholder='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler',
                          debounce=True, style={"width": "300px"}),
                dbc.Button('load', id=f'{APP_ID}_youtube_load_button', color='primary', 
                           disabled=False, n_clicks=0),], style={"margin":"20px 0px"}),
        dbc.Row([html.P(id=f'{APP_ID}_video_filename'),]),
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
                                value=video_to_led.clip_height-4,),
                    ]), 
                dbc.FormGroup([
                    dbc.Label('Rect Left (px)'),
                    dcc.Slider(0, video_to_led.clip_width, 1, 
                               id=f'{APP_ID}_rect_left_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=4,),
                    ]),   
                dbc.FormGroup([
                    dbc.Label('Rect Right (px)'),
                    dcc.Slider(0, video_to_led.clip_width, 1,
                                id=f'{APP_ID}_rect_right_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=video_to_led.clip_width-4),
                    ]),
                dbc.FormGroup([
                    dbc.Label('Clip Start (sec)'),
                    dcc.Slider(0, video_to_led.clip_duration, 1, 
                               id=f'{APP_ID}_t_start_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=0,),
                    ]),
                dbc.FormGroup([
                    dbc.Label('Clip End (sec)'),
                    dcc.Slider(1, video_to_led.clip_duration, 1, 
                               id=f'{APP_ID}_t_end_input', marks=None,
                                tooltip={"placement": "bottom", "always_visible": False}, 
                                value=video_to_led.clip_duration),
                    ]),
            ]),
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label('Thickness (px)'),
                    dcc.Slider(0, 20, 1, id=f'{APP_ID}_thickness_input', marks=None, value=4,
                                tooltip={"placement": "bottom", "always_visible": False}, 
                                disabled=True),
                    ]),
                dbc.FormGroup([
                    dbc.Label('Brightness'),
                    dcc.Slider(-1, 1, 0.01, id=f'{APP_ID}_brightness_input', marks={'0':'0'}, 
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=0,),
                    ]),
                dbc.FormGroup([
                    dbc.Label('Contrast'),
                    dcc.Slider(1, 10, 0.1, id=f'{APP_ID}_contrast_input', marks=None, 
                                tooltip={"placement": "bottom", "always_visible": False},
                                value=1,),
                    ]),
            ]),
        ]),
        dbc.ButtonGroup([
            # dbc.Button('Record', id=f'{APP_ID}_record_button', color='primary', disabled=False),
            # dbc.Button('Stop Record', id=f'{APP_ID}_stop_record_button', color='primary', disabled=False),
            dbc.Button('Create Sequence', id=f'{APP_ID}_create_sequence_button', color='primary', disabled=False),
            dcc.Download(id=f"{APP_ID}_download_sequence_file"),
            dcc.Input(id=f'{APP_ID}_frame_id', type='url', 
                          placeholder='frame id here',
                          debounce=True, style={"width": "300px"}),
            dbc.Button('Send Sequence', id=f'{APP_ID}_send_sequence', color='primary', disabled=True),
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
            Output(f'{APP_ID}_status', 'data')
        ],
        [
            Input(f'{APP_ID}_large_upload_fn_store', 'data'),
        ],
    )
    def upload_video(dic_of_names):
        if dic_of_names is None:
            return True, 0., None, None

        clip = mpy.VideoFileClip(dic_of_names[list(dic_of_names)[0]])

        return ''
    
    
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
                Input(f'{APP_ID}_brightness_input', 'value'),
                Input(f'{APP_ID}_contrast_input', 'value'),
                Input(f'{APP_ID}_video_filename', 'value')
            ])
    def update_video(thickness, dic_of_names, clip_start, clip_end, rect_bot, rect_top, rect_left, rect_right, 
                     brightness, contrast, video_filename):
        rect_top = video_to_led.clip_height - rect_top
        rect_right = video_to_led.clip_width - rect_right
        
        path = os.path.join('apps', 'static', 'assets', '.temp')
        filename = "color stripes.mp4"
        if video_filename:
            filename = video_filename
        filename_bytes = filename.encode("ascii")
        path_bytes = path.encode("ascii")
        path_base64_bytes = base64.b64encode(path_bytes)
        path_base64_string = path_base64_bytes.decode("ascii")
        filename_base64_bytes = base64.b64encode(filename_bytes)
        filename_base64_string = filename_base64_bytes.decode("ascii")
        video_feed_url = f'{URL_BASE}video_feed/{path_base64_string}/{filename_base64_string}/{rect_bot}/{rect_top}/{rect_left}/{rect_right}/{clip_start}/{clip_end}/{thickness}/{brightness}/{contrast}'
        if os.path.exists(os.path.join(path, filename)):
            return html.Img(src=video_feed_url, style={'width': '500px'})
        
    # @dash_app.callback(Output(f'{APP_ID}_send_sequence', 'disabled'),
    #         [
    #             State(f'{APP_ID}_thickness_input', 'value'),
    #             State(f'{APP_ID}_large_upload_fn_store', 'data'),
    #             State(f'{APP_ID}_t_start_input', 'value'),
    #             State(f'{APP_ID}_t_end_input', 'value'),
    #             State(f'{APP_ID}_rect_bot_input', 'value'),
    #             State(f'{APP_ID}_rect_top_input', 'value'),
    #             State(f'{APP_ID}_rect_left_input', 'value'),
    #             State(f'{APP_ID}_rect_right_input', 'value'),
    #             State(f'{APP_ID}_video_filename', 'value'),
    #             State(f'{APP_ID}_frame_id', 'value'),
    #             Input(f'{APP_ID}_create_sequence_button', 'n_clicks')
    #         ])
    # def create_sequence_callback(thickness, dic_of_names, clip_start, clip_end, rect_bot, rect_top, rect_left, rect_right, video_filename, frame_id, n_clicks):
    #     if n_clicks:
    #         rect_top = video_to_led.clip_height - rect_top
    #         rect_right = video_to_led.clip_width - rect_right
    #         path = os.path.join('apps', 'static', 'assets', '.temp')
    #         filename = "color stripes.mp4"
    #         if video_filename:
    #             filename = video_filename
    #         video_for_download = VideoToLed()
    #         video_for_download.open_video_from_file(path, filename)
    #         video_for_download.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
    #         video_for_download.set_start_end_sec(int(clip_start), int(float(clip_end)))
    #         status = video_for_download.save_to_file(frame_id)
    #         return not status
    
    @dash_app.callback(Output(f'{APP_ID}_status', 'data'),
            [
                State(f'{APP_ID}_thickness_input', 'value'),
                State(f'{APP_ID}_large_upload_fn_store', 'data'),
                State(f'{APP_ID}_t_start_input', 'value'),
                State(f'{APP_ID}_t_end_input', 'value'),
                State(f'{APP_ID}_rect_bot_input', 'value'),
                State(f'{APP_ID}_rect_top_input', 'value'),
                State(f'{APP_ID}_rect_left_input', 'value'),
                State(f'{APP_ID}_rect_right_input', 'value'),
                State(f'{APP_ID}_video_filename', 'value'),
                State(f'{APP_ID}_frame_id', 'value'),
                State(f'{APP_ID}_brightness_input', 'value'),
                State(f'{APP_ID}_contrast_input', 'value'),
                Input(f'{APP_ID}_send_sequence', 'n_clicks')
            ])
    def send_to_frame(thickness, dic_of_names, clip_start, clip_end, rect_bot, rect_top, rect_left, 
                      rect_right, video_filename, frame_id, brightness, contrast, n_clicks):
        if n_clicks:
            rect_top = video_to_led.clip_height - rect_top
            rect_right = video_to_led.clip_width - rect_right
            path = os.path.join('apps', 'static', 'assets', '.temp')
            filename = "color stripes.mp4"
            if video_filename:
                filename = video_filename
            video_for_download = VideoToLed()
            video_for_download.open_video_from_file(path, filename)
            video_for_download.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
            video_for_download.set_start_end_sec(int(clip_start), int(float(clip_end)))
            video_for_download.set_brightness_contrast(int(brightness), int(float(contrast)))
            return video_for_download.send_over_mqtt(frame_id)
        
    @dash_app.callback(Output(f'{APP_ID}_video_filename', 'value'),
                Input(f'{APP_ID}_youtube_load_button', 'n_clicks'),
                State(f'{APP_ID}_youtube_url', 'value')
                )
    def load_youtube_video(nclicks:int, url: str):
        payload = ''
        if url:
            payload = video_to_led.load_youtube_video(url=url)
        return payload
    
        
    @dash_app.server.route(f'{URL_BASE}video_feed/<string:path_encoded>/<string:filename_encoded>/<rect_bot>/<rect_top>/<rect_left>/<rect_right>/<t_start>/<t_end>/<thickness>/<brightness>/<contrast>')
    def video_feed(path_encoded, filename_encoded, rect_bot, rect_top, rect_left, rect_right, t_start, t_end, thickness,brightness, contrast):
        path_base64_bytes = path_encoded.encode("ascii")
        path_base64_bytes = base64.b64decode(path_base64_bytes)
        path_decoded = path_base64_bytes.decode("ascii")
        filename_base64_bytes = filename_encoded.encode("ascii")
        filename_base64_bytes = base64.b64decode(filename_base64_bytes)
        filename_decoded = filename_base64_bytes.decode("ascii")
        video_to_led_feed = VideoToLed()
        video_to_led_feed.open_video_from_file(path_decoded, filename_decoded)
        video_to_led_feed.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
        video_to_led_feed.set_start_end_sec(int(t_start), int(float(t_end)))
        video_to_led_feed.set_brightness_contrast(float(brightness), int(float(contrast)))
        if video_to_led_feed.is_playing:
            video_to_led_feed.restart()
        return Response(video_to_led_feed.start(),
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

