from datetime import datetime
from typing import Union
from PyQt5.QtWidgets import QApplication, QWidget
import pandas as pd
import logging

def format_date(time_str: str) -> Union[datetime.date, None]:
    """
    將日期字符串格式化為 datetime.date 物件。

    參數:
        time_str (str): 要格式化的日期字符串。

    返回:
        Union[datetime.date, None]: 格式化後的日期物件，若解析失敗則返回 None。
    """
    if not time_str:
        return None
    try:
        return pd.to_datetime(time_str).date()
    except (ValueError, TypeError) as e:
        logging.error(f"時間解析錯誤 '{time_str}': {str(e)}")
        return None

def center_window(window: QWidget):
    """
    將窗口置中於螢幕。

    參數:
        window (QWidget): 要置中的窗口物件。
    """
    rect = window.frameGeometry()
    center_point = QApplication.desktop().availableGeometry().center()
    rect.moveCenter(center_point)
    window.move(rect.topLeft())