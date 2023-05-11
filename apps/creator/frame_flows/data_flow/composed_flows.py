import multiprocessing
from typing import Dict, Any

import isodate
from op.basyx.basyx_generic_sensor.time_series_utils.data_flow.composed_flows import (
    AbstractFlowsManager,
    AbstractComposedFlow,
)

from op.basyx.caas_kaugummiautomaten.flow_provider.data_flow.queueable_flow import (
    to_df_msg_flow,
    df_to_mqtt_manager_status_flow,
    dict_to_rotation_flow
)
from op.basyx.caas_kaugummiautomaten.utils.mqtt.queueable_client import (
    QueueableMqttClient,
)


class MqttRotations2RotationsFlowManager(AbstractFlowsManager):
    def start_flow(self, flow_config_dict: Dict[str, Any]) -> str:
        if flow_config_dict["topic"] not in self.flows_dict:
            self.flows_dict[flow_config_dict["topic"]] = (
                MqttRotations2RotationsStateFlow.from_config_dict(flow_config_dict),
                MqttTopic2MqttManagerStatusFlow.from_config_dict(flow_config_dict),
            )
            for flow in self.flows_dict[flow_config_dict["topic"]]:
                flow.start()
            return flow_config_dict["topic"]

    def stop_flow(self, flow_id) -> None:
        if flow_id in self.flows_dict:
            for flow in self.flows_dict[flow_id]:
                flow.stop()
            del self.flows_dict[flow_id]

    def stop(self) -> None:
        for flow_id in list(self.flows_dict.keys()):
            self.stop_flow(flow_id)
        self.flows_dict.clear()

    def __init__(self):
        self.flows_dict = {}

    def __del__(self):
        if len(self.flows_dict) > 0:
            self.stop()


class MqttRotations2RotationsStateFlow(AbstractComposedFlow):
    """
    classdocs
    """

    def stop(self) -> None:
        if self.started:
            self.qmc.stop_topic_to_queue_streaming(topic=self.topic)
            self.sensor_messages_queue.put(None)
            self.qtsm.stop()
            self.qmc.stop()
            self.started = False

    def start(self) -> None:
        if not self.started:
            self.started = True
            self.qmc.start()
            self.qmc.map_topic_to_queue(
                topic=self.topic, queue=self.sensor_messages_queue
            )
            self.internal_segment_process.start()

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> AbstractComposedFlow:
        """
        dictionary example:

        {
            'topic': 'sensor1',
            'timeseries_ref': <Reference>,
            'internal_cache_duration': "00:03:00",
            'time_column': "Time"
        }

        """
        return cls(
            topic=config_dict["topic"],
            timeseries_ref=config_dict["timeseries_ref"],
            internal_cache_duration=config_dict["internal_cache_duration"],
            time_column=config_dict["time_column"],
        )

    def __init__(
        self,
        topic: str,
        timeseries_ref=None,
        internal_cache_duration="P30M5",
        time_column="Time",
    ):
        """
        Constructor
        """
        self.started = False
        self.topic = topic + "/rotations"
        duration = isodate.parse_duration(internal_cache_duration)

        self.sensor_messages_queue = multiprocessing.Queue()
        self.qmc = QueueableMqttClient.from_config_service(
            client_id_prefix=self.__class__.__name__
        )

        self.internal_segment_process = multiprocessing.Process(
            target=dict_to_rotation_flow,
            args=(  # input queue
                self.sensor_messages_queue,
                duration,
                timeseries_ref,
                time_column,
            ),
        )

        self.internal_segment_process.daemon = True


class MqttTopic2MqttManagerStatusFlow(AbstractComposedFlow):
    """
    classdocs
    """

    def stop(self) -> None:
        if self.started:
            self.qmc.stop_topic_to_queue_streaming(topic=self.topic)
            self.sensor_messages_queue.put(None)
            self.qmc.stop()
            self.started = False

    def start(self) -> None:
        if not self.started:
            self.started = True
            self.qmc.start()
            self.df_to_mqtt_manager_status_flow.start()
            self.transformer_process.start()
            self.qmc.map_topic_to_queue(
                topic=self.topic, queue=self.sensor_messages_queue
            )

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> AbstractComposedFlow:
        """
        dictionary example:

        {
            'topic': 'sensor1',
            'mapping': {'captured_at': 'Time', 'Beschleunigung 1 X': 'xAchse', 'Beschleunigung 1 Y': 'yAchse', 'Beschleunigung 1 Z': 'zAchse'},
            'sensor_config_id': <str>,
            'time_column': "Time"
        }

        """
        return cls(
            topic=config_dict["topic"],
            caas_id=config_dict["caas_id"],
            time_column=config_dict["time_column"],
        )

    def __init__(
        self,
        topic: str,
        caas_id=None,
        time_column="Time",
    ):
        """
        Constructor
        """
        self.started = False
        self.topic = topic

        self.sensor_messages_queue = multiprocessing.Queue()
        self.sensor_data_frames_queue = multiprocessing.Queue()

        self.qmc = QueueableMqttClient.from_config_service(
            client_id_prefix=self.__class__.__name__
        )

        # process transforms sensor data
        self.transformer_process = multiprocessing.Process(
            target=to_df_msg_flow,
            args=(  # input queue
                self.sensor_messages_queue,
                # output queue
                self.sensor_data_frames_queue,
            ),
        )

        self.transformer_process.daemon = True

        self.df_to_mqtt_manager_status_flow = multiprocessing.Process(
            target=df_to_mqtt_manager_status_flow,
            args=(  # input queue
                self.sensor_data_frames_queue,
                caas_id,
                time_column,
            ),
        )

        self.df_to_mqtt_manager_status_flow.daemon = True
