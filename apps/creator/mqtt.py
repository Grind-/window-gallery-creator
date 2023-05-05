'''
Created on 05.08.2022

@author: jhirte
'''
from json import loads

from threading import Thread
import atexit
import requests
import pickle

import paho.mqtt.client as mqtt


config = {}
config['frame_id'] = '0000001'
config['topic_sequence'] = '/frame/' + config['frame_id'] + '/sequence/'
config['topic_frame_connected'] = '/frame_connected/'
config['client_id'] = 'window_gallery'
config['password'] = 'password'
mqtt_host = "81.169.134.31"
mqtt_port = 1883
        
class MqttCore():
    def __init__(self):
        self.config = config

    def start(self, subscription_name: str=None, mqtt_config: dict=None):
        if subscription_name:
            self.subscription_name = self.derive_subscription_name(subscription_name)
            atexit.register(self.stop, subscription_name)
            
        self.mqtt_config = mqtt_config

        global mqtt_subscriber
        mqtt_subscriber = MqttSubscriberThread(self.config)
        mqtt_subscriber.start()

        if mqtt_subscriber.is_running:
            return 'Subscription running'
        else:
            return 'Subscription error'

    def stop(self, subscription_name: str=None):
        if subscription_name:
            subscription_name = self.derive_subscription_name(subscription_name)
        global mqtt_subscriber
        mqtt_subscriber.shutdown()
        return 'Subscription stopped'
    
    def publish(self, topic: str, payload: str):
        mqtt_subscriber.publish(topic=topic, payload=payload)
        
    def subscribe(self, topic: str):
        mqtt_subscriber.subscribe(topic=topic)
        
    def get_sequence(self):
        return {'sequence_name' : mqtt_subscriber.sequence_name,
                'sequence' : mqtt_subscriber.sequence}

    def derive_subscription_name(self, subscription_name):
        return str(hash(subscription_name))


class MqttSubscriberThread(Thread):

    def __init__(self, config: dict):
        self.is_running = False
        Thread.__init__(self)
        self.config = config
        self.sequence = []
        self.sequence_name = ''
        
        # mqtt_url = "wss://enterprise-messaging-messaging-gateway.cfapps.eu10.hana.ondemand.com/protocols/mqtt311ws"


        # If you want to use a specific client id, use
        # mqttc = mqtt.Client("client-id")
        # but note that the client id must be unique on the broker. Leaving the client
        # id parameter empty will generate a random id for you.

        #self.mqttc = mqtt.Client(transport="websockets", client_id=clientid, clean_session=False, protocol=mqtt.MQTTv311)
        self.mqttc = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.on_subscribe = self.on_subscribe

        # self.mqttc.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
        # self.mqttc.tls_insecure_set(False)
        clientid = self.config['client_id']
        clientsecret = self.config['password']
        self.mqttc.username_pw_set(clientid, clientsecret)

        self.mqttc.on_log = self.on_log
        self.mqttc.connect(mqtt_host, mqtt_port)

    def on_connect(self, mqttc, obj, flags, rc):
        print("connected: " + str(rc))
        self.publish(self.config['topic_frame_connected'], self.config['frame_id'])
        self.subscribe(self.config['topic_frame_connected']+'#')
        #self.subscribe(self.config['topic_sequence']+'#')

    def on_disconnect(self, client, userdata, rc):
        print("disconnected: " + str(rc))

    def on_message(self, mqttc, obj, msg):
        # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

        # data = msg.payload.decode("utf-8")
        # data_dict = loads(data)
        if msg.topic.startswith(self.config['topic_sequence']):
            data =  msg.payload
            # self.sequence = pickle.loads(data)
            # self.sequence_name = msg.topic.rsplit('/', 1)[-1]
            print('received sequence: ' + str(data))

    def on_publish(self, mqttc, obj, mid):
        print("published: " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.is_running = True
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        # print(string)
        pass

    def get_access_token(self, url, client_id, client_secret):
        response = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        return response.json()["access_token"]

    def run(self):
        self.mqttc.loop_forever(timeout=0.0)
        
    def publish(self, topic: str, payload: str):
        print(f'publishing {payload} to topic {topic}')
        self.mqttc.publish(topic, payload=payload, qos=1, retain=False)
        
    def subscribe(self, topic: str):
        self.mqttc.subscribe(topic, 1)

    def shutdown(self):
        self.mqttc.unsubscribe(self.config['topic_sequence']+'#')
        self.mqttc.disconnect()
        self.is_running = False
