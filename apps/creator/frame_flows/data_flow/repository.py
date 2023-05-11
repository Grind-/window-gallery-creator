"""
Created on 22.03.2023

@author: jhirte
"""
import datetime

from op.basyx.basyx_generic_sensor.time_series_utils.data_access.repository import (
    AbstractMqttManagerStatusRepository,
)

from op.basyx.caas_kaugummiautomaten.mqtt_data_acquisition import MqttManagerStatusType


class MqttManagerStatusRepository(AbstractMqttManagerStatusRepository):
    def __init__(self, sensor_config_id: str):
        self._sensor_config_id = sensor_config_id

    def update_1hour(self, message_count: int) -> None:
        """
        update 1 hour
        """
        print(f"*** update_1hour message count  {message_count}")
        MqttManagerStatusType().update_1hour(self._sensor_config_id, message_count)

    def update_15min(self, message_count: int) -> None:
        """
        update 15 min
        """
        print(f"*** update_15min message count  {message_count}")
        MqttManagerStatusType().update_15min(self._sensor_config_id, message_count)

    def set_last_updated(self, timestamp: datetime) -> None:
        """
        set last updated
        """
        print(f"*** set_last_updated timestamp  {timestamp}")
        MqttManagerStatusType().set_last_updated(self._sensor_config_id, timestamp)
