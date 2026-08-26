from typing import Dict, Any, Callable
import requests
from requests import Session
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import json

class NASClient:
    """
    NAS Client class used to interact with the NAS system's API, handling login, logout, log querying, and other functionalities.
    
    Attributes:
        BASE_URL (str): Base URL template used to build API endpoints.
        ERROR_MESSAGES (dict): Mapping table of error codes to their corresponding error messages.
        nas_ip (str): IP address of the NAS.
        nas_port (str): Port number of the NAS.
        sid (str | None): Session ID, retrieved after logging in.
        session (Session): HTTP session object used to send requests.
    """
    BASE_URL = "http://{ip}:{port}/webapi/"
    ERROR_MESSAGES = {
        400: "No such account or incorrect password",
        401: "Account disabled",
        402: "Permission denied",
        403: "Two-factor authentication code required",
        404: "Two-factor authentication failed",
        406: "Two-factor authentication must be enabled",
        407: "IP address blocked",
        408: "Password expired and cannot be changed",
        409: "Password expired",
        410: "Password change required",
    }

    def __init__(self, nas_ip: str, nas_port: str):
        """
        Initialize NASClient instance.

        Parameters:
            nas_ip (str): IP address of the NAS.
            nas_port (str): Port number of the NAS.
        """
        self.nas_ip = nas_ip
        self.nas_port = nas_port
        self.sid: str | None = None
        self.session = Session()

    def build_url(self, endpoint: str) -> str:
        """
        Build full API endpoint URL.

        Parameters:
            endpoint (str): Specific endpoint path of the API.

        Returns:
            str: Full API URL.
        """
        return self.BASE_URL.format(ip=self.nas_ip, port=self.nas_port) + endpoint

    def get_error_message(self, error_code: int) -> str:
        """
        Get corresponding error message based on error code.

        Parameters:
            error_code (int): Error code returned by API.

        Returns:
            str: Corresponding error message, or unknown error description if not found.
        """
        return self.ERROR_MESSAGES.get(error_code, f"Unknown error (code: {error_code})")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def login(self, account: str, password: str, otp_code: str | None = None, clear_password_callback: Callable[[], None] | None = None, clear_otp_callback: Callable[[], None] | None = None) -> str:
        """
        Execute NAS administrator login operation with retry mechanism.

        Parameters:
            account (str): Administrator account username.
            password (str): Administrator password.
            otp_code (str | None): Two-factor authentication code, or None if not applicable.
            clear_password_callback (Callable | None): Callback function to clear password field.
            clear_otp_callback (Callable | None): Callback function to clear 2FA code field.

        Returns:
            str: Session ID.

        Raises:
            Exception: If login fails, raises exception containing error message.
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
        elif error_code in (403, 404, 406) and clear_otp_callback:
            clear_otp_callback()
        raise Exception(error_msg)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_user_info(self, username: str | None = None, additional: list[str] = ["description", "email"]) -> Dict[str, Any]:
        """
        Fetch user information for a specific user or all users.

        Parameters:
            username (str | None): Target username to query; queries all users if None.
            additional (list[str]): Additional user information fields.

        Returns:
            Dict[str, Any]: Dictionary containing user information.

        Raises:
            Exception: If not logged in or API request fails.
        """
        if not self.sid:
            raise Exception("Not logged in. Please run the login method first.")
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
            raise Exception(f"API returned failure: {data.get('error', 'Unknown error')}") 
        return data
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_logs_page(self, logtype: str, limit: int, offset: int) -> Dict[str, Any]:
        """
        Fetch log data for a specific page.

        Parameters:
            logtype (str): Log type (e.g., "system" or "filestation").
            limit (int): Number of log entries returned per page.
            offset (int): Data offset used for pagination.

        Returns:
            Dict[str, Any]: Dictionary containing log data.

        Raises:
            Exception: If API request fails.
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
            raise Exception(f"API returned failure: {data.get('error', 'Unknown error')}")
        return data
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_all_logs(self, logtype: str, page_size: int) -> Dict[str, Any]:
        """
        Fetch all log data with pagination support.

        Parameters:
            logtype (str): Log type (e.g., "system" or "filestation").
            page_size (int): Number of logs per page.

        Returns:
            Dict[str, Any]: Dictionary containing all log data.

        Raises:
            Exception: If not logged in or fetching logs fails.
        """
        if not self.sid:
            raise Exception("Not logged in")
        all_items = []
        offset = 0
        limit = page_size

        while True:
            try:
                data = self.fetch_logs_page(logtype=logtype, limit=limit, offset=offset)
                
                if not data.get("success"):
                    raise Exception(f"API returned failure: {data.get('error', 'Unknown error')}")
                    
                if "data" not in data or "items" not in data["data"]:
                    raise Exception("Invalid log data structure, missing 'data' or 'items'")
                
                items = data["data"]["items"]
                all_items.extend(items)

                if len(items) < limit:
                    break

                offset += limit
                
            except Exception as e:
                raise Exception(f"Failed to fetch logs: {str(e)}")

        return {
            "success": True,
            "data": {
                "items": all_items
            }
        }

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_system_logs(self, logtype: str = "system", page_size: int = 1000) -> Dict[str, Any]:
        """
        Fetch system logs.

        Parameters:
            logtype (str): Log type, defaults to "system".
            page_size (int): Number of logs per page, defaults to 1000.

        Returns:
            Dict[str, Any]: Dictionary containing system log data.
        """
        return self.fetch_all_logs(logtype, page_size)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.RequestException))
    def fetch_filestation_logs(self, logtype: str = "filestation", page_size: int = 1000) -> Dict[str, Any]:
        """
        Fetch File Station logs.

        Parameters:
            logtype (str): Log type, defaults to "filestation".
            page_size (int): Number of logs per page, defaults to 1000.

        Returns:
            Dict[str, Any]: Dictionary containing File Station log data.
        """
        return self.fetch_all_logs(logtype, page_size)
    
    def logout(self) -> bool:
        """
        Execute logout operation and clear session ID.

        Returns:
            bool: True if logout is successful; False otherwise.

        Raises:
            Exception: If logout request fails.
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
            raise Exception(f"Logout failed: {str(e)}")