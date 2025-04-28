import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path

class FilesStation_Log:    
    """
    檔案管理日誌類，用於記錄和保存檔案管理相關的日誌數據。

    屬性:
        EVENT_MAPPING (dict): 事件名稱與中文描述的映射表。
        FILESTATION_COLUMNS (list): 日誌表格的欄位名稱。
        logs (List[Dict[str, str]]): 儲存日誌記錄的列表。
        log_file (str): 日誌檔案的保存路徑。
    """
    EVENT_MAPPING = {
        "upload": "上傳", 
        "download": "下載", 
        "delete": "刪除",
        "rename": "重新命名", 
        "move": "移動", 
        "copy": "複製",
        "create folder": "建立資料夾", 
        "extract": "解壓縮",
        "compress": "壓縮", 
        "property set": "設定屬性"
    }

    FILESTATION_COLUMNS = ["日誌", "時間", "IP位址", "使用者", "事件", "檔案/資料夾", "檔案大小", "檔案名稱"]

    def __init__(self):
        """
        初始化 FilesStation_Log 實例。
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
        return str(desktop_path / f"NAS_Filestation_Log_{date_str}.xlsx")

    def map_event(self, cmd: str) -> str:
        """
        將事件名稱映射為中文描述。

        參數:
            cmd (str): 原始事件名稱。

        返回:
            str: 對應的中文事件名稱，若無則返回 "未知事件"。
        """
        return self.EVENT_MAPPING.get(cmd.lower(), "未知事件")

    def add_log(self, log: Dict[str, str]):
        """
        添加檔案管理日誌記錄。

        參數:
            log (Dict[str, str]): 包含日誌資訊的字典。

        異常:
            Exception: 若添加記錄失敗，拋出異常。
        """
        try:
            isdir = str(log.get("isdir", "False")).lower() == "true"
            entry = {
                "日誌": "FileStation",
                "時間": log.get("time", "N/A"),
                "IP位址": log.get("ip", "N/A"),
                "使用者": log.get("username", "N/A"),
                "事件": self.map_event(log.get("cmd", "N/A")),
                "檔案/資料夾": "資料夾" if isdir else "檔案",
                "檔案大小": log.get("filesize", "N/A"),
                "檔案名稱": log.get("descr", "N/A")
            }
            self.logs.append(entry)
        except Exception as e:
            raise Exception(f"添加日誌失敗: {str(e)}")
        
    def save_to_file(self) -> bool:
        """
        將檔案管理日誌保存為 Excel 檔案。

        返回:
            bool: 若保存成功，返回 True；否則返回 False。

        異常:
            Exception: 若保存失敗，拋出異常。
        """
        if not self.logs:
            return False
        try:
            df = pd.DataFrame(self.logs, columns=self.FILESTATION_COLUMNS)
            df.to_excel(self.log_file, index=False, engine="openpyxl")
            self.logs.clear()
            return True
        except Exception as e:
            raise Exception(f"保存日誌失敗: {str(e)}")