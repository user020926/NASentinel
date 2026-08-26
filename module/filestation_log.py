import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path

class FilesStation_Log:    
    """
    File Station log class used to record and save File Station-related log data.

    Attributes:
        EVENT_MAPPING (dict): Mapping table of event names to their English descriptions.
        FILESTATION_COLUMNS (list): Column names for the log table.
        logs (List[Dict[str, str]]): List storing the log records.
        log_file (str): Save path for the log file.
    """
    EVENT_MAPPING = {
        "upload": "Upload", 
        "download": "Download", 
        "delete": "Delete",
        "rename": "Rename", 
        "move": "Move", 
        "copy": "Copy",
        "create folder": "Create Folder", 
        "extract": "Extract",
        "compress": "Compress", 
        "property set": "Set Properties"
    }

    FILESTATION_COLUMNS = ["Log Type", "Time", "IP Address", "User", "Event", "File/Folder", "File Size", "File Name"]

    def __init__(self):
        """
        Initialize FilesStation_Log instance.
        """
        self.logs: List[Dict[str, str]] = []
        self.log_file = self.get_log_path()

    def get_log_path(self) -> str:
        """
        Generate save path for the log file.

        Returns:
            str: Full path to the log file (located on the Desktop).
        """
        date_str = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        desktop_path = Path.home() / "Desktop"
        return str(desktop_path / f"NAS_Filestation_Log_{date_str}.xlsx")

    def map_event(self, cmd: str) -> str:
        """
        Map event names to English descriptions.

        Parameters:
            cmd (str): Original event command name.

        Returns:
            str: Corresponding English event name, or "Unknown Event" if not mapped.
        """
        return self.EVENT_MAPPING.get(cmd.lower(), "Unknown Event")

    def add_log(self, log: Dict[str, str]):
        """
        Add a File Station log record.

        Parameters:
            log (Dict[str, str]): Dictionary containing log information.

        Raises:
            Exception: If adding record fails, raises an exception.
        """
        try:
            isdir = str(log.get("isdir", "False")).lower() == "true"
            entry = {
                "Log Type": "FileStation",
                "Time": log.get("time", "N/A"),
                "IP Address": log.get("ip", "N/A"),
                "User": log.get("username", "N/A"),
                "Event": self.map_event(log.get("cmd", "N/A")),
                "File/Folder": "Folder" if isdir else "File",
                "File Size": log.get("filesize", "N/A"),
                "File Name": log.get("descr", "N/A")
            }
            self.logs.append(entry)
        except Exception as e:
            raise Exception(f"Failed to add log record: {str(e)}")
        
    def save_to_file(self) -> bool:
        """
        Save File Station logs to an Excel file.

        Returns:
            bool: True if saving is successful; False otherwise.

        Raises:
            Exception: If saving fails, raises an exception.
        """
        if not self.logs:
            return False
        try:
            df = pd.DataFrame(self.logs, columns=self.FILESTATION_COLUMNS)
            df.to_excel(self.log_file, index=False, engine="openpyxl")
            self.logs.clear()
            return True
        except Exception as e:
            raise Exception(f"Failed to save log file: {str(e)}")