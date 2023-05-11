"""
Created on 22.03.2023

@author: jhirte
"""
from multiprocessing import Queue
import os
from apps.creator.frame_flows.mqtt import (
    MqttFrame2StatusFlowManager
)


class MqttProviderManager:
    instance = None
    _incoming_caas_queue: Queue = None

    @classmethod
    def get_instance(cls) -> "MqttProviderManager":
        if not cls.instance:
            cls.instance = MqttProviderManager()
        return cls.instance

    def __init__(self):
        self.mqtt_set_flows_manager = None
        self.mqtt_rotations_flows_manager = None
        print(
            f"{os.getpid()} / MqttProviderManager.__init__:  Created MqttProviderManager",
            flush=True,
        )

    def consume_new_caas(self, config_service: ConfigService, queue: Queue) -> None:
        global ConfigService
        ConfigService._INSTANCE = config_service
        self._incoming_caas_queue = queue

        print(
            f"{os.getpid()} / MqttProviderManager.consume_new_caas_sm / Using queue: {queue}",
            flush=True,
        )

        self._create_mqtt_manager_status()
            
        if not self.mqtt_rotations_flows_manager:
            self.mqtt_rotations_flows_manager = MqttFrame2StatusFlowManager()

        while True:
            ser_caas_sm = self._incoming_caas_queue.get()
            if ser_caas_sm:
                print(
                    f"{os.getpid()} / MqttProviderManager.consume_new_caas_sm / Processing incoming CaaS Submodel"
                )
                caas_sm_dict = self.config_dict_from_caas(ser_caas_sm)
                self.mqtt_rotations_flows_manager.start_flow(caas_sm_dict)

    def accept_new_caas(self):
        print(
            f"{os.getpid()} / MqttProviderManager.accept_new_caas_sm / Using queue: {self._incoming_caas_queue}",
            flush=True,
        )
        if self._incoming_caas_queue:
            self._incoming_caas_queue.put(caas_sm)
        else:
            raise IllegalStateException(
                "MqttProviderManager not yet initialized, booting..."
            )

    def config_dict_from_caas(self, caas: CaaS) -> dict:
        """
        dictionary example:

        {
            'topic': 'sensor1',
            'timeseries_ref': <Reference>,
            'time_column': 'Time',
            'caas_id': 'op.basyx.generic_sensor.sensor-config_123'
        }

        """
        topic = caas.get_property_by_short_id(
            SensorConfigurationConstants.PROPERTY_INCOMING_MQTT_TOPIC
        ).value
        internal_cache_duration = caas.get_property_by_short_id(
            SensorConfigurationConstants.PROPERTY_INTERNAL_CACHE_DURATION
        ).value
        timeseries_ref = caas.get_referenceelement_by_short_id(
            CaaSConstants.REFERENCE_TIMESERIES
        ).value

        time_column = "Time"

        time_series_manager_cfg_dict = {}
        time_series_manager_cfg_dict["topic"] = topic
        time_series_manager_cfg_dict["timeseries_ref"] = timeseries_ref
        time_series_manager_cfg_dict[
            "internal_cache_duration"
        ] = internal_cache_duration
        time_series_manager_cfg_dict["time_column"] = time_column
        time_series_manager_cfg_dict["caas_id"] = caas.identification.id
        return time_series_manager_cfg_dict

    def _create_mqtt_manager_status(self):
        manager_aas_descr = RemoteObjectRegistryClient.fetch_aas_descriptor(
            MqttDataAcquisitionConstants.IDENTIFIER
        )
        if not manager_aas_descr.get_submodel_descriptor_by_idshort(
            MqttManagerStatusTypeConstants.ID_SHORT
        ):
            deploy_status_submodel()
