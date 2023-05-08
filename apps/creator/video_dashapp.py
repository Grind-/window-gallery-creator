import base64
from distutils.dir_util import copy_tree
import logging
import os.path
from pathlib import Path

from dash import dcc, ctx, MATCH, ALL
from dash import html
from dash.dependencies import Output, Input
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, State, Trigger
from flask import Flask, send_from_directory, Response

from apps.creator.functions import VideoToLed, FileUtils, Configurator
import dash_bootstrap_components as dbc
import dash_uploader as du
import moviepy.editor as mpy


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

APP_ID = 'windwow_gallery_creator'
URL_BASE = '/dashapp/'
MIN_HEIGHT = 600
max_sequence_length = 30

username = 'TestUser'
file_utils = FileUtils(username)

root_directory = Path(*list(Path(__file__).parts[:-5]))

# copy subdirectory example
from_directory = "apps/static/assets/videos"
to_directory = "apps/static/assets/.temp"
copy_tree(from_directory, to_directory)



video_to_led = VideoToLed(username)
video_to_led.open_video_from_file(filepath=os.path.join('apps', 'static', 'assets', 'videos'), filename="color stripes.mp4")
youtube_url='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler' 
        
def get_layout():
    layout = dbc.Container([
        dbc.Card(
            dbc.CardBody([
                html.H3('Frame Configuration', className="card-title"),
                html.P('Frame ID'),
                dcc.Input(id=f'{APP_ID}_frame_id', type='text', 
                                          placeholder='Frame ID',
                                          debounce=True),
                html.P('LED Count Horizontal'),
                dcc.Input(id=f'{APP_ID}_led_hor', type='number', 
                              placeholder='LED Horizontal',
                              debounce=True, value=65),
                html.P('LED Count Vertical '),
                dcc.Input(id=f'{APP_ID}_led_ver', type='number', 
                              placeholder='LED Vertical',
                              debounce=True, value=85),
                dbc.ButtonGroup([
                    dbc.Button('Send To Frame', id=f'{APP_ID}_send_config', color='primary', disabled=True),
                ]),
            ])
        ),
        dbc.Card(
            dbc.CardBody([
                html.H3('Video Loader', className="card-title"),
                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            dbc.Label('Paste a Youtube Link here and press load (max 5 min):  ',),
                            ], style={"margin-top":"50px", "margin":"20px 0px"}),
                        dbc.Row([dcc.Input(id=f'{APP_ID}_youtube_url', type='url', 
                                          placeholder='https://www.youtube.com/watch?v=KM5kaH-y43Q&ab_channel=PixCycler',
                                          debounce=True, style={"width": "300px"}),
                                dbc.Button('load', id=f'{APP_ID}_youtube_load_button', color='primary', 
                                           disabled=False, n_clicks=0),], 
                                style={"margin":"20px 0px"}),
                    ]),

                    dbc.Col([
                        dbc.Row([dbc.Label('or drag and drop a video file here')], style={"margin-top":"50px", "margin":"20px 0px"}),
                        dbc.Row(
                            [  
                                dcc.Store(id=f'{APP_ID}_large_upload_fn_store'),
                                 du.Upload(id=f'{APP_ID}_large_upload', max_file_size=5120, default_style={
                                    'minHeight': 1,
                                    'lineHeight': 1
                                    # 'width': '80%',
                                    # 'height': '50%',
                                    # 'border': 'none',
                                    # 'textAlign': 'center',
                                    # 'background': "#ea8f32",
                                    # 'color': 'white',
                                    # 'outlineColor': '#ea8f32',
                                    # 'font-family': 'Avenir',
                                    # 'font-size': '10px',
                                    # 'font-weight': '150',
                                    # 'border-radius': '10px'
                                },),
                            ],
                            style={"margin":"20px 0px"}
                        ),
                    dbc.Row([html.P(id=f'{APP_ID}_video_filename')]),
                    ])
                 ])
            ])
        ),
        dbc.Row([

        ]), 
        
        dbc.Card(
            dbc.CardBody([
                html.H3('Video Creator', className="card-title"),
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            html.Div(
                                html.Div(id=f'{APP_ID}_update_video')
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
                            dbc.Label('Clip Length (sec)'),
                            dcc.Slider(1, max_sequence_length, 1, 
                                       id=f'{APP_ID}_t_length_input', marks=None,
                                        tooltip={"placement": "bottom", "always_visible": False}, 
                                        value=max_sequence_length),
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
                        dbc.FormGroup([
                            dbc.Label('Black (low)'),
                            dcc.Slider(0, 255, 1, id=f'{APP_ID}_black_input', marks=None, value=5,
                                        tooltip={"placement": "bottom", "always_visible": False}),
                            ]),
                        dbc.Button('Send Sequence to Frame', id=f'{APP_ID}_send_sequence', color='primary', disabled=True),
                        html.H5('Save Sequence'),
                        dbc.ButtonGroup([
                            dcc.Input(id=f'{APP_ID}_sequence_name', type='text', 
                                          placeholder='Sequence name',
                                          debounce=True),
                            dbc.Button('Save', id=f'{APP_ID}_save_sequence', color='primary', disabled=True),
                        ])
                    ]),
                ])
            ])
        ),
        
        html.H4(id=f'{APP_ID}_status', children=''),
            
       dbc.Card(
            dbc.CardBody([
                html.H3('Spotlight Creator', className="card-title"),
                html.Div([
                    dcc.RadioItems(['Bottom Left', 'Top Left', 'Top Right', 'Bottom Right'], 
                                   'Bottom Left', 
                                   id=f'{APP_ID}_spot_selector',
                                   inline=True
                                   # style={"display":"flex", "gap":"20px", "align-items":"flex-end"}
                                   )
                        ]),
                
                html.Div(id=f'{APP_ID}_keyframes', style={"display":"flex", "gap":"20px", "align-items":"flex-end"}),
                dcc.Store(id=f'{APP_ID}_keyframes_bl_store'),
                dcc.Store(id=f'{APP_ID}_keyframes_tl_store'),
                dcc.Store(id=f'{APP_ID}_keyframes_tr_store'),
                dcc.Store(id=f'{APP_ID}_keyframes_br_store')
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody([
                html.H3('Saved Sequences', className="card-title"),
                dbc.Row([
                    dbc.Col([
                            html.Div(id=f'{APP_ID}_live_update_sequences')
                        ])
                    ]),
                ])
            ),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )        
    ])
    
    return layout

        
