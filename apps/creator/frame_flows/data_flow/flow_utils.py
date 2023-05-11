"""
Created on 22.03.2023

@author: jhirte
"""
from typing import Dict, Any

import ciso8601
import pandas as pd


def dict_2_data_frame(data_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Converts list of simple dictionaries like [{"col1":"abc", "col2":25},{"col1":"def", "col2":50}]
    in pandas data frame.
    """
    df = pd.DataFrame()

    try:
        result_dict: Dict[str, Any] = {}

        for col_name in data_dict:
            if result_dict.get(col_name, None) is None:
                result_dict[col_name] = []

        for col_name in result_dict.keys():
            if col_name == "Time":
                dt = ciso8601.parse_datetime(data_dict.get(col_name, None))
                result_dict[col_name].append(dt)
            else:
                result_dict[col_name].append(data_dict.get(col_name, None))

        df = pd.DataFrame(result_dict)
    except:
        print(f"Malformed message: {data_dict}")

    return df
