import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path

class System_Log:    
    """
    系統日誌類，用於記錄和保存系統相關的日誌數據。

    屬性:
        PRIORITY_MAPPING (dict): 優先層級與中文描述的映射表。
        SYSTEM_COLUMNS (list): 日誌表格的欄位名稱。
        logs (List[Dict[str, str]]): 儲存日誌記錄的列表。
        log_file (str): 日誌檔案的保存路徑。
    """
    PRIORITY_MAPPING = {
        "info": "資訊",
        "warn": "警告",
        "error": "錯誤"
    }

    SYSTEM_COLUMNS = ["優先層級", "日誌", "時間", "使用者", "事件"]

    def __init__(self):
        """
        初始化 System_Log 實例。
        """
        self.logs: List[Dict[str, str]] = []
        self.log_file = self.get_log_path()

    def get_log_path(self) -> str:
        """
        生成日誌檔案的保存路徑。

        返回:
            str: 日誌檔案的完整路徑（位於桌面）。
        """
        date_str = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        desktop_path = Path.home() / "Desktop"
        return str(desktop_path / f"NAS_System_Log_{date_str}.xlsx")

    def map_priority(self, level: str) -> str:
        """
        將優先層級映射為中文描述。

        參數:
            level (str): 原始優先層級。

        返回:
            str: 對應的中文優先層級名稱，若無則返回 "未知事件"。
        """
        return self.PRIORITY_MAPPING.get(level.lower(), "未知事件")

    def add_log(self, log: Dict[str, str]):
        """
        添加系統日誌記錄。

        參數:
            log (Dict[str, str]): 包含日誌資訊的字典。

        異常:
            Exception: 若添加記錄失敗，拋出異常。
        """
        try:
            required_keys = ["level", "time", "who", "descr"]
            for key in required_keys:
                if key not in log:
                    raise KeyError(f"項目遺失: {key}")
            
            entry = {
                "優先層級": self.map_priority(log["level"]),
                "日誌": "System",
                "時間": log["time"],
                "使用者": log["who"],
                "事件": log["descr"],
            }
            self.logs.append(entry)
        except Exception as e:
            raise Exception(f"添加日誌失敗: {str(e)}")

    def save_to_file(self) -> bool:
        """
        將系統日誌保存為 Excel 檔案。

        返回:
            bool: 若保存成功，返回 True；否則返回 False。

        異常:
            Exception: 若保存失敗，拋出異常。
        """
        if not self.logs:
            return False
        try:
            df = pd.DataFrame(self.logs, columns=self.SYSTEM_COLUMNS)
            df.to_excel(self.log_file, index=False, engine="openpyxl")
            self.logs.clear()
            return True
        except Exception as e:
            raise Exception(f"保存日誌失敗: {str(e)}")