def add_spotlights_dashboard(dash_app):
    
    def generate_keyframes(second: int):
    
        return html.Div([dcc.Slider(0, 255, 5,
                               value=0,
                               marks=None,
                               id={"type": "keyframe", "index": second},
                               vertical=True,
                               verticalHeight=200)],
        style= {'transform': 'scale(0.8)', 'margin-right': '-25px'})
    
    @dash_app.callback(Output(f'{APP_ID}_keyframes', 'children'),
              [Input(f'{APP_ID}_t_length_input', 'value')])
    def update_keyframes(seconds_length: float= None):
        if not seconds_length or seconds_length > max_sequence_length:
            seconds_length = max_sequence_length
        return [generate_keyframes(i) for i in range(int(seconds_length))]
    
    

    @dash_app.callback(
        [
            Output(f'{APP_ID}_keyframes_bl_store', "data"),
            Output(f'{APP_ID}_keyframes_tl_store', "data"),
            Output(f'{APP_ID}_keyframes_tr_store', "data"),
            Output(f'{APP_ID}_keyframes_br_store', "data"),
        ],
        [
            Input({'type': 'keyframe', 'index': ALL}, 'value'),
            State(f'{APP_ID}_spot_selector', "value"),
            State(f'{APP_ID}_keyframes_bl_store', "data"),
            State(f'{APP_ID}_keyframes_tl_store', "data"),
            State(f'{APP_ID}_keyframes_tr_store', "data"),
            State(f'{APP_ID}_keyframes_br_store', "data"),
        ],
        prevent_initial_call=True
    )
    def store_keyframe_array(keyframe, spot_selector, keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br): 
        if not keyframes_bl or len(keyframes_bl) != len(keyframe):
            keyframes_bl = [0]*len(keyframe)
        if not keyframes_tl  or len(keyframes_tl) != len(keyframe):
            keyframes_tl = [0]*len(keyframe)
        if not keyframes_tr  or len(keyframes_tr) != len(keyframe):
            keyframes_tr = [0]*len(keyframe)
        if not keyframes_br  or len(keyframes_br) != len(keyframe):
            keyframes_br = [0]*len(keyframe)
        if spot_selector == 'Bottom Left':
            keyframes_bl = keyframe
        if spot_selector == 'Top Left':
            keyframes_tl = keyframe
        if spot_selector == 'Top Right': 
            keyframes_tr = keyframe
        if spot_selector == 'Bottom Right':
            keyframes_br = keyframe
        return keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br
    
    @dash_app.callback(
        Output(f'{APP_ID}_keyframes', 'children'),
        [
            Input(f'{APP_ID}_spot_selector', "value"),
            State(f'{APP_ID}_keyframes_bl_store', "data"),
            State(f'{APP_ID}_keyframes_tl_store', "data"),
            State(f'{APP_ID}_keyframes_tr_store', "data"),
            State(f'{APP_ID}_keyframes_br_store', "data")
        ],
        prevent_initial_call=True
              )
    def load_keyframes(spot_selector, keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br):
        if spot_selector == 'Bottom Left':
            keyframes = load_keyframes_generator(keyframes_bl)
        if spot_selector == 'Top Left':
            keyframes = load_keyframes_generator(keyframes_tl)
        if spot_selector == 'Top Right': 
            keyframes = load_keyframes_generator(keyframes_tr)
        if spot_selector == 'Bottom Right':
            keyframes = load_keyframes_generator(keyframes_br)
        return keyframes
    
    def load_keyframes_generator(keyframes):
        second = 0
        keyframe_list = []
        for i in keyframes:
            keyframe_list.append(html.Div([dcc.Slider(0, 255, 5,
                                   value=i,
                                   marks=None,
                                   id={"type": "keyframe", "index": second},
                                   vertical=True,
                                   verticalHeight=100)],
                                       style= {'transform': 'scale(0.8)', 'margin-right': '-25px'}))
            second += 1
        return keyframe_list
        
    return dash_app 

                    
