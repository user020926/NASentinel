import logging
from datetime import datetime
from typing import Union
from PyQt5.QtWidgets import QApplication, QWidget
import pandas as pd


def format_date(time_str: str) -> Union[datetime.date, None]:
    """
    Format a date string into a datetime.date object.

    Parameters:
        time_str (str): The date string to format.

    Returns:
        Union[datetime.date, None]: The formatted date object, or None if parsing fails.
    """
    if not time_str:
        return None
    try:
        return pd.to_datetime(time_str).date()
    except (ValueError, TypeError) as e:
        logging.error(f"Time parsing error '{time_str}': {str(e)}")
        return None


def center_window(window: QWidget):
    """
    Center a window on the screen.

    Parameters:
        window (QWidget): The window object to center.
    """
    rect = window.frameGeometry()
    center_point = QApplication.desktop().availableGeometry().center()
    rect.moveCenter(center_point)
    window.move(rect.topLeft())