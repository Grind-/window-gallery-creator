from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from multiprocessing import Queue
import os
from queue import Empty
import random
from threading import Thread
import time
from typing import Dict, Any, Set
from urllib.parse import urlparse

from op.basyx.config.service import ConfigService
from op.basyx.logging_helper import get_named_logger
from paho.mqtt.client import Client, ssl


_DEFAULT_MQTT_URL = "mqtt://data:password@localhost:1883"
_DEFAULT_MQTT_info = False


@dataclass
class MqttConfig:
    host: str = "localhost"
    port: int = 1883
    username: str = None
    password: str = None
    tls: bool = False


class AbstractQueueableMqttClient(ABC):
    @abstractmethod
    def map_topic_to_queue(self, topic: str, queue: Any) -> Any:
        pass

    @abstractmethod
    def stop_topic_to_queue_streaming(self, topic: str) -> None:
        pass

    @abstractmethod
    def map_queue_to_topic(self, queue: Any, topic: str) -> None:
        pass

    @abstractmethod
    def stop_queue_to_topic_streaming(self, topic: str) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class QueueableMqttClient(AbstractQueueableMqttClient):
    @classmethod
    def from_config_service(cls, client_id_prefix: str, cfg_service: ConfigService= None) -> AbstractQueueableMqttClient:
        """
        This method should be generally used to create QueueableMqttClient instance
        """
        if not cfg_service:
            cfg_service = ConfigService.get_instance()
        cfg = cfg_service.get_config()
        host = cfg["mqtt"]["host"]
        port = int(cfg["mqtt"]["port"])
        user = cfg["mqtt"]["user"]
        password = cfg["mqtt"]["pass"]
        transport = cfg["mqtt"]["transport"]
        tls = cfg["mqtt"]["tls"] == "True"
        return cls(
            client_id_prefix=client_id_prefix,
            host=host,
            port=port,
            username=user,
            password=password,
            transport=transport,
            tls=tls,
        )

    @classmethod
    def from_config(cls, client_id_prefix: str, config: MqttConfig) -> AbstractQueueableMqttClient:
        return cls(
            client_id_prefix=client_id_prefix,
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            tls=config.tls,
        )

    @classmethod
    def url_to_mqtt_config(cls, url: str = None) -> MqttConfig:
        """
        :param url: if empty or none it will take $MQTT_URL or default_url
        :return:
        """
        if not url:
            url = _DEFAULT_MQTT_URL
        # if not url:
        #     return self.url_to_mqtt_config(os.environ.get("MQTT_URL", _DEFAULT_MQTT_URL))
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ("mqtt", "mqtts"):
            raise RuntimeError(f"Invalid url scheme: '{parsed_url.scheme}'")
        tls = str(parsed_url.scheme) == "mqtts"
        username = ""
        if parsed_url.username:
            username = str(parsed_url.username)
        password = ""
        if parsed_url.password:
            password = str(parsed_url.password)
        default_port = 8883 if tls else 1883
        # print("Connecting to ", re.sub(r":[^@]+@", ":xxxxxx@", url))
        return MqttConfig(
            host=str(parsed_url.hostname),
            port=parsed_url.port or default_port,
            username=username,
            password=password,
            tls=tls,
        )

    @classmethod
    def from_url(cls, client_id_prefix: str, url: str = "") -> AbstractQueueableMqttClient:
        return cls.from_config(client_id_prefix=client_id_prefix, config=cls.url_to_mqtt_config(url))

    @classmethod
    def from_environ(cls, client_id_prefix: str) -> AbstractQueueableMqttClient:
        url = os.environ.get("MQTT_URL", _DEFAULT_MQTT_URL)
        return cls.from_config(client_id_prefix=client_id_prefix, config=cls.url_to_mqtt_config(url))

    def __init__(
        self,
        client_id_prefix: str,
        host: str = "localhost",
        port: int = 1883,
        username: str = None,
        password: str = None,
        qos: int = 0,
        clean_session: bool = False,
        tls=False,
        transport: str = "tcp",
        queue_maxsize: int = 10000,
        timeout: int = 30,
        mqtt_info: bool = _DEFAULT_MQTT_info,
    ) -> None:
        """
        client_id_prefix is prefix of client_id used when connecting to the broker.

        host is the hostname or IP address of the remote broker.

        port is the network port of the server host to connect to. Defaults to
        1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
        are using tls_set() the port may need providing.

        username is the username to authenticate with. Need have no relationship to
        the client id. Must be unicode [MQTT-3.1.3-11].
        Set to None to reset client back to not using username/password for broker authentication.

        password is the password to authenticate with. Optional, set to None if not required.
        If it is unicode, then it will be encoded as UTF-8.

        qos is the desired quality of service level

        clean_session is a boolean that determines the client type. If True,
        the broker will remove all information about this client when it
        disconnects. If False, the client is a persistent client and
        subscription information and queued messages will be retained when the
        client disconnects.

        tls should be set to True for using MQTT over SSL/TLS. Current implementation
        expects installation of certificate at the operating system.

        Set transport to "websockets" to use WebSockets as the transport
        mechanism. Set to "tcp" to use raw TCP, which is the default.

        queue_maxsize is queues size limit

        timeout - time limit in seconds

        mqtt_info should be True to switch on mqtt info messages
        """

        self._logger = get_named_logger(QueueableMqttClient)

        self._queue_maxsize = queue_maxsize
        self._timeout = timeout
        self._mqtt_info = mqtt_info
        self._qos = qos
        self._host = host
        self._port = port

        self._mqtt = Client(
            f"{client_id_prefix}_{random.random()*10000000}",
            clean_session=clean_session,
            transport=transport,
        )
        # if tls:
        #     self._mqtt.tls_set(tls_version=ssl.PROTOCOL_TLS)
        # if username:
        #     self._mqtt.username_pw_set(username, password)
        if tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            # ignore host name setting in certificate
            context.check_hostname = False
            self._mqtt.tls_set_context(context)
        if username is not None and len(username) > 0:
            self._mqtt.username_pw_set(username, password)

        self._mqtt.on_message = self._mqtt_on_message
        self._mqtt.on_connect = self._mqtt_on_connect
        self._mqtt.on_subscribe = self._mqtt_on_subscribe
        self._mqtt.on_publish = self._mqtt_on_publish
        self._mqtt.on_disconnect = self._mqtt_on_disconnect
        self._mqtt.on_log = self._mqtt_on_log

        self._switched_on = False

        self._running_loop = False
        self._bad_connection_flag = False
        self._connected_flag = False
        self._suback_set: Set[Any] = set()

        self._write_queues_dic: Dict[str, Any] = {}
        self._read_queues_dic: Dict[str, Any] = {}

    def _mqtt_on_connect(self, mqttc, obj, flags, rc):  # type: ignore
        if rc == 0:
            self._connected_flag = True
            self._logger.info("connected OK")
        else:
            self._logger.error(f"Bad connection Returned code= {rc}")
            self._bad_connection_flag = True

    def _mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):  # type: ignore
        self._logger.info("on_subscribe mid = " + str(mid))
        self._suback_set.add(str(mid))

    def _mqtt_on_publish(self, mqttc, obj, mid):  # type: ignore
        self._logger.info(f"on_publish: mid: {mid}")

    def _mqtt_on_disconnect(self, client, userdata, rc):  # type: ignore
        self._logger.info("disconnected with " + str(client._client_id))
        self._connected_flag = False

    def _mqtt_on_log(self, client, userdata, level, buff):  # type: ignore
        if self._mqtt_info:
            self._logger.info(f"Paho log level={level}, buff={buff}")

    def _mqtt_on_message(self, mqtt, obj, msg):  # type: ignore
        self._logger.info("on_message: " + msg.topic + " " + str(msg.payload))
        msg_payload = None
        try:
            msg_payload = json.loads(msg.payload.decode("utf-8"))
        except:
            self._logger.error(f"mqtt_on_message: malformed message {msg.payload}")
        else:
            topic = msg.topic
        if not msg.topic in self._write_queues_dic:
            topic = self._map_wildcard_topic(msg.topic, self._write_queues_dic)
        if topic:
            self._write_queues_dic[topic].put(msg_payload)
        else:
            print(
                f"{os.getpid()} queueable_client._mqtt_on_message  / mqtt_on_message: topic not in queue: {msg.topic}"
            )
            
    def _map_wildcard_topic(self, topic: str, queue_dict: dict) -> str:
        for key in queue_dict:
            if topic.startswith(key.rstrip("*#")):
                return key
        return None
    
    def map_queue_to_topic(self, queue: Any, topic: str) -> None:
        self._logger.info(f"map_queue_to_topic: topic {topic}")
        if self._connected_flag and topic in self._read_queues_dic or not self._connected_flag:
            # set or update topic queue
            self._read_queues_dic[topic] = queue
        else:
            self._read_queues_dic[topic] = queue
            self._start_worker(topic)

    def stop_queue_to_topic_streaming(self, topic: str) -> None:
        self._logger.info(f"stop_queue_to_topic_streaming: topic {topic}")
        self._stop_worker(topic)

    def map_topic_to_queue(self, topic: str, queue: Any) -> Any:
        self._logger.info(f"map_topic_to_queue: topic {topic}")

        q: Queue[Any] = Queue(maxsize=self._queue_maxsize) if queue is None else queue
        self._write_queues_dic[topic] = q
        if self._connected_flag:
            (result, mid) = self._mqtt.subscribe(topic, self._qos)
            timeout_start = time.time()
            while not str(mid) in self._suback_set:
                if time.time() < timeout_start + self._timeout:
                    time.sleep(0.1)
                else:
                    self._logger.error(f"error: in subscribe_all suback timeout mid = {mid}")
                    return None
            self._logger.info("subscribe MID: " + str(mid))
            self._suback_set.remove(str(mid))
        return q

    def stop_topic_to_queue_streaming(self, topic: str) -> None:
        self._logger.info(f"stop_topic_to_queue_streaming: topic {topic}")
        if topic in self._write_queues_dic:
            del self._write_queues_dic[topic]
            if self._connected_flag:
                self._mqtt.unsubscribe(topic)

    def _subscribe_all(self) -> Dict[str, Any]:
        self._logger.info("_subscribe_all")
        topics = set(self._write_queues_dic.keys())
        if len(topics) > 0:
            timeout_start = time.time()
            while not self._connected_flag:
                if time.time() < timeout_start + self._timeout:
                    time.sleep(0.1)
                else:
                    self._logger.error("subscribe_all: connected_flag timeout")
                    return {"error": "in subscribe_all connected_flag timeout"}
            subscr_list = [(topic, self._qos) for topic in topics]
            (result, mid) = self._mqtt.subscribe(subscr_list, self._qos)
            timeout_start = time.time()
            while not str(mid) in self._suback_set:
                if time.time() < timeout_start + self._timeout:
                    time.sleep(0.1)
                else:
                    self._logger.error(f"error: in subscribe_all suback timeout mid = {mid}")
                    return {"error": f"in subscribe_all suback timeout mid = {mid}"}
            self._suback_set.remove(str(mid))
            return {"mid": mid}
        else:
            return {}

    def _process(self, topic: str) -> None:
        self._logger.info(f"_process: topic = {topic}")
        while topic in self._read_queues_dic:
            try:
                q = self._read_queues_dic[topic]
                msg = q.get(timeout=1)
                self._logger.info(f"publish to {topic}: {msg}")
                json_utf_8_msg = json.dumps(msg).encode("utf-8")
                self._mqtt.publish(topic, json_utf_8_msg, self._qos)
            except Empty:
                continue

    def _start_worker(self, topic: str) -> None:
        self._logger.info(f"_start_worker: topic = {topic}")
        t = Thread(target=self._process, args=(topic,))
        t.setDaemon(True)
        t.start()

    def _start_all_workers(self) -> None:
        self._logger.info("_start_all_workers")
        for topic in self._read_queues_dic:
            self._start_worker(topic)

    def _stop_all_workers(self) -> None:
        self._read_queues_dic = {}

    def _stop_worker(self, topic: str) -> None:
        if topic in self._read_queues_dic:
            del self._read_queues_dic[topic]

    def start(self) -> None:
        self._switched_on = True
        self._logger.info("start")
        self._bad_connection_flag = False
        if not self._connected_flag:
            timeout_start = time.time()
            self._logger.info(f"Connecting to {self._host}:{self._port}")
            self._mqtt.connect(self._host, self._port)
            if not self._running_loop:
                self._mqtt.loop_start()  # type:ignore
                self._running_loop = True
            while not self._connected_flag and not self._bad_connection_flag:
                if time.time() < timeout_start + self._timeout:
                    time.sleep(0.1)
                else:
                    self._logger.error(
                        f"connection fail connected_flag: {self._connected_flag} bad_connection_flag {self._bad_connection_flag}"
                    )
                    self._bad_connection_flag = True
            if self._bad_connection_flag and self._running_loop:
                self._mqtt.loop_stop()
                self._running_loop = False
            if self._bad_connection_flag:
                raise ConnectionError(
                    f"connection fail connected_flag: {self._connected_flag} bad_connection_flag {self._bad_connection_flag}"
                )
            self._subscribe_all()
            self._start_all_workers()

    def stop(self) -> None:
        self._switched_on = False
        self._logger.info("stop")
        self._stop_all_workers()
        self._running_loop = False
        self._mqtt.loop_stop()
        self._mqtt.disconnect()
        self._connected_flag = False

    def __del__(self):
        if self._switched_on:
            self.stop()
