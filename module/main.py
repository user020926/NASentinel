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
Main application module responsible for implementing the graphical user interface 
for the NAS Log Query Application, including the login window and log display window.
"""

def resource_path(relative_path):
    """
    Get the absolute path to a resource, supporting both development and packaged execution environments.

    Parameters:
        relative_path (str): Relative path to the resource.

    Returns:
        str: Absolute path to the resource.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)
    return os.path.join(base_path, relative_path)

class LoginWindow(QMainWindow):
    """
    Login window class providing a graphical interface for NAS administrator login.

    Attributes:
        nas_client (NASClient): NAS client object used for interacting with the NAS API.
        system_log (System_Log): System log object used for recording system logs.
        filestation_log (FilesStation_Log): File Station log object used for recording File Station logs.
        ip_entry (QLineEdit): NAS IP input field.
        port_entry (QLineEdit): NAS port input field.
        admin_entry (QLineEdit): Administrator username input field.
        pwd_entry (QLineEdit): Administrator password input field.
        otp_entry (QLineEdit): 2FA verification code input field.
    """
    def __init__(self):
        """
        Initialize the LoginWindow instance, setting up window properties and UI components.
        """
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(700, 400, 480, 300)
        self.setWindowIcon(QIcon(resource_path("icons/NASentinel.ico")))
        self.nas_client = None
        self.system_log = System_Log()
        self.filestation_log = FilesStation_Log()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI components for the login window, including input fields, buttons, and stylesheets.
        """
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        self.ip_entry = self.add_field(input_layout, "NAS IP:", "e.g., 10.57.78.62")
        self.port_entry = self.add_field(input_layout, "NAS Port:", "e.g., 5000")
        self.admin_entry = self.add_field(input_layout, "Admin Username:")
        self.pwd_entry = self.add_field(input_layout, "Admin Password:", is_password=True)
        self.otp_entry = self.add_field(input_layout, "2FA Code:", "Enter 6-digit code, or leave blank if none")
        
        self.ip_entry.returnPressed.connect(lambda: self.port_entry.setFocus())
        self.port_entry.returnPressed.connect(lambda: self.admin_entry.setFocus())
        self.admin_entry.returnPressed.connect(lambda: self.pwd_entry.setFocus())
        self.pwd_entry.returnPressed.connect(lambda: self.otp_entry.setFocus())
        self.otp_entry.returnPressed.connect(self.attempt_login)
        layout.addWidget(input_widget)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.attempt_login)
        login_btn.setFixedSize(80, 40)
        layout.addWidget(login_btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        center_window(self)
        self.set_stylesheet()

    def add_field(self, layout: QVBoxLayout, label: str, placeholder: str = "", is_password: bool = False) -> QLineEdit:
        """
        Add an input field to the specified layout, including its label and text box.

        Parameters:
            layout (QVBoxLayout): Target layout.
            label (str): Field label text.
            placeholder (str): Placeholder text for the input box.
            is_password (bool): Whether the field is for a password.

        Returns:
            QLineEdit: The created text box object.
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
        Execute the NAS administrator login action, validating inputs and calling NASClient's login method.

        Raises:
            Exception: Displays an error message and clears sensitive fields if login fails.
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
            QMessageBox.information(self, "Success", "Administrator logged in successfully!")
            self.open_log_window()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")

    def validate_inputs(self) -> bool:
        """
        Validate the input fields for IP, port, username, and password.

        Returns:
            bool: Returns True if all inputs are valid; otherwise shows an error message and returns False.
        """
        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", self.ip_entry.text()):
            QMessageBox.critical(self, "Error", "Please enter a valid IP address")
            return False
        port_text = self.port_entry.text() or "5000"
        if not port_text.isdigit() or not (1 <= int(port_text) <= 65535):
            QMessageBox.critical(self, "Error", "Please enter a valid port number")
            return False
        if not self.admin_entry.text():
            QMessageBox.critical(self, "Error", "Please enter the admin username")
            return False
        if not self.pwd_entry.text():
            QMessageBox.critical(self, "Error", "Please enter the admin password")
            return False
        return True

    def clear_pwd(self):
        """
        Clear the password input field.
        """
        self.pwd_entry.clear()
        self.pwd_entry.setFocus()

    def clear_otp(self):
        """
        Clear the 2FA verification code input field.
        """
        self.otp_entry.clear()
        self.pwd_entry.setFocus()

    def open_log_window(self):
        """
        Open the log window and close the login window.
        """
        self.log_window = LogWindow(self.nas_client)
        self.log_window.show()
        self.clear_pwd()
        self.clear_otp()
        self.close()

    def set_stylesheet(self):
        """
        Set the stylesheet for the login window to define its visual appearance.
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
    Log window class providing display and filtering features for system logs, File Station logs, and rankings.

    Attributes:
        MAX_DISPLAY_ROWS (int): Maximum number of log rows to display.
        ROWS_PER_PAGE (int): Number of log rows displayed per page.
        nas_client (NASClient): NAS client object.
        system_log (System_Log): System log object.
        filestation_log (FilesStation_Log): File Station log object.
        ranking_log (Ranking_Log): Ranking log object.
        start_date (datetime.date | None): Selected start date for filtering.
        end_date (datetime.date): Selected end date for filtering.
        selected_priority (str | None): Selected priority level.
        selected_event (str | None): Selected event type.
        system_current_page (int): Current page index for system logs.
        filestation_current_page (int): Current page index for File Station logs.
        system_filtered_logs (list): Filtered system log dataset.
        filestation_filtered_logs (list): Filtered File Station log dataset.
    """
    MAX_DISPLAY_ROWS = 10000
    ROWS_PER_PAGE = 100

    def __init__(self, nas_client: NASClient):
        """
        Initialize LogWindow instance, setting up window properties and UI interface.

        Parameters:
            nas_client (NASClient): NAS client object.
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
        self.top_rankings = 10
        self.setup_ui()
        self.fetch_logs()

    def setup_ui(self):
        """
        Set up UI interface for the log window, including tabs, tables, filter controls, and pagination buttons.
        """
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tabs)
        self.system_tab = QWidget()
        self.tabs.addTab(self.system_tab, "System Logs")
        system_layout = QVBoxLayout(self.system_tab)
        system_controls_layout = QHBoxLayout()
        self.system_start_date_edit, self.system_end_date_edit = self.date_controls(system_controls_layout, "system")
        self.priority_controls(system_controls_layout, include_priority_combo=True)
        system_controls_layout.addSpacing(10)
        self.search_export_buttons(system_controls_layout)
        system_layout.addLayout(system_controls_layout)

        self.system_table = QTableWidget()
        self.system_table.setColumnCount(5)
        self.system_table.setHorizontalHeaderLabels(["Priority", "Log", "Time", "User", "Event"])
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
        system_pagination_layout.addWidget(QLabel("Page"))
        system_pagination_layout.addWidget(self.system_page_edit)

        total_pages_label = QLabel("/ Total 1 Pages")
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
        self.tabs.addTab(self.filestation_tab, "File Station Logs")
        filestation_layout = QVBoxLayout(self.filestation_tab)
        filestation_controls_layout = QHBoxLayout()
        self.filestation_start_date_edit, self.filestation_end_date_edit = self.date_controls(filestation_controls_layout, "filestation")
        self.event_controls(filestation_controls_layout, include_event_combo=True)
        filestation_controls_layout.addSpacing(10)
        self.search_export_buttons(filestation_controls_layout)
        filestation_layout.addLayout(filestation_controls_layout)

        self.filestation_table = QTableWidget()
        self.filestation_table.setColumnCount(8)
        self.filestation_table.setHorizontalHeaderLabels(["Log", "Time", "IP Address", "User", "Event", "File/Folder", "File Size", "File Name"])
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
        filestation_pagination_layout.addWidget(QLabel("Page"))
        filestation_pagination_layout.addWidget(self.filestation_page_edit)

        filestation_total_pages_label = QLabel("/ Total 1 Pages")
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
        self.tabs.addTab(self.rankings_tab, "Rankings")
        rankings_layout = QVBoxLayout(self.rankings_tab)
        rankings_controls_layout = QHBoxLayout()
        self.rankings_start_date_edit, self.rankings_end_date_edit = self.date_controls(rankings_controls_layout, "rankings")
        
        ranks_label = QLabel("Top:")
        ranks_label.setFixedWidth(30)
        rankings_controls_layout.addWidget(ranks_label)
        self.ranks_combo = QComboBox()
        self.ranks_combo.setFixedWidth(80)
        self.ranks_combo.addItems([str(i) for i in range(1, 21)])
        self.ranks_combo.setCurrentText("10")
        rankings_controls_layout.addWidget(self.ranks_combo)
        rankings_controls_layout.addSpacing(25)

        self.search_export_buttons(rankings_controls_layout)
        rankings_layout.addLayout(rankings_controls_layout)
        
        rankings_layout.addWidget(QLabel("Upload Count Ranking"))
        self.upload_table = QTableWidget()
        self.upload_table.setColumnCount(6)
        self.upload_table.setHorizontalHeaderLabels(["Rank", "User", "Upload Count", "File Size", "Name", "Email"])
        self.upload_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.upload_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.upload_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.upload_table)

        rankings_layout.addWidget(QLabel("Download Count Ranking"))
        self.download_table = QTableWidget()
        self.download_table.setColumnCount(6)
        self.download_table.setHorizontalHeaderLabels(["Rank", "User", "Download Count", "File Size", "Name", "Email"])
        self.download_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.download_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.download_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.download_table)

        rankings_layout.addWidget(QLabel("Delete Count Ranking"))
        self.delete_table = QTableWidget()
        self.delete_table.setColumnCount(6)
        self.delete_table.setHorizontalHeaderLabels(["Rank", "User", "Delete Count", "File Size", "Name", "Email"])
        self.delete_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.delete_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.delete_table.verticalHeader().setVisible(False)
        rankings_layout.addWidget(self.delete_table)

        center_window(self)
        self.set_stylesheet()

    def date_controls(self, layout: QHBoxLayout, tab_name: str):
        """
        Add date filter controls, including start and end date input fields and calendar buttons.

        Parameters:
            layout (QHBoxLayout): Target layout.
            tab_name (str): Tab name ("system", "filestation", "rankings").

        Returns:
            tuple: Tuple containing start and end date input field objects.
        """
        from_label = QLabel("From:")
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

        to_label = QLabel("To:")
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
        Display the start date picker dialog and update the start date input field.

        Parameters:
            tab_name (str): Tab name ("system", "filestation", "rankings").
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
        Display the end date picker dialog and update the end date input field.

        Parameters:
            tab_name (str): Tab name ("system", "filestation", "rankings").
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
        Validate whether the date string format is a valid date.

        Parameters:
            date_text (str): Date string to validate.

        Returns:
            bool: Returns True if the format is valid; otherwise returns False.
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
        Add priority level filter controls to the layout, including a drop-down menu.

        Parameters:
            layout (QHBoxLayout): Target layout.
            include_priority_combo (bool): Whether to include the priority level drop-down menu.
        """
        if include_priority_combo:
            priority_label = QLabel("Priority:")
            priority_label.setFixedWidth(90)
            layout.addWidget(priority_label)
            layout.addSpacing(5)
            self.priority_combo = QComboBox()
            self.priority_combo.setFixedWidth(170)
            self.priority_combo.addItems(["All"] + list(System_Log.PRIORITY_MAPPING.values()))
            self.priority_combo.currentTextChanged.connect(self.on_priority_changed)
            layout.addWidget(self.priority_combo)
            layout.addSpacing(20)

    def on_priority_changed(self, priority_text):
        """
        Handle changes in priority level filtering and update the selected priority level.

        Parameters:
            priority_text (str): Selected priority level.
        """
        self.selected_priority = priority_text if priority_text != "All" else None
    
    def event_controls(self, layout: QHBoxLayout, include_event_combo: bool):
        """
        Add event type filter controls to the layout, including a drop-down menu.

        Parameters:
            layout (QHBoxLayout): Target layout.
            include_event_combo (bool): Whether to include the event type drop-down menu.
        """
        if include_event_combo:
            event_label = QLabel("Event Type:")
            event_label.setFixedWidth(90)
            layout.addWidget(event_label)
            layout.addSpacing(5)
            self.event_combo = QComboBox()
            self.event_combo.setFixedWidth(170)
            self.event_combo.addItems(["All"] + list(FilesStation_Log.EVENT_MAPPING.values()))
            self.event_combo.currentTextChanged.connect(self.on_event_changed)
            layout.addWidget(self.event_combo)
            layout.addSpacing(20)

    def on_event_changed(self, event_text):
        """
        Handle changes in event type filtering and update the selected event type.

        Parameters:
            event_text (str): Selected event type.
        """
        self.selected_event = event_text if event_text != "All" else None

    def search_export_buttons(self, layout: QHBoxLayout):
        """
        Add search and export buttons to the layout.

        Parameters:
            layout (QHBoxLayout): Target layout.
        """
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.fetch_logs)
        search_btn.setFixedSize(60, 40)
        layout.addWidget(search_btn)
        layout.addSpacing(10)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_logs)
        export_btn.setFixedSize(60, 40)
        layout.addWidget(export_btn)
        layout.addStretch()

    def system_jump_to_page(self):
        """
        Jump to the specified system log page.

        Exceptions:
            ValueError: If the page number is invalid, display a warning message and restore the current page number.
        """
        try:
            page_num = int(self.system_page_edit.text())
            total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
            
            if 1 <= page_num <= total_pages:
                self.system_current_page = page_num
                self.update_system_table()
            else:
                QMessageBox.warning(self, "Warning", f"Page number must be between 1 and {total_pages}")
                self.system_page_edit.setText(str(self.system_current_page))
        except ValueError:
            self.system_page_edit.setText(str(self.system_current_page))

    def system_prev_page(self):
        """
        Switch to the previous page of system logs and update the table.
        """
        if self.system_current_page > 1:
            self.system_current_page -= 1
            self.update_system_table()

    def system_next_page(self):
        """
        Switch to the next page of system logs and update the table.
        """
        total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        if self.system_current_page < total_pages:
            self.system_current_page += 1
            self.update_system_table()

    def update_system_table(self):
        """
        Update the display content of the system log table to show filtered log data based on the current page number.
        """
        self.system_table.setRowCount(0)
        start_idx = (self.system_current_page - 1) * self.ROWS_PER_PAGE
        end_idx = min(start_idx + self.ROWS_PER_PAGE, len(self.system_filtered_logs))
        display_rows = end_idx - start_idx

        self.system_table.setRowCount(display_rows)
        for row_idx in range(display_rows):
            log_entry = self.system_filtered_logs[start_idx + row_idx]
            for col_idx, col in enumerate(["Priority", "Log", "Time", "User", "Event"]):
                self.system_table.setItem(row_idx, col_idx, QTableWidgetItem(str(log_entry[col])))

        total_pages = (len(self.system_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        self.system_page_edit.setText(str(self.system_current_page))
        self.findChild(QLabel, "systemTotalPages").setText(f"/ Total {total_pages} Pages")
        
        self.system_prev_btn.setEnabled(self.system_current_page > 1)
        self.system_next_btn.setEnabled(self.system_current_page < total_pages)

    def filestation_jump_to_page(self):
        """
        Jump to the specified File Station log page.

        Exceptions:
            ValueError: If the page number is invalid, display a warning message and restore the current page number.
        """
        try:
            page_num = int(self.filestation_page_edit.text())
            total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
            
            if 1 <= page_num <= total_pages:
                self.filestation_current_page = page_num
                self.update_filestation_table()
            else:
                QMessageBox.warning(self, "Warning", f"Page number must be between 1 and {total_pages}")
                self.filestation_page_edit.setText(str(self.filestation_current_page))
        except ValueError:
            self.filestation_page_edit.setText(str(self.filestation_current_page))

    def filestation_prev_page(self):
        """
        Switch to the previous page of File Station logs and update the table.
        """
        if self.filestation_current_page > 1:
            self.filestation_current_page -= 1
            self.update_filestation_table()

    def filestation_next_page(self):
        """
        Switch to the next page of File Station logs and update the table.
        """
        total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        if self.filestation_current_page < total_pages:
            self.filestation_current_page += 1
            self.update_filestation_table()

    def update_filestation_table(self):
        """
        Update the display content of the File Station log table to show filtered log data based on the current page number.
        """
        self.filestation_table.setRowCount(0)
        start_idx = (self.filestation_current_page - 1) * self.ROWS_PER_PAGE
        end_idx = min(start_idx + self.ROWS_PER_PAGE, len(self.filestation_filtered_logs))
        display_rows = end_idx - start_idx

        self.filestation_table.setRowCount(display_rows)
        for row_idx in range(display_rows):
            log_entry = self.filestation_filtered_logs[start_idx + row_idx]
            for col_idx, col in enumerate(["Log", "Time", "IP Address", "User", "Event", "File/Folder", "File Size", "File Name"]):
                self.filestation_table.setItem(row_idx, col_idx, QTableWidgetItem(str(log_entry[col])))

        total_pages = (len(self.filestation_filtered_logs) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        self.filestation_page_edit.setText(str(self.filestation_current_page))
        self.findChild(QLabel, "filestationTotalPages").setText(f"/ Total {total_pages} Pages")
        
        self.filestation_prev_btn.setEnabled(self.filestation_current_page > 1)
        self.filestation_next_btn.setEnabled(self.filestation_current_page < total_pages)

    def fetch_logs(self):
        """
        Fetch log data from the NAS based on filter conditions and update the table of the corresponding tab.

        Exceptions:
            Exception: If fetching logs fails, display an error message.
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
                QMessageBox.warning(self, "Warning", "Invalid start date format")
                return
            self.start_date = datetime.strptime(start_date_text, "%Y-%m-%d").date() if start_date_text else None

            if end_date_text and not self.validate_date(end_date_text):
                QMessageBox.warning(self, "Warning", "Invalid end date format")
                return
            self.end_date = datetime.strptime(end_date_text, "%Y-%m-%d").date() if end_date_text else None

            if self.start_date and self.end_date and self.start_date > self.end_date:
                QMessageBox.warning(self, "Warning", "Start date cannot be later than end date")
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
                                "Priority": priority,
                                "Log": "System",
                                "Time": log["time"],
                                "User": log["who"],
                                "Event": log["descr"],
                            })
                self.system_current_page = 1
                self.update_system_table() if self.system_filtered_logs else self.system_page_label.setText("Page 0 / Total 0 Pages")

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
                                "Log": "FileStation",
                                "Time": log["time"],
                                "IP Address": log["ip"],
                                "User": log["username"],
                                "Event": event,
                                "File/Folder": "Folder" if str(log["isdir"]).lower() == "true" else "File",
                                "File Size": log["filesize"],
                                "File Name": log["descr"]
                            })
                self.filestation_current_page = 1
                self.update_filestation_table() if self.filestation_filtered_logs else self.filestation_page_label.setText("Page 0 / Total 0 Pages")

            if is_initial_load or current_tab == 2:
                self.top_n_ranks = int(self.ranks_combo.currentText())
                filestation_log_data = self.nas_client.fetch_filestation_logs()
                filestation_logs = filestation_log_data["data"]["items"]
                filtered_logs = []
                for log in filestation_logs:
                    log_time = format_date(log.get("time", ""))
                    if log_time and (not self.start_date or not self.end_date or (self.start_date <= log_time <= self.end_date)):
                        filtered_logs.append({
                            "Log": "FileStation",
                            "Time": log["time"],
                            "IP Address": log["ip"],
                            "User": log["username"],
                            "Event": self.filestation_log.map_event(log["cmd"]),
                            "File/Folder": "Folder" if str(log["isdir"]).lower() == "true" else "File",
                            "File Size": log["filesize"],
                            "File Name": log["descr"]
                        })
                if filtered_logs:
                    self.populate_rankings(pd.DataFrame(filtered_logs))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch logs: {str(e)}")

    def populate_rankings(self, df):
        """
        Populate the rankings table to display top N users by upload, download, and delete counts.
        Also displays the total file size sum for each user.

        Parameters:
            df (pd.DataFrame): DataFrame containing file management log data.
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
            df_event = df[df["事件"].str.contains(event, na=False)].copy()
            df_event["檔案大小"] = df_event["檔案大小"].apply(self.parse_file_size)
            
            grouped = df_event.groupby("使用者").agg(次數=("事件", "size"), 檔案大小=("檔案大小", "sum")).reset_index()
            
            df_event = grouped.sort_values(by="次數", ascending=False, ignore_index=True).head(self.top_n_ranks)
            df_event["姓名"] = df_event["使用者"].map(lambda x: user_info_dict.get(x, {}).get("description", ""))
            df_event["信箱"] = df_event["使用者"].map(lambda x: user_info_dict.get(x, {}).get("email", ""))
            
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["排名", "使用者", "次數", "檔案大小", "姓名", "電子郵件"])
            
            table.setRowCount(len(df_event))
            for idx, row in df_event.iterrows():
                for col_idx, value in enumerate([
                    str(idx + 1), 
                    row["使用者"], 
                    str(row["次數"]), 
                    self.format_size(row["檔案大小"]), 
                    row["姓名"], 
                    row["信箱"]
                ]):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(idx, col_idx, item)
                
                ranking_log.add_log(
                    ranking_type=ranking_type,
                    rank=idx + 1,
                    username=row["使用者"],
                    count=row["次數"],
                    size=row["檔案大小"],
                    name=row["姓名"],
                    email=row["信箱"]
                )
            
            table.resizeColumnsToContents()
        
        self.ranking_log = ranking_log

    def top_rankings_changed(self, ranks_text):
        """
        Handle selection changes in the top rankings count, updating top_n_ranks and refreshing the leaderboard.

        Parameters:
            ranks_text (str): Selected ranking limit (1 to 20).
        """
        self.top_rankings = int(ranks_text)
        if self.tabs.currentIndex() == 2:
            self.fetch_logs()

    def parse_file_size(self, size_str):
        """
        Convert file size string into number of bytes.
        
        Parameters:
            size_str (str): File size string (e.g., "1.5 MB")
            
        Returns:
            int: Number of bytes
        """
        if size_str == "N/A":
            return 0
            
        try:
            size, unit = size_str.split()
            size = float(size)
            unit = unit.upper()
            
            if unit == "KB":
                return int(size * 1024)
            elif unit == "MB":
                return int(size * 1024 * 1024)
            elif unit == "GB":
                return int(size * 1024 * 1024 * 1024)
            else:
                return int(size)
        except:
            return 0

    def format_size(self, size):
        """
        Format byte count into a human-readable file size string (KB, MB, GB).
        
        Parameters:
            size (int): File size in bytes
            
        Returns:
            str: Formatted file size string
        """
        if size == 0:
            return "0 KB"
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} GB"

    def export_logs(self):
        """
        Export log data from the current tab to an Excel file.

        Exceptions:
            Exception: Displays an error message dialog if export fails.
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
        """
        Handle window close event.

        Args:
            event: Close event object.
        """
        if self.nas_client and self.nas_client.sid:
            self.nas_client.logout()
        event.accept()

    def set_stylesheet(self):
        """
        Set stylesheet for the log window to define UI appearance.
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
    Application entry point: launches the application and displays the login window.
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("Yu Gothic UI", 12))
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())