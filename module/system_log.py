import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path

class System_Log:    
    """
    System log class for recording and saving system-related log data.

    Attributes:
        PRIORITY_MAPPING (dict): Mapping table between priority levels and Chinese descriptions.
        SYSTEM_COLUMNS (list): Column names for the log table.
        logs (List[Dict[str, str]]): List storing log records.
        log_file (str): File path for saving the log.
    """
    PRIORITY_MAPPING = {
        "info": "資訊",
        "warn": "警告",
        "error": "錯誤"
    }

    SYSTEM_COLUMNS = ["優先層級", "日誌", "時間", "使用者", "事件"]

    def __init__(self):
        """
        Initialize the System_Log instance.
        """
        self.logs: List[Dict[str, str]] = []
        self.log_file = self.get_log_path()

    def get_log_path(self) -> str:
        """
        Generate the save path for the log file.

        Returns:
            str: Full path of the log file (located on the Desktop).
        """
        date_str = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        desktop_path = Path.home() / "Desktop"
        return str(desktop_path / f"NAS_System_Log_{date_str}.xlsx")

    def map_priority(self, level: str) -> str:
        """
        Map priority level to its corresponding Chinese description.

        Parameters:
            level (str): Raw priority level.

        Returns:
            str: Corresponding Chinese priority name, or "未知事件" if not found.
        """
        return self.PRIORITY_MAPPING.get(level.lower(), "未知事件")

    def add_log(self, log: Dict[str, str]):
        """
        Add a system log record.

        Parameters:
            log (Dict[str, str]): Dictionary containing log information.

        Exceptions:
            Exception: Raised if adding the record fails.
        """
        try:
            required_keys = ["level", "time", "who", "descr"]
            for key in required_keys:
                if key not in log:
                    raise KeyError(f"Missing required key: {key}")
            
            entry = {
                "優先層級": self.map_priority(log["level"]),
                "日誌": "System",
                "時間": log["time"],
                "使用者": log["who"],
                "事件": log["descr"],
            }
            self.logs.append(entry)
        except Exception as e:
            raise Exception(f"Failed to add log entry: {str(e)}")

    def save_to_file(self) -> bool:
        """
        Save system logs to an Excel file.

        Returns:
            bool: Returns True if saving is successful; otherwise False.

        Exceptions:
            Exception: Raised if saving fails.
        """
        if not self.logs:
            return False
        try:
            df = pd.DataFrame(self.logs, columns=self.SYSTEM_COLUMNS)
            df.to_excel(self.log_file, index=False, engine="openpyxl")
            self.logs.clear()
            return True
        except Exception as e:
            raise Exception(f"Failed to save log file: {str(e)}")