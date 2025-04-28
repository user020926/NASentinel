from typing import Dict, Any, Callable
import requests
from requests import Session
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log
import json

class NASClient:
    """
    NAS 客戶端類，用於與 NAS 系統的 API 進行交互，處理登入、登出、日誌查詢等功能。
    
    屬性:
        BASE_URL (str): 基礎 URL 模板，用於構建 API 端點。
        ERROR_MESSAGES (dict): 錯誤代碼與對應錯誤訊息的映射表。
        nas_ip (str): NAS 的 IP 地址。
        nas_port (str): NAS 的埠口。
        sid (str | None): 會話 ID，登入後獲取。
        session (Session): HTTP 會話物件，用於發送請求。
    """
    BASE_URL = "http://{ip}:{port}/webapi/"
    ERROR_MESSAGES = {
        400: "沒有該帳號或密碼錯誤",
        401: "帳戶已禁用",
        402: "權限不足",
        403: "需要雙重驗證碼",
        404: "雙重驗證失敗",
        406: "必須啟用雙重驗證",
        407: "IP被封鎖",
        408: "密碼過期且無法更改",
        409: "密碼已過期",
        410: "必須更改密碼",
    }

    def __init__(self, nas_ip: str, nas_port: str):
        """
        初始化 NASClient 實例。

        參數:
            nas_ip (str): NAS 的 IP 地址。
            nas_port (str): NAS 的埠口。
        """
        self.nas_ip = nas_ip
        self.nas_port = nas_port
        self.sid: str | None = None
        self.session = Session()

    def build_url(self, endpoint: str) -> str:
        """
        構建完整的 API 端點 URL。

        參數:
            endpoint (str): API 的具體端點路徑。

        返回:
            str: 完整的 API URL。
        """
        return self.BASE_URL.format(ip=self.nas_ip, port=self.nas_port) + endpoint

    def get_error_message(self, error_code: int) -> str:
        """
        根據錯誤代碼獲取對應的錯誤訊息。

        參數:
            error_code (int): API 返回的錯誤代碼。

        返回:
            str: 對應的錯誤訊息，若無則返回未知錯誤描述。
        """
        return self.ERROR_MESSAGES.get(error_code, f"未知錯誤 (代碼: {error_code})")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def login(self, account: str, password: str, otp_code: str | None = None, clear_password_callback: Callable[[], None] | None = None, clear_otp_callback: Callable[[], None] | None = None) -> str:
        """
        執行 NAS 管理員登入操作，支援重試機制。

        參數:
            account (str): 管理員帳號。
            password (str): 管理員密碼。
            otp_code (str | None): 雙重驗證碼，若無則為 None。
            clear_password_callback (Callable | None): 清空密碼欄位的回呼函數。
            clear_otp_callback (Callable | None): 清空雙重驗證碼欄位的回呼函數。

        返回:
            str: 會話 ID。

        異常:
            Exception: 若登入失敗，拋出包含錯誤訊息的異常。
        """
        url = self.build_url("auth.cgi")
        params = {
            "api": "SYNO.API.Auth",
            "method": "login",
            "version": "7",
            "account": account,
            "passwd": password,
            "format": "sid"
        }
        if otp_code:
            params["otp_code"] = otp_code

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "sid" in data["data"]:
            self.sid = data["data"]["sid"]
            return self.sid

        error_code = data.get("error", {}).get("code")
        error_msg = self.get_error_message(error_code)
        
        if error_code in (400, 408, 409, 410) and clear_password_callback:
            clear_password_callback()
        elif error_code in (404, 406) and clear_otp_callback:
            clear_otp_callback()
        raise Exception(error_msg)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_user_info(self, username: str | None = None, additional: list[str] = ["description", "email"]) -> Dict[str, Any]:
        """
        獲取用戶資訊，支援指定用戶或所有用戶。

        參數:
            username (str | None): 要查詢的用戶名稱，若為 None 則查詢所有用戶。
            additional (list[str]): 額外的用戶資訊欄位。

        返回:
            Dict[str, Any]: 包含用戶資訊的字典。

        異常:
            Exception: 若未登入或 API 請求失敗，拋出異常。
        """
        if not self.sid:
            raise Exception("未登入，請先執行 login 方法")
        url = self.build_url("entry.cgi")
        params = {
            "api": "SYNO.Core.User",
            "version": "1",
            "method": "list" if not username else "get",
            "_sid": self.sid
        }
        if username:
            params["name"] = username
        if additional:
            params["additional"] = json.dumps(additional)

        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise Exception(f"API 返回失敗: {data.get('error', '未知錯誤')}") 
        return data
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_logs_page(self, logtype: str, limit: int, offset: int) -> Dict[str, Any]:
        """
        獲取指定頁面的日誌數據。

        參數:
            logtype (str): 日誌類型（例如 "system" 或 "filestation"）。
            limit (int): 每頁返回的日誌數量。
            offset (int): 數據偏移量，用於分頁。

        返回:
            Dict[str, Any]: 包含日誌數據的字典。

        異常:
            Exception: 若 API 請求失敗，拋出異常。
        """
        url = self.build_url("entry.cgi")
        params = {
            "api": "SYNO.Core.SyslogClient.Log",
            "version": "1",
            "method": "list",
            "limit": limit,
            "offset": offset,
            "logtype": logtype,
            "_sid": self.sid
        }
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise Exception(f"API 返回失敗: {data.get('error', '未知錯誤')}")
        return data
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_all_logs(self, logtype: str, page_size: int) -> Dict[str, Any]:
        """
        獲取所有日誌數據，支援分頁處理。

        參數:
            logtype (str): 日誌類型（例如 "system" 或 "filestation"）。
            page_size (int): 每頁的日誌數量。

        返回:
            Dict[str, Any]: 包含所有日誌數據的字典。

        異常:
            Exception: 若未登入或獲取日誌失敗，拋出異常。
        """
        if not self.sid:
            raise Exception("未登入")
        all_items = []
        offset = 0
        limit = page_size

        while True:
            try:
                data = self.fetch_logs_page(logtype=logtype, limit=limit, offset=offset)
                
                if not data.get("success"):
                    raise Exception(f"API 返回失敗: {data.get('error', '未知錯誤')}")
                    
                if "data" not in data or "items" not in data["data"]:
                    raise Exception("日誌資料結構無效，缺少 'data' 或 'items'")
                
                items = data["data"]["items"]
                all_items.extend(items)

                if len(items) < limit:
                    break

                offset += limit
                
            except Exception as e:
                raise Exception(f"獲取日誌失敗: {str(e)}")

        return {
            "success": True,
            "data": {
                "items": all_items
            }
        }

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_system_logs(self, logtype: str = "system", page_size: int = 1000) -> Dict[str, Any]:
        """
        獲取系統日誌。

        參數:
            logtype (str): 日誌類型，預設為 "system"。
            page_size (int): 每頁的日誌數量，預設為 1000。

        返回:
            Dict[str, Any]: 包含系統日誌數據的字典。
        """
        return self.fetch_all_logs(logtype, page_size)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_filestation_logs(self, logtype: str = "filestation", page_size: int = 1000) -> Dict[str, Any]:
        """
        獲取檔案管理日誌。

        參數:
            logtype (str): 日誌類型，預設為 "filestation"。
            page_size (int): 每頁的日誌數量，預設為 1000。

        返回:
            Dict[str, Any]: 包含檔案管理日誌數據的字典。
        """
        return self.fetch_all_logs(logtype, page_size)
    
    def logout(self) -> bool:
        """
        執行登出操作，清除會話 ID。

        返回:
            bool: 若登出成功，返回 True；否則返回 False。

        異常:
            Exception: 若登出請求失敗，拋出異常。
        """
        if not self.sid:
            return True
        url = self.build_url("auth.cgi")
        params = {
            "api": "SYNO.API.Auth",
            "method": "logout",
            "version": "7", 
            "_sid": self.sid
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("success", False):
                self.sid = None
                return True
            return False
        except requests.RequestException as e:
            raise Exception(f"登出失敗: {str(e)}")