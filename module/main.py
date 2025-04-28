import sys
import os
import re
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QTabWidget, QComboBox, QHeaderView, QProgressDialog)
from PyQt5.QtGui import QFont, QIcon, QIntValidator
from PyQt5.QtCore import Qt, QDate
from api import NASClient
from utils import center_window, format_date
from date_picker import DatePickerDialog
from system_log import System_Log
from filestation_log import FilesStation_Log
from ranking_log import Ranking_Log

"""
主程式模組，負責實現 NAS 日誌查詢應用程式的圖形化介面，包括登入窗口和日誌顯示窗口。
"""

def resource_path(relative_path):
    """
    獲取資源的絕對路徑，支援開發環境和打包後的執行環境。

    參數:
        relative_path (str): 資源的相對路徑。

    返回:
        str: 資源的絕對路徑。
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)
    return os.path.join(base_path, relative_path)

class LoginWindow(QMainWindow):
    """
    登入窗口類，提供 NAS 管理員登入的圖形化介面。

    屬性:
        nas_client (NASClient): NAS 客戶端物件，用於與 NAS API 交互。
        system_log (System_Log): 系統日誌物件，用於記錄系統日誌。
        filestation_log (FilesStation_Log): 檔案管理日誌物件，用於記錄檔案管理日誌。
        ip_entry (QLineEdit): NAS IP 輸入框。
        port_entry (QLineEdit): NAS 埠口輸入框。
        admin_entry (QLineEdit): 管理員帳號輸入框。
        pwd_entry (QLineEdit): 管理員密碼輸入框。
        otp_entry (QLineEdit): 雙重驗證碼輸入框。
    """
    def __init__(self):
        """
        初始化 LoginWindow 實例，設置窗口屬性和 UI 介面。
        """
        super().__init__()
        self.setWindowTitle("登入")
        self.setGeometry(700, 400, 480, 300)
        self.setWindowIcon(QIcon(resource_path("icons/NASentinel.ico")))
        self.nas_client = None
        self.system_log = System_Log()
        self.filestation_log = FilesStation_Log()
        self.setup_ui()

    def setup_ui(self):
        """
        設置登入窗口的 UI 介面，包括輸入欄位、按鈕和樣式。
        """
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        self.ip_entry = self.add_field(input_layout, "NAS IP:", "例如: 10.57.78.62")
        self.port_entry = self.add_field(input_layout, "NAS 埠口:", "例如: 5000")
        self.admin_entry = self.add_field(input_layout, "管理員帳號:")
        self.pwd_entry = self.add_field(input_layout, "管理員密碼:", is_password=True)
        self.otp_entry = self.add_field(input_layout, "雙重驗證碼:", "請輸入 6 位驗證碼，若無則留空")
        
        self.ip_entry.returnPressed.connect(lambda: self.port_entry.setFocus())
        self.port_entry.returnPressed.connect(lambda: self.admin_entry.setFocus())
        self.admin_entry.returnPressed.connect(lambda: self.pwd_entry.setFocus())
        self.pwd_entry.returnPressed.connect(lambda: self.otp_entry.setFocus())
        self.otp_entry.returnPressed.connect(self.attempt_login)
        layout.addWidget(input_widget)

        login_btn = QPushButton("登入")
        login_btn.clicked.connect(self.attempt_login)
        login_btn.setFixedSize(80, 40)
        layout.addWidget(login_btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        center_window(self)
        self.set_stylesheet()

    def add_field(self, layout: QVBoxLayout, label: str, placeholder: str = "", is_password: bool = False) -> QLineEdit:
        """
        添加輸入欄位到佈局中，包括標籤和輸入框。

        參數:
            layout (QVBoxLayout): 目標佈局。
            label (str): 欄位標籤。
            placeholder (str): 輸入框的提示文字。
            is_password (bool): 是否為密碼欄位。

        返回:
            QLineEdit: 創建的輸入框物件。
        """
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        entry = QLineEdit()
        entry.setPlaceholderText(placeholder)
        if is_password:
            entry.setEchoMode(QLineEdit.Password)
        hbox.addWidget(entry)
        layout.addLayout(hbox)
        return entry

    def attempt_login(self):
        """
        執行 NAS 管理員登入操作，驗證輸入並調用 NASClient 的登入方法。

        異常:
            Exception: 若登入失敗，顯示錯誤訊息並清空相關欄位。
        """
        if not self.validate_inputs():
            return
        nas_ip = self.ip_entry.text()
        nas_port = self.port_entry.text() or "5000"
        username = self.admin_entry.text()
        password = self.pwd_entry.text()
        otp_code = self.otp_entry.text() or None
        self.nas_client = NASClient(nas_ip, nas_port)

        try:
            self.nas_client.login(username, password, otp_code=otp_code, clear_password_callback=self.clear_pwd, clear_otp_callback=self.clear_otp)
            QMessageBox.information(self, "成功", "管理員登入成功!")
            self.open_log_window()
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"登入失敗: {str(e)}")
            self.clear_pwd()
            self.clear_otp()

    def validate_inputs(self) -> bool:
        """
        驗證輸入欄位的有效性，包括 IP、埠口和帳號密碼。

        返回:
            bool: 若所有輸入有效，返回 True；否則顯示錯誤訊息並返回 False。
        """
        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", self.ip_entry.text()):
            QMessageBox.critical(self, "錯誤", "請輸入有效IP")
            return False
        port_text = self.port_entry.text() or "5000"
        if not port_text.isdigit() or not (1 <= int(port_text) <= 65535):
            QMessageBox.critical(self, "錯誤", "請輸入有效埠口")
            return False
        if not self.admin_entry.text():
            QMessageBox.critical(self, "錯誤", "請輸入管理員帳號")
            return False
        if not self.pwd_entry.text():
            QMessageBox.critical(self, "錯誤", "請輸入管理員密碼")
            return False
        return True

    def clear_pwd(self):
        """
        清空密碼輸入欄位。
        """
        self.pwd_entry.clear()

    def clear_otp(self):
        """
        清空雙重驗證碼輸入欄位。
        """
        self.otp_entry.clear()

    def open_log_window(self):
        """
        打開日誌窗口並關閉登入窗口。
        """
        self.log_window = LogWindow(self.nas_client)
        self.log_window.show()
        self.clear_pwd()
        self.clear_otp()
        self.close()

    def set_stylesheet(self):
        """
        設置登入窗口的樣式表，定義 UI 外觀。
        """
        self.setStyleSheet("""
            QWidget { 
                background-color: #ECF0F1;
                font-family: Yu Gothic UI;
            }
            QLineEdit {
                background-color: #F9F9F9; 
                border: 1px solid #979EA9; 
                border-radius: 5px;
                padding: 5px;
                color: #333333;
            }
            QPushButton { 
                background-color: #BFD1E5;
                color: #333333;
                border: None; 
                border-radius: 5px; 
                padding: 8px; 
            }
            QPushButton:hover { 
                background-color: #C6D9F1; 
            }
            QLabel { 
                color: #333333; 
            }
        """)

class LogWindow(QMainWindow):
    """
    日誌窗口類，提供系統日誌、檔案管理日誌和排行榜的顯示與篩選功能。

    屬性:
        MAX_DISPLAY_ROWS (int): 最大顯示的日誌行數。
        ROWS_PER_PAGE (int): 每頁顯示的日誌行數。
        nas_client (NASClient): NAS 客戶端物件。
        system_log (System_Log): 系統日誌物件。
        filestation_log (FilesStation_Log): 檔案管理日誌物件。
        ranking_log (Ranking_Log): 排行榜日誌物件。
        start_date (datetime.date | None): 篩選的開始日期。
        end_date (datetime.date): 篩選的結束日期。
        selected_priority (str | None): 選中的優先層級。
        selected_event (str | None): 選中的事件類型。
        system_current_page (int): 系統日誌當前頁碼。
        filestation_current_page (int): 檔案管理日誌當前頁碼。
        system_filtered_logs (list): 篩選後的系統日誌數據。
        filestation_filtered_logs (list): 篩選後的檔案管理日誌數據。
    """
    MAX_DISPLAY_ROWS = 10000
    ROWS_PER_PAGE = 100

    def __init__(self, nas_client: NASClient):
        """
        初始化 LogWindow 實例，設置窗口屬性和 UI 介面。

        參數:
            nas_client (NASClient): NAS 客戶端物件。
        """
        super().__init__()
        self.setWindowTitle("NASentinel")
        self.setGeometry(100, 100, 1800, 800)
        self.setWindowIcon(QIcon(resource_path("icons/NASentinel.ico")))
        self.nas_client = nas_client
        self.system_log = System_Log()
        self.filestation_log = FilesStation_Log()
        self.ranking_log = Ranking_Log()
        self.start_date = None
        self.end_date = datetime.now().date()
        self.selected_priority = None
        self.selected_event = None
        self.system_current_page = 1
        self.filestation_current_page = 1
        self.system_filtered_logs = []
        self.filestation_filtered_logs = []
        self.setup_ui()
        self.fetch_logs()

    def setup_ui(self):
        """
        設置日誌窗口的 UI 介面，包括標籤頁、表格、篩選控件和分頁按鈕。
        """
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tabs)
        self.system_tab = QWidget()
        self.tabs.addTab(self.system_tab, "系統日誌")
        system_layout = QVBoxLayout(self.system_tab)
        system_controls_layout = QHBoxLayout()
        self.system_start_date_edit, self.system_end_date_edit = self.date_controls(system_controls_layout, "system")
        self.priority_controls(system_controls_layout, include_priority_combo=True)
        system_controls_layout.addSpacing(10)
        self.search_export_buttons(system_controls_layout)
        system_layout.addLayout(system_controls_layout)

        self.system_table = QTableWidget()
        self.system_table.setColumnCount(5)
        self.system_table.setHorizontalHeaderLabels(["優先層級", "日誌", "時間", "使用者", "事件"])
        self.system_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.system_table.horizontalHeader().setStretchLastSection(True)
        self.system_table.verticalHeader().setFixedWidth(50)
        system_layout.addWidget(self.system_table)

        system_pagination_layout = QHBoxLayout()
        self.system_prev_btn = QPushButton()
        self.system_prev_btn.setIcon(QIcon(resource_path("icons/left-arrow.png")))
        self.system_prev_btn.clicked.connect(self.system_prev_page)
        self.system_prev_btn.setFixedSize(40, 40)
        system_pagination_layout.addWidget(self.system_prev_btn)

        self.system_page_edit = QLineEdit("1")
        self.system_page_edit.setAlignment(Qt.AlignCenter)
        self.system_page_edit.setFixedWidth(50)
        self.system_page_edit.setValidator(QIntValidator(1, 9999))
        self.system_page_edit.returnPressed.connect(self.system_jump_to_page)
        system_pagination_layout.addWidget(QLabel("第"))
        system_pagination_layout.addWidget(self.system_page_edit)
        system_pagination_layout.addWidget(QLabel("頁"))

        total_pages_label = QLabel("/ 共 1 頁")
        total_pages_label.setObjectName("systemTotalPages")
        system_pagination_layout.addWidget(total_pages_label)

        self.system_next_btn = QPushButton()
        self.system_next_btn.setIcon(QIcon(resource_path("icons/right-arrow.png")))
        self.system_next_btn.clicked.connect(self.system_next_page)
        self.system_next_btn.setFixedSize(40, 40)
        system_pagination_layout.addWidget(self.system_next_btn)

        system_pagination_layout.addStretch()
        system_layout.addLayout(system_pagination_layout)

        self.filestation_tab = QWidget()
        self.tabs.addTab(self.filestation_tab, "檔案管理日誌")
        filestation_layout = QVBoxLayout(self.filestation_tab)
        filestation_controls_layout = QHBoxLayout()
        self.filestation_start_date_edit, self.filestation_end_date_edit = self.date_controls(filestation_controls_layout, "filestation")
        self.event_controls(filestation_controls_layout, include_event_combo=True)
        filestation_controls_layout.addSpacing(10)
        self.search_export_buttons(filestation_controls_layout)
        filestation_layout.addLayout(filestation_controls_layout)

        self.filestation_table = QTableWidget()
        self.filestation_table.setColumnCount(8)
        self.filestation_table.setHorizontalHeaderLabels(["日誌", "時間", "IP 位址", "使用者", "事件", "檔案/資料夾", "檔案大小", "檔案名稱"])
        self.filestation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.filestation_table.horizontalHeader().setStretchLastSection(True)
        self.filestation_table.verticalHeader().setFixedWidth(50)
        filestation_layout.addWidget(self.filestation_table)

        filestation_pagination_layout = QHBoxLayout()
        self.filestation_prev_btn = QPushButton()
        self.filestation_prev_btn.setIcon(QIcon(resource_path("icons/left-arrow.png")))
        self.filestation_prev_btn.clicked.connect(self.filestation_prev_page)
        self.filestation_prev_btn.setFixedSize(40, 40)
        filestation_pagination_layout.addWidget(self.filestation_prev_btn)

        self.filestation_page_edit = QLineEdit("1")
        self.filestation_page_edit.setAlignment(Qt.AlignCenter)
        self.filestation_page_edit.setFixedWidth(50)
        self.filestation_page_edit.setValidator(QIntValidator(1, 9999))
        self.filestation_page_edit.returnPressed.connect(self.filestation_jump_to_page)
        filestation_pagination_layout.addWidget(QLabel("第"))
        filestation_pagination_layout.addWidget(self.filestation_page_edit)
        filestation_pagination_layout.addWidget(QLabel("頁"))

        filestation_total_pages_label = QLabel("/ 共 1 頁")
        filestation_total_pages_label.setObjectName("filestationTotalPages")
        filestation_pagination_layout.addWidget(filestation_total_pages_label)

        self.filestation_next_btn = QPushButton()
        self.filestation_next_btn.setIcon(QIcon(resource_path("icons/right-arrow.png")))
        self.filestation_next_btn.clicked.connect(self.filestation_next_page)
        self.filestation_next_btn.setFixedSize(40, 40)
        filestation_pagination_layout.addWidget(self.filestation_next_btn)

        filestation_pagination_layout.addStretch()
        filestation_layout.addLayout(filestation_pagination_layout)

        self.rankings_tab = QWidget()
        self.tabs.addTab(self.rankings_tab, "排行榜")
        rankings_layout = QVBoxLayout(self.rankings_tab)
        rankings_controls_layout = QHBoxLayout()
        self.rankings_start_date_edit, self.rankings_end_date_edit = self.date_controls(rankings_controls_layout, "rankings")
        self.search_export_buttons(rankings_controls_layout)
        rankings_controls_layout.addSpacing(20)
        rankings_layout.addLayout(rankings_controls_layout)
        
        rankings_layout.addWidget(QLabel("上傳次數排行榜"))
        self.upload_table = QTableWidget()
        self.upload_table.setColumnCount(5)
        self.upload_table.setHorizontalHeaderLabels(["排名", "使用者", "上傳次數", "姓名", "電子郵件"])
        self.upload_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.upload_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.upload_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.upload_table)

        rankings_layout.addWidget(QLabel("下載次數排行榜"))
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(5)
        self.download_table.setHorizontalHeaderLabels(["排名", "使用者", "下載次數", "姓名", "電子郵件"])
        self.download_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.download_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.download_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.download_table)

        rankings_layout.addWidget(QLabel("刪除次數排行榜"))
        self.delete_table = QTableWidget()
        self.delete_table.setColumnCount(5)
        self.delete_table.setHorizontalHeaderLabels(["排名", "使用者", "刪除次數", "姓名", "電子郵件"])
        self.delete_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.delete_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.delete_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.delete_table)

        center_window(self)
        self.set_stylesheet()

    def date_controls(self, layout: QHBoxLayout, tab_name: str):
        """
        添加日期篩選控件，包括開始和結束日期輸入框及日曆按鈕。

        參數:
            layout (QHBoxLayout): 目標佈局。
            tab_name (str): 標籤頁名稱（"system", "filestation", "rankings"）。

        返回:
            tuple: 包含開始和結束日期輸入框的元組。
        """
        from_label = QLabel("從:")
        from_label.setFixedWidth(30)
        layout.addWidget(from_label)
        layout.addSpacing(10)
        
        start_date_edit = QLineEdit()
        start_date_edit.setPlaceholderText("yyyy-MM-dd")
        start_date_edit.setAlignment(Qt.AlignCenter)
        start_date_edit.setFixedWidth(140)
        layout.addWidget(start_date_edit)
        
        start_date_btn = QPushButton()
        start_date_btn.setIcon(QIcon(resource_path("icons/calendar.png")))
        start_date_btn.setFixedSize(40, 40)
        start_date_btn.clicked.connect(lambda: self.show_start_date_picker(tab_name))
        layout.addWidget(start_date_btn)
        layout.addSpacing(25)

        to_label = QLabel("到:")
        to_label.setFixedWidth(30)
        layout.addWidget(to_label)
        layout.addSpacing(10)
        
        end_date_edit = QLineEdit()
        end_date_edit.setPlaceholderText("yyyy-MM-dd")
        end_date_edit.setAlignment(Qt.AlignCenter)
        end_date_edit.setFixedWidth(140)
        layout.addWidget(end_date_edit)
        
        end_date_btn = QPushButton()
        end_date_btn.setIcon(QIcon(resource_path("icons/calendar.png")))
        end_date_btn.setFixedSize(40, 40)
        end_date_btn.clicked.connect(lambda: self.show_end_date_picker(tab_name))
        layout.addWidget(end_date_btn)
        layout.addSpacing(25)

        if tab_name == "system":
            start_date_edit.returnPressed.connect(lambda: end_date_edit.setFocus())
            end_date_edit.returnPressed.connect(lambda: self.priority_combo.setFocus())
        elif tab_name == "filestation":
            start_date_edit.returnPressed.connect(lambda: end_date_edit.setFocus())
            end_date_edit.returnPressed.connect(lambda: self.event_combo.setFocus())
        elif tab_name == "rankings":
            start_date_edit.returnPressed.connect(lambda: end_date_edit.setFocus())

        return start_date_edit, end_date_edit

    def show_start_date_picker(self, tab_name):
        """
        顯示開始日期選擇器對話框，並更新開始日期輸入框。

        參數:
            tab_name (str): 標籤頁名稱（"system", "filestation", "rankings"）。
        """
        start_date_edit = self.system_start_date_edit if tab_name == "system" else self.filestation_start_date_edit if tab_name == "filestation" else self.rankings_start_date_edit
        end_date_text = (self.system_end_date_edit if tab_name == "system" else self.filestation_end_date_edit if tab_name == "filestation" else self.rankings_end_date_edit).text()
        start_date_text = start_date_edit.text()
        initial_date = datetime.strptime(start_date_text, "%Y-%m-%d").date() if start_date_text and self.validate_date(start_date_text) else None
        end_date = datetime.strptime(end_date_text, "%Y-%m-%d").date() if end_date_text and self.validate_date(end_date_text) else None

        dialog = DatePickerDialog(self, QDate(initial_date.year, initial_date.month, initial_date.day) if initial_date else None)
        if end_date:
            dialog.calendar.setMaximumDate(QDate(end_date.year, end_date.month, end_date.day))
        
        if dialog.exec_():
            selected_date = dialog.get_selected_date()
            self.start_date = selected_date.toPyDate()
            start_date_edit.setText(selected_date.toString("yyyy-MM-dd"))

    def show_end_date_picker(self, tab_name):
        """
        顯示結束日期選擇器對話框，並更新結束日期輸入框。

        參數:
            tab_name (str): 標籤頁名稱（"system", "filestation", "rankings"）。
        """
        end_date_edit = self.system_end_date_edit if tab_name == "system" else self.filestation_end_date_edit if tab_name == "filestation" else self.rankings_end_date_edit
        start_date_text = (self.system_start_date_edit if tab_name == "system" else self.filestation_start_date_edit if tab_name == "filestation" else self.rankings_start_date_edit).text()
        end_date_text = end_date_edit.text()
        initial_date = datetime.strptime(end_date_text, "%Y-%m-%d").date() if end_date_text and self.validate_date(end_date_text) else None
        start_date = datetime.strptime(start_date_text, "%Y-%m-%d").date() if start_date_text and self.validate_date(start_date_text) else None

        dialog = DatePickerDialog(self, QDate(initial_date.year, initial_date.month, initial_date.day) if initial_date else None)
        if start_date:
            dialog.calendar.setMinimumDate(QDate(start_date.year, start_date.month, start_date.day))
        
        if dialog.exec_():
            selected_date = dialog.get_selected_date()
            self.end_date = selected_date.toPyDate()
            end_date_edit.setText(selected_date.toString("yyyy-MM-dd"))

    def validate_date(self, date_text):
        """
        驗證日期字符串的格式是否為有效日期。

        參數:
            date_text (str): 要驗證的日期字符串。

        返回:
            bool: 若格式有效，返回 True；否則返回 False。
        """
        try:
            parts = date_text.split("-")
            if len(parts) != 3 or not (len(parts[0]) == 4 and parts[0].isdigit()) or not (1 <= int(parts[1]) <= 12) or not (1 <= int(parts[2]) <= 31):
                return False
            datetime.strptime(f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}", "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def priority_controls(self, layout: QHBoxLayout, include_priority_combo: bool = True):
        """
        添加優先層級篩選控件到佈局中，包括下拉選單。

        參數:
            layout (QHBoxLayout): 目標佈局。
            include_priority_combo (bool): 是否包含優先層級下拉選單。
        """
        if include_priority_combo:
            priority_label = QLabel("優先層級:")
            priority_label.setFixedWidth(90)
            layout.addWidget(priority_label)
            layout.addSpacing(5)
            self.priority_combo = QComboBox()
            self.priority_combo.setFixedWidth(170)
            self.priority_combo.addItems(["全部"] + list(System_Log.PRIORITY_MAPPING.values()))
            self.priority_combo.currentTextChanged.connect(self.on_priority_changed)
            layout.addWidget(self.priority_combo)
            layout.addSpacing(20)

    def on_priority_changed(self, priority_text):
        """
        處理優先層級篩選變化，更新選中的優先層級。

        參數:
            priority_text (str): 選中的優先層級。
        """
        self.selected_priority = priority_text if priority_text != "全部" else None
    
    def event_controls(self, layout: QHBoxLayout, include_event_combo: bool):
        """
        添加事件類型篩選控件到佈局中，包括下拉選單。

        參數:
            layout (QHBoxLayout): 目標佈局。
            include_event_combo (bool): 是否包含事件類型下拉選單。
        """
        if include_event_combo:
            event_label = QLabel("事件類別:")
            event_label.setFixedWidth(90)
            layout.addWidget(event_label)
            layout.addSpacing(5)
            self.event_combo = QComboBox()
            self.event_combo.setFixedWidth(170)
            self.event_combo.addItems(["全部"] + list(FilesStation_Log.EVENT_MAPPING.values()))
            self.event_combo.currentTextChanged.connect(self.on_event_changed)
            layout.addWidget(self.event_combo)
            layout.addSpacing(20)

    def on_event_changed(self, event_text):
        """
        處理事件類型篩選變化，更新選中的事件類型。

        參數:
            event_text (str): 選中的事件類型。
        """
        self.selected_event = event_text if event_text != "全部" else None

    def search_export_buttons(self, layout: QHBoxLayout):
        """
        添加搜尋和匯出按鈕到佈局中。

        參數:
            layout (QHBoxLayout): 目標佈局。
        """
        search_btn = QPushButton("搜尋")
        search_btn.clicked.connect(self.fetch_logs)
        search_btn.setFixedSize(60, 40)
        layout.addWidget(search_btn)
        layout.addSpacing(10)
        export_btn = QPushButton("匯出")
        export_btn.clicked.connect(self.export_logs)
        export_btn.setFixedSize(60, 40)
        layout.addWidget(export_btn)
        layout.addStretch()

    def system_jump_to_page(self):
        """
        跳轉到指定的系統日誌頁面。

        異常:
            ValueError: 若頁碼無效，顯示警告訊息並恢復當前頁碼。
        """
        try:
            page_num = int(self.system_page_edit.text())
            total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
            
            if 1 <= page_num <= total_pages:
                self.system_current_page = page_num
                self.update_system_table()
            else:
                QMessageBox.warning(self, "警告", f"頁碼必須在 1 到 {total_pages} 之間")
                self.system_page_edit.setText(str(self.system_current_page))
        except ValueError:
            self.system_page_edit.setText(str(self.system_current_page))

    def system_prev_page(self):
        """
        切換到系統日誌的上一頁並更新表格。
        """
        if self.system_current_page > 1:
            self.system_current_page -= 1
            self.update_system_table()

    def system_next_page(self):
        """
        切換到系統日誌的下一頁並更新表格。
        """
        total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        if self.system_current_page < total_pages:
            self.system_current_page += 1
            self.update_system_table()

    def update_system_table(self):
        """
        更新系統日誌表格的顯示內容，根據當前頁碼顯示篩選後的日誌數據。
        """
        self.system_table.setRowCount(0)
        start_idx = (self.system_current_page - 1) * self.ROWS_PER_PAGE
        end_idx = min(start_idx + self.ROWS_PER_PAGE, len(self.system_filtered_logs))
        display_rows = end_idx - start_idx

        self.system_table.setRowCount(display_rows)
        for row_idx in range(display_rows):
            log_entry = self.system_filtered_logs[start_idx + row_idx]
            for col_idx, col in enumerate(["優先層級", "日誌", "時間", "使用者", "事件"]):
                self.system_table.setItem(row_idx, col_idx, QTableWidgetItem(str(log_entry[col])))

        total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        self.system_page_edit.setText(str(self.system_current_page))
        self.findChild(QLabel, "systemTotalPages").setText(f"/ 共 {total_pages} 頁")
        
        self.system_prev_btn.setEnabled(self.system_current_page > 1)
        self.system_next_btn.setEnabled(self.system_current_page < total_pages)

    def filestation_jump_to_page(self):
        """
        跳轉到指定的檔案管理日誌頁面。

        異常:
            ValueError: 若頁碼無效，顯示警告訊息並恢復當前頁碼。
        """
        try:
            page_num = int(self.filestation_page_edit.text())
            total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
            
            if 1 <= page_num <= total_pages:
                self.filestation_current_page = page_num
                self.update_filestation_table()
            else:
                QMessageBox.warning(self, "警告", f"頁碼必須在 1 到 {total_pages} 之間")
                self.filestation_page_edit.setText(str(self.filestation_current_page))
        except ValueError:
            self.filestation_page_edit.setText(str(self.filestation_current_page))

    def filestation_prev_page(self):
        """
        切換到檔案管理日誌的上一頁並更新表格。
        """
        if self.filestation_current_page > 1:
            self.filestation_current_page -= 1
            self.update_filestation_table()

    def filestation_next_page(self):
        """
        切換到檔案管理日誌的下一頁並更新表格。
        """
        total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        if self.filestation_current_page < total_pages:
            self.filestation_current_page += 1
            self.update_filestation_table()

    def update_filestation_table(self):
        """
        更新檔案管理日誌表格的顯示內容，根據當前頁碼顯示篩選後的日誌數據。
        """
        self.filestation_table.setRowCount(0)
        start_idx = (self.filestation_current_page - 1) * self.ROWS_PER_PAGE
        end_idx = min(start_idx + self.ROWS_PER_PAGE, len(self.filestation_filtered_logs))
        display_rows = end_idx - start_idx

        self.filestation_table.setRowCount(display_rows)
        for row_idx in range(display_rows):
            log_entry = self.filestation_filtered_logs[start_idx + row_idx]
            for col_idx, col in enumerate(["日誌", "時間", "IP位址", "使用者", "事件", "檔案/資料夾", "檔案大小", "檔案名稱"]):
                self.filestation_table.setItem(row_idx, col_idx, QTableWidgetItem(str(log_entry[col])))

        total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        self.filestation_page_edit.setText(str(self.filestation_current_page))
        self.findChild(QLabel, "filestationTotalPages").setText(f"/ 共 {total_pages} 頁")
        
        self.filestation_prev_btn.setEnabled(self.filestation_current_page > 1)
        self.filestation_next_btn.setEnabled(self.filestation_current_page < total_pages)

    def fetch_logs(self):
        """
        根據篩選條件從 NAS 獲取日誌數據，並更新對應標籤頁的表格。

        異常:
            Exception: 若獲取日誌失敗，顯示錯誤訊息。
        """
        try:
            is_initial_load = (
                not any([self.system_start_date_edit.text(), self.filestation_start_date_edit.text(), self.rankings_start_date_edit.text(),
                         self.system_end_date_edit.text(), self.filestation_end_date_edit.text(), self.rankings_end_date_edit.text()]) and
                self.selected_priority is None and self.selected_event is None
            )

            current_tab = self.tabs.currentIndex()
            start_date_text = (self.system_start_date_edit if current_tab == 0 else self.filestation_start_date_edit if current_tab == 1 else self.rankings_start_date_edit).text()
            end_date_text = (self.system_end_date_edit if current_tab == 0 else self.filestation_end_date_edit if current_tab == 1 else self.rankings_end_date_edit).text()

            if start_date_text and not self.validate_date(start_date_text):
                QMessageBox.warning(self, "警告", "開始日期格式無效")
                return
            self.start_date = datetime.strptime(start_date_text, "%Y-%m-%d").date() if start_date_text else None

            if end_date_text and not self.validate_date(end_date_text):
                QMessageBox.warning(self, "警告", "結束日期格式無效")
                return
            self.end_date = datetime.strptime(end_date_text, "%Y-%m-%d").date() if end_date_text else None

            if self.start_date and self.end_date and self.start_date > self.end_date:
                QMessageBox.warning(self, "警告", "開始日期不能晚於結束日期")
                return

            if is_initial_load or current_tab == 0:
                system_log_data = self.nas_client.fetch_system_logs()
                system_logs = system_log_data["data"]["items"]
                self.system_log.logs.clear()
                self.system_filtered_logs = []
                for log in system_logs:
                    log_time = format_date(log.get("time", ""))
                    if log_time:
                        date_match = (not self.start_date or not self.end_date) or (self.start_date <= log_time <= self.end_date)
                        priority = self.system_log.map_priority(log.get("level", "N/A"))
                        priority_match = (not self.selected_priority) or (priority == self.selected_priority)
                        if date_match and priority_match:
                            self.system_log.add_log(log)
                            self.system_filtered_logs.append({
                                "優先層級": priority,
                                "日誌": "System",
                                "時間": log["time"],
                                "使用者": log["who"],
                                "事件": log["descr"],
                            })
                self.system_current_page = 1
                self.update_system_table() if self.system_filtered_logs else self.system_page_label.setText("第 0 頁 / 共 0 頁")

            if is_initial_load or current_tab == 1:
                filestation_log_data = self.nas_client.fetch_filestation_logs()
                filestation_logs = filestation_log_data["data"]["items"]
                self.filestation_log.logs.clear()
                self.filestation_filtered_logs = []
                for log in filestation_logs:
                    log_time = format_date(log.get("time", ""))
                    if log_time:
                        date_match = (not self.start_date or not self.end_date) or (self.start_date <= log_time <= self.end_date)
                        event = self.filestation_log.map_event(log.get("cmd", "N/A"))
                        event_match = (not self.selected_event) or (event == self.selected_event)
                        if date_match and event_match:
                            self.filestation_log.add_log(log)
                            self.filestation_filtered_logs.append({
                                "日誌": "FileStation",
                                "時間": log["time"],
                                "IP位址": log["ip"],
                                "使用者": log["username"],
                                "事件": event,
                                "檔案/資料夾": "資料夾" if str(log["isdir"]).lower() == "true" else "檔案",
                                "檔案大小": log["filesize"],
                                "檔案名稱": log["descr"]
                            })
                self.filestation_current_page = 1
                self.update_filestation_table() if self.filestation_filtered_logs else self.filestation_page_label.setText("第 0 頁 / 共 0 頁")

            if is_initial_load or current_tab == 2:
                filestation_log_data = self.nas_client.fetch_filestation_logs()
                filestation_logs = filestation_log_data["data"]["items"]
                filtered_logs = []
                for log in filestation_logs:
                    log_time = format_date(log.get("time", ""))
                    if log_time and (not self.start_date or not self.end_date or (self.start_date <= log_time <= self.end_date)):
                        filtered_logs.append({
                            "日誌": "FileStation",
                            "時間": log["time"],
                            "IP位址": log["ip"],
                            "使用者": log["username"],
                            "事件": self.filestation_log.map_event(log["cmd"]),
                            "檔案/資料夾": "資料夾" if str(log["isdir"]).lower() == "true" else "檔案",
                            "檔案大小": log["filesize"],
                            "檔案名稱": log["descr"]
                        })
                if filtered_logs:
                    self.populate_rankings(pd.DataFrame(filtered_logs))

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"獲取日誌失敗: {str(e)}")

    def populate_rankings(self, df):
        """
        填充排行榜表格，顯示上傳、下載、刪除次數的前十名用戶。

        參數:
            df (pd.DataFrame): 包含檔案管理日誌數據的 DataFrame。
        """
        user_info_data = self.nas_client.fetch_user_info()
        user_info_dict = {user["name"]: {"description": user.get("description", "N/A"), "email": user.get("email", "N/A")} 
                        for user in user_info_data["data"]["users"]}

        ranking_log = Ranking_Log()

        for table, event, ranking_type in [
            (self.upload_table, "上傳", "upload"),
            (self.download_table, "下載", "download"),
            (self.delete_table, "刪除", "delete")
        ]:
            df_event = df[df["事件"].str.contains(event, na=False)].groupby("使用者").size().reset_index(name=f"{event}次數")
            df_event = df_event.sort_values(by=f"{event}次數", ascending=False, ignore_index=True).head(10)
            df_event["姓名"] = df_event["使用者"].map(lambda x: user_info_dict.get(x, {}).get("description", ""))
            df_event["信箱"] = df_event["使用者"].map(lambda x: user_info_dict.get(x, {}).get("email", ""))

            table.setRowCount(len(df_event))
            for idx, row in df_event.iterrows():
                for col_idx, value in enumerate([str(idx + 1), row["使用者"], str(row[f"{event}次數"]), row["姓名"], row["信箱"]]):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(idx, col_idx, item)
                
                ranking_log.add_log(
                    ranking_type=ranking_type,
                    rank=idx + 1,
                    username=row["使用者"],
                    count=row[f"{event}次數"],
                    name=row["姓名"],
                    email=row["信箱"]
                )
            
            table.resizeColumnsToContents()
        
        self.ranking_log = ranking_log

    def export_logs(self):
        """
        匯出當前標籤頁的日誌數據至 Excel 檔案。

        異常:
            Exception: 若匯出失敗，顯示錯誤訊息。
        """
        try:
            current_tab = self.tabs.currentIndex()
            if current_tab == 0:
                if not self.system_log.logs:
                    QMessageBox.warning(self, "警告", "沒有系統日誌可匯出")
                    return
                if self.system_log.save_to_file():
                    QMessageBox.information(self, "成功", f"系統日誌已保存至 {self.system_log.log_file}")
                else:
                    QMessageBox.critical(self, "錯誤", "匯出失敗")
            elif current_tab == 1:
                if not self.filestation_log.logs:
                    QMessageBox.warning(self, "警告", "沒有檔案管理日誌可匯出")
                    return
                if self.filestation_log.save_to_file():
                    QMessageBox.information(self, "成功", f"檔案管理日誌已保存至 {self.filestation_log.log_file}")
                else:
                    QMessageBox.critical(self, "錯誤", "匯出失敗")   
            elif current_tab == 2:
                if not hasattr(self, 'ranking_log') or not self.ranking_log.logs:
                    QMessageBox.warning(self, "警告", "沒有排行榜數據可匯出")
                    return
                try:
                    if self.ranking_log.save_to_excel():
                        QMessageBox.information(self, "成功", f"排行榜數據已保存至 {self.ranking_log.log_file}")
                    else:
                        QMessageBox.critical(self, "錯誤", "匯出失敗")
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"匯出排行榜失敗: {str(e)}")
        
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出失敗: {str(e)}")
        
    def closeEvent(self, event):
        """處理視窗關閉事件
        Args:
            event: 關閉事件
        """
        if self.nas_client and self.nas_client.sid:
            self.nas_client.logout()
        event.accept()

    def set_stylesheet(self):
        """
        設置日誌窗口的樣式表，定義 UI 外觀。
        """
        down_arrow_path = resource_path("icons/down-arrow.png").replace("\\", "/")
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #ECF0F1;
                font-family: Yu Gothic UI;
            }}
            QLineEdit, QComboBox {{
                background-color: #F9F9F9;
                border: 1px solid #979EA9; 
                border-radius: 5px; 
                padding: 5px;
                color: #333333;
                font-family: Yu Gothic UI;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #979EA9;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                background: #F9F9F9;
            }}
            
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                image: url("{down_arrow_path}");
            }}
            
            QComboBox::drop-down:hover {{
                background: #C6D9F1;
            }}
            
            QPushButton, QToolButton {{
                background-color: #BFD1E5;
                color: #333333;
                border: None; 
                border-radius: 5px; 
                padding: 8px;
            }}
            
            QPushButton:hover, QToolButton:hover {{
                background-color: #C6D9F1; 
            }}
            
            QPushButton:disabled {{
                background-color: #D3D3D3;
                color: #A9A9A9;
            }}
            
            QLabel {{
                color: #333333;
                font-family: Yu Gothic UI;
            }}
            
            QHeaderView::section {{
                text-align:center;
            }}
        """)

if __name__ == "__main__":
    """
    程式入口，啟動應用程式並顯示登入窗口。
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("Yu Gothic UI", 12))
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())