# SuperFastPython.com
# example of using the queue with processes
from datetime import datetime, timedelta
import os
from queue import Empty
from time import sleep
from typing import Any, Optional

from ciso8601 import parse_datetime
import ciso8601
from op.basyx.basyx_generic_sensor.time_series_utils.data_access.repository import (
    InternalSegmentRepository,
)
from op.basyx.basyx_generic_sensor.time_series_utils.data_flow.flow_utils import (
    to_data_frame,
)
from op.basyx.sdk.referable import Reference
from op.basyx.timeseries_model.timeseries import RecordConstants
from pandas.core.frame import DataFrame
from pandas.core.internals.construction import dict_to_mgr
import pytz

from op.basyx.caas_kaugummiautomaten.flow_provider.data_flow.flow_utils import (
    dict_2_data_frame,
)
from op.basyx.caas_kaugummiautomaten.flow_provider.data_flow.repository import (
    MqttManagerStatusRepository,
)
import pandas as pd


def dict_to_rotation_flow(
    in_queue: Any,
    duration: timedelta,
    timeseries_sm_ref: Reference,
    time_column="Time",
) -> None:
    """
    data frame to current streaming
    """
    isr = InternalSegmentRepository(timeseries_sm_ref)

    repo_df = isr.get_all()
    while True:
        try:
            message_dict = in_queue.get(timeout=1)
            if not message_dict:
                break
            repo_df = isr.get_all()
            if not repo_df.empty:
                repo_df.sort_values(by=[time_column])
            index_list = []
            for meta in isr.rec_meta.value:
                index_list.append(meta.idShort)
            new_df = {}

            new_df[time_column] = [datetime.fromtimestamp(message_dict["finished"]).astimezone(pytz.utc)]
            new_df["quality"] = [message_dict["qual"]]
            new_df["amount"] = [message_dict["amount"]]
            isr.put(pd.DataFrame.from_dict(new_df))
            sleep(1)
        except Empty:
            continue
        except Exception as e:
            print(
                f"{os.getpid()} / queueable_flow.df_to_internal_segment_flow / Malformed data dict: {message_dict} - "
                f"caused by {e.with_traceback()}",
                flush=True,
            )
            continue

    print(f"{os.getpid()} / queueable_flow.dic_to_df_msg_flow: Done", flush=True)


def to_df_msg_flow(
    in_queue: Any,
    out_queue: Any,
) -> None:
    """
    dictionary to data frame streaming
    """
    while True:
        try:
            msg = in_queue.get(timeout=1)
            if msg is None:
                break
            if len(msg) == 0:
                continue

            # msg["Time"] = parse_datetime(msg["Time"])

            df_msg = dict_2_data_frame(msg)
            out_queue.put(df_msg)

        except Empty:
            continue
        except Exception as e:
            print(
                f"{os.getpid()} / queueable_flow.to_df_msg_flow / Malformed data frame: {msg} - "
                f"caused by {e.with_traceback()}",
                flush=True,
            )
            continue


def df_to_mqtt_manager_status_flow(
    in_queue: Any,
    sensor_config_id: str,
    time_column: object = "Time",
) -> None:
    """
    data frame to snapshot streaming
    """
    mmsr = MqttManagerStatusRepository(sensor_config_id)

    df_1hour = pd.DataFrame()
    df_15min = pd.DataFrame()
    length_1hour = -1
    length_15min = -1
    last_time = None

    while True:
        try:
            message_df = in_queue.get(timeout=1)
            if message_df is None:
                break
            if len(message_df) == 0:
                continue
            last_time = message_df[time_column].max()
            mmsr.set_last_updated(last_time)
            df_1hour = pd.concat([df_1hour, message_df.copy()], ignore_index=True)

            from_time = last_time - timedelta(hours=1)
            df_1hour = df_1hour[(df_1hour[time_column] > from_time)]
            length = len(df_1hour)
            if length != length_1hour:
                mmsr.update_1hour(length)
                length_1hour = length

            df_15min = pd.concat([df_15min, message_df.copy()], ignore_index=True)
            from_time = last_time - timedelta(minutes=15)
            df_15min = df_15min[(df_15min[time_column] > from_time)]
            length = len(df_15min)
            if length != length_15min:
                mmsr.update_15min(length)
                length_15min = length
        except Empty:
            continue
        except Exception as e:
            print(
                f"{os.getpid()} / queueable_flow.df_to_mqtt_manager_status_flow / Malformed data frame: {message_df} - "
                f"caused by {e.with_traceback()}",
                flush=True,
            )
            continue

    print(f"{os.getpid()} / queueable_flow.dic_to_df_msg_flow: Done", flush=True)