def add_video_editing_dashboard(dash_app):
    
    def generate_available_sequence(sequence_name: str):
    
        return dbc.Row([
                    dbc.ButtonGroup([
                        html.P(str(sequence_name), style={"width": "300px"}),
                        dbc.Button(children='Send',
                            color="primary",
                            className="mr-1",
                            id={"type": "send_button", "index": str(sequence_name)}),
                        dbc.Button(children='Delete',
                            color="primary",
                            className="mr-1",
                            id={"type": "delete_button", "index": str(sequence_name)})
                    ], style={"margin-left": "50px"})
                ])
        
    
    @dash_app.callback(Output(f'{APP_ID}_live_update_sequences', 'children'),
              Input('interval-component', 'n_intervals'))
    def update_available_sequences(n):
        return [dbc.Col([
                    generate_available_sequence(i) for i in file_utils.list_movies()
                    ])]

    @du.callback(
        output=Output(f'{APP_ID}_large_upload_fn_store', 'data'),
        id=f'{APP_ID}_large_upload',
    )
    def get_a_list(filenames):
        return {i: filenames[i] for i in range(len(filenames))}


    @dash_app.callback(
        [
            Output(f'{APP_ID}_status', 'children')
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
    
    
    @dash_app.callback(
        Output({"type": "delete_button", "index": MATCH}, "children"),
        Input({"type": "delete_button", "index": MATCH}, "n_clicks"),
        State({"type": "delete_button", "index": MATCH}, "id"),
    )
    def delete_saved_sequence(n_clicks, id):
        if n_clicks:
            sequence_filename = id['index']
            file_utils.delete_sequence(sequence_filename)
        return 'Delete'
    
    @dash_app.callback(
        Output({"type": "send_button", "index": MATCH}, "children"),
        Input({"type": "send_button", "index": MATCH}, "n_clicks"),
        State({"type": "send_button", "index": MATCH}, "id"),
        State(f'{APP_ID}_frame_id', 'value'),
    )       
    def send_saved_sequence(n_clicks, id: str, frame_id: str):
        if n_clicks:
            sequence_filename = id['index']
            file_utils.send_saved_sequence(sequence_filename, frame_id)
        return 'Send'
    
    
    @dash_app.callback(Output(f'{APP_ID}_update_video', 'children'),
            [
                Input(f'{APP_ID}_thickness_input', 'value'),
                Input(f'{APP_ID}_large_upload_fn_store', 'data'),
                Input(f'{APP_ID}_t_start_input', 'value'),
                Input(f'{APP_ID}_t_length_input', 'value'),
                Input(f'{APP_ID}_rect_bot_input', 'value'),
                Input(f'{APP_ID}_rect_top_input', 'value'),
                Input(f'{APP_ID}_rect_left_input', 'value'),
                Input(f'{APP_ID}_rect_right_input', 'value'),
                Input(f'{APP_ID}_brightness_input', 'value'),
                Input(f'{APP_ID}_contrast_input', 'value'),
                Input(f'{APP_ID}_black_input', 'value'),
                Input(f'{APP_ID}_led_hor', 'value'),
                Input(f'{APP_ID}_led_ver', 'value'),
                Input(f'{APP_ID}_video_filename', 'value'),
                Input(f'{APP_ID}_keyframes_bl_store', 'data'),
                Input(f'{APP_ID}_keyframes_tl_store', 'data'),
                Input(f'{APP_ID}_keyframes_tr_store', 'data'),
                Input(f'{APP_ID}_keyframes_br_store', 'data')
            ])
    def update_video(thickness, dic_of_names, clip_start, clip_length, rect_bot, rect_top, rect_left, rect_right, 
                     brightness, contrast, black, led_hor, led_ver, video_filename, keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br):
        rect_top = video_to_led.clip_height - rect_top
        rect_right = video_to_led.clip_width - rect_right
        clip_end = clip_start + clip_length
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
        keyframe_bl_string = ','.join(str(x) for x in keyframes_bl)
        keyframe_tl_string = ','.join(str(x) for x in keyframes_tl)
        keyframe_tr_string = ','.join(str(x) for x in keyframes_tr)
        keyframe_br_string = ','.join(str(x) for x in keyframes_br)
        video_feed_url = f'{URL_BASE}video_feed/{path_base64_string}/{filename_base64_string}/{rect_bot}/{rect_top}/{rect_left}/{rect_right}/{clip_start}/{clip_end}/{thickness}/{brightness}/{contrast}/{black}/{led_hor}/{led_ver}/{keyframe_bl_string}/{keyframe_tl_string}/{keyframe_tr_string}/{keyframe_br_string}'
        if os.path.exists(os.path.join(path, filename)):
            return html.Img(src=video_feed_url, style={'width': '500px'})
    
   
    @dash_app.callback(Output(f'{APP_ID}_status', 'children'),
            [
                State(f'{APP_ID}_frame_id', 'value'),
                State(f'{APP_ID}_led_hor', 'value'),
                State(f'{APP_ID}_led_ver', 'value'),
                Input(f'{APP_ID}_send_config', 'n_clicks')
            ])
    def send_config(frame_id: str, led_hor: int, led_ver: int, n_clicks):
        if n_clicks:
            led_count = 2*(led_hor + led_ver)
            return  Configurator.send_config(frame_id, led_count)
         
         
    @dash_app.callback(Output(f'{APP_ID}_status', 'children'),
            [
                State(f'{APP_ID}_thickness_input', 'value'),
                State(f'{APP_ID}_large_upload_fn_store', 'data'),
                State(f'{APP_ID}_t_start_input', 'value'),
                State(f'{APP_ID}_t_length_input', 'value'),
                State(f'{APP_ID}_rect_bot_input', 'value'),
                State(f'{APP_ID}_rect_top_input', 'value'),
                State(f'{APP_ID}_rect_left_input', 'value'),
                State(f'{APP_ID}_rect_right_input', 'value'),
                State(f'{APP_ID}_video_filename', 'value'),
                State(f'{APP_ID}_frame_id', 'value'),
                State(f'{APP_ID}_brightness_input', 'value'),
                State(f'{APP_ID}_contrast_input', 'value'),
                State(f'{APP_ID}_keyframes_bl_store', 'data'),
                State(f'{APP_ID}_keyframes_tl_store', 'data'),
                State(f'{APP_ID}_keyframes_tr_store', 'data'),
                State(f'{APP_ID}_keyframes_br_store', 'data'),
                State(f'{APP_ID}_black_input', 'value'),
                State(f'{APP_ID}_led_hor', 'value'),
                State(f'{APP_ID}_led_ver', 'value'),
                Input(f'{APP_ID}_send_sequence', 'n_clicks')
            ])
    def send_to_frame(thickness, dic_of_names, clip_start, clip_length, rect_bot, rect_top, rect_left, 
                      rect_right, video_filename, frame_id, brightness, contrast, 
                      keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br, black, led_hor, led_ver, n_clicks):
        if n_clicks:
            clip_end = clip_start + clip_length
            if not frame_id:
                return 'Please enter Frame ID'
            rect_top = video_to_led.clip_height - rect_top
            rect_right = video_to_led.clip_width - rect_right
            path = os.path.join('apps', 'static', 'assets', '.temp')
            filename = "color stripes.mp4"
            if video_filename:
                filename = video_filename
            video_for_download = VideoToLed(username)
            video_for_download.set_led_count(led_hor, led_ver)
            video_for_download.open_video_from_file(path, filename)
            video_for_download.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
            video_for_download.set_start_end_sec(int(clip_start), int(float(clip_end)))
            video_for_download.set_brightness_contrast(int(brightness), int(float(contrast)), int(float(black)))
            video_for_download.set_spot_keyframes(keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br)
            validation = video_for_download.validate_settings()
            if validation != 'ok':
                return validation
            return video_for_download.send_over_mqtt(frame_id)
        
    @dash_app.callback(Output(f'{APP_ID}_status', 'children'),
            [
                State(f'{APP_ID}_thickness_input', 'value'),
                State(f'{APP_ID}_large_upload_fn_store', 'data'),
                State(f'{APP_ID}_t_start_input', 'value'),
                State(f'{APP_ID}_t_length_input', 'value'),
                State(f'{APP_ID}_rect_bot_input', 'value'),
                State(f'{APP_ID}_rect_top_input', 'value'),
                State(f'{APP_ID}_rect_left_input', 'value'),
                State(f'{APP_ID}_rect_right_input', 'value'),
                State(f'{APP_ID}_video_filename', 'value'),
                State(f'{APP_ID}_sequence_name', 'value'),
                State(f'{APP_ID}_brightness_input', 'value'),
                State(f'{APP_ID}_contrast_input', 'value'),
                State(f'{APP_ID}_keyframes_bl_store', 'data'),
                State(f'{APP_ID}_keyframes_tl_store', 'data'),
                State(f'{APP_ID}_keyframes_tr_store', 'data'),
                State(f'{APP_ID}_keyframes_br_store', 'data'),
                Input(f'{APP_ID}_black_input', 'value'),
                State(f'{APP_ID}_led_hor', 'value'),
                State(f'{APP_ID}_led_ver', 'value'),
                Input(f'{APP_ID}_save_sequence', 'n_clicks')
            ])
    def save_sequence(thickness, dic_of_names, clip_start, clip_length, rect_bot, rect_top, rect_left, 
                      rect_right, video_filename, sequence_name, brightness, contrast, 
                      keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br, black, led_hor, led_ver, n_clicks):
        if n_clicks:
            clip_end = clip_start + clip_length
            rect_top = video_to_led.clip_height - rect_top
            rect_right = video_to_led.clip_width - rect_right
            path = os.path.join('apps', 'static', 'assets', '.temp')
            filename = "color stripes.mp4"
            if video_filename:
                filename = video_filename
            video_for_download = VideoToLed(username)
            video_for_download.set_led_count(led_hor, led_ver)
            video_for_download.open_video_from_file(path, filename)
            video_for_download.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
            video_for_download.set_start_end_sec(int(clip_start), int(float(clip_end)))
            video_for_download.set_brightness_contrast(int(brightness), int(float(contrast)), int(float(black)))
            video_for_download.set_spot_keyframes(keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br)
            validation = video_for_download.validate_settings()
            if validation != 'ok':
                return validation
            return video_for_download.save_sequence(sequence_name)
        
    @dash_app.callback(Output(f'{APP_ID}_video_filename', 'value'),
                Input(f'{APP_ID}_youtube_load_button', 'n_clicks'),
                State(f'{APP_ID}_youtube_url', 'value')
                )
    def load_youtube_video(nclicks:int, url: str):
        payload = ''
        if url:
            payload = video_to_led.load_youtube_video(url=url)
        return payload
    
        
    @dash_app.server.route(f'{URL_BASE}video_feed/<string:path_encoded>/<string:filename_encoded>/<rect_bot>/<rect_top>/<rect_left>/<rect_right>/<t_start>/<t_end>/<thickness>/<brightness>/<contrast>/<black>/<led_hor>/<led_ver>/<keyframes_bl>/<keyframes_tl>/<keyframes_tr>/<keyframes_br>')
    def video_feed(path_encoded, filename_encoded, rect_bot, rect_top, rect_left, rect_right, t_start, t_end, thickness,brightness, contrast, black, led_hor, led_ver, keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br):
        path_base64_bytes = path_encoded.encode("ascii")
        path_base64_bytes = base64.b64decode(path_base64_bytes)
        path_decoded = path_base64_bytes.decode("ascii")
        filename_base64_bytes = filename_encoded.encode("ascii")
        filename_base64_bytes = base64.b64decode(filename_base64_bytes)
        filename_decoded = filename_base64_bytes.decode("ascii")
        video_to_led_feed = VideoToLed(username)
        video_to_led_feed.set_led_count(int(led_hor), int(led_ver))
        video_to_led_feed.open_video_from_file(path_decoded, filename_decoded)
        video_to_led_feed.set_rectangle(int(rect_bot), int(rect_top), int(rect_left), int(rect_right), int(thickness))
        video_to_led_feed.set_start_end_sec(int(t_start), int(float(t_end)))
        video_to_led_feed.set_brightness_contrast(float(brightness), int(float(contrast)), int(float(black)))
        keyframes_bl = [int(x) for x in keyframes_bl.split(",")]
        keyframes_tl = [int(x) for x in keyframes_tl.split(",")]
        keyframes_tr = [int(x) for x in keyframes_tr.split(",")]
        keyframes_br = [int(x) for x in keyframes_br.split(",")]
        video_to_led_feed.set_spot_keyframes(keyframes_bl, keyframes_tl, keyframes_tr, keyframes_br)
        if video_to_led_feed.is_playing:
            video_to_led_feed.restart()
        return Response(video_to_led_feed.start(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
        
        
    @dash_app.server.route('/downloads/<path:path>')
    def serve_static(path):
        return send_from_directory(
            Path("downloads"), path, as_attachment=True
        )
        
        
    @dash_app.callback(
    Output(f'{APP_ID}_send_sequence','disabled'),
    [Input(f'{APP_ID}_frame_id','value')])
    def activate_send_button(frame_id):
        if frame_id and len(frame_id) > 4:
            return False
        
    @dash_app.callback(
    Output(f'{APP_ID}_send_config','disabled'),
    [Input(f'{APP_ID}_frame_id','value'),
     Input(f'{APP_ID}_led_count','value'),
     State(f'{APP_ID}_frame_id','value'),
     State(f'{APP_ID}_led_count','value')])
    def activate_config_button(f, l, frame_id, led_count):
        if frame_id and len(frame_id) > 4 and led_count:
            return False
        
    @dash_app.callback(
    Output(f'{APP_ID}_save_sequence','disabled'),
    [Input(f'{APP_ID}_sequence_name','value')])
    def activate_save_button(sequence_name):
        if sequence_name and len(sequence_name) > 0:
            return False

    return dash_app 
  
    


def init_dash(server):
    
    external_stylesheets = [
        dbc.themes.BOOTSTRAP,
        dbc.themes.SLATE
    ]
    
    # Setup Dash app
    dash_app = Dash(__name__, server=server, 
                    url_base_pathname=URL_BASE,
                    update_title = None,
                    external_stylesheets=external_stylesheets)
    dash_app.config['suppress_callback_exceptions'] = True
    du.configure_upload(dash_app, Path.cwd() / Path("video_temp"), use_upload_id=False, upload_api=URL_BASE+"API/resumable")
    
    dash_app.layout = get_layout()
    dash_app = add_video_editing_dashboard(dash_app)
    dash_app = add_spotlights_dashboard(dash_app)
    
    return dash_app.server

