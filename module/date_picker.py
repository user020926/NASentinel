from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QCalendarWidget, QDialogButtonBox, QHBoxLayout, QToolButton, QLabel)
from PyQt5.QtCore import Qt, QDate
from utils import center_window

class DatePickerDialog(QDialog):
    """
    日期選擇器對話框類，提供日曆介面讓使用者選擇日期。

    屬性:
        selected_date (QDate): 使用者選擇的日期。
        is_from_picker (bool): 是否為開始日期選擇器。
        min_date (QDate): 可選擇的最早日期。
        max_date (QDate): 可選擇的最晚日期。
        calendar (QCalendarWidget): 日曆控件。
    """
    def __init__(self, parent=None, initial_date=None, is_from_picker=False):
        """
        初始化 DatePickerDialog 實例。

        參數:
            parent (QWidget): 父窗口，預設為 None。
            initial_date (QDate): 初始選中的日期，預設為當前日期。
            is_from_picker (bool): 是否為開始日期選擇器，預設為 False。
        """
        super().__init__(parent)
        self.setWindowTitle("日期選擇")
        self.setModal(True)
        self.setFixedSize(450, 400)
        
        self.selected_date = initial_date if initial_date else QDate.currentDate()
        self.is_from_picker = is_from_picker
        self.min_date = QDate(2000, 1, 1)
        self.max_date = QDate.currentDate()
        
        self.setup_ui()
        center_window(self)
        self.set_stylesheet()
        self.format_calendar()

    def setup_ui(self):
        """
        設置對話框的 UI 介面，包括導航欄、日曆和按鈕。
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        nav_layout = QHBoxLayout()
        self.prev_button = QToolButton(text="◄")
        self.prev_button.clicked.connect(self.last_month)
        self.prev_button.setFixedSize(40, 40)
        
        self.date_label = QLabel(alignment=Qt.AlignCenter)
        
        self.next_button = QToolButton(text="►")
        self.next_button.clicked.connect(self.next_month)
        self.next_button.setFixedSize(40, 40)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.date_label, 1)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(self.selected_date)
        self.calendar.setFirstDayOfWeek(Qt.Sunday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setDateRange(self.min_date, self.max_date)
        self.calendar.setNavigationBarVisible(False)
        self.calendar.currentPageChanged.connect(self.month_changed)
        self.calendar.clicked[QDate].connect(self.update_selected_date)
        layout.addWidget(self.calendar)

        self.calendar.installEventFilter(self)

        buttons = QDialogButtonBox()
        buttons.addButton("確認", QDialogButtonBox.AcceptRole).clicked.connect(self.accept)
        buttons.addButton("取消", QDialogButtonBox.RejectRole).clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.update_display()

    def format_calendar(self):
        """
        格式化日曆，禁用早於開始日期的日期。
        """
        if not hasattr(self.parent(), 'from_date') or self.is_from_picker:
            return
        
        from_date = getattr(self.parent(), 'from_date', QDate())
        if not from_date.isValid():
            return

        disabled_format = QTextCharFormat()
        disabled_format.setBackground(QBrush(QColor(240, 240, 240)))
        disabled_format.setForeground(QBrush(QColor(100, 100, 100)))
        
        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        days_in_month = QDate(year, month, 1).daysInMonth()
        
        for day in range(1, days_in_month + 1):
            date = QDate(year, month, day)
            if date < from_date:
                self.calendar.setDateTextFormat(date, disabled_format)
        
        self.calendar.updateCells()

    def last_month(self):
        """
        切換到上個月。
        """
        new_date = self.calendar.selectedDate().addMonths(-1)
        if new_date >= self.min_date:
            self.calendar.setSelectedDate(new_date)
            self.update_display()
            self.format_calendar()

    def next_month(self):
        """
        切換到下個月。
        """
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(1)
        if (new_date.year() < self.max_date.year() or (new_date.year() == self.max_date.year() and new_date.month() <= self.max_date.month())):
            self.calendar.setSelectedDate(new_date)
            self.update_display()
            self.format_calendar()

    def month_changed(self, year: int, month: int):
        """
        處理月份變更事件，更新顯示。

        參數:
            year (int): 當前年份。
            month (int): 當前月份。
        """
        self.update_display()
        self.format_calendar()

    def get_selected_date(self) -> QDate:
        """
        獲取使用者選擇的日期。

        返回:
            QDate: 選中的日期。
        """
        return self.selected_date

    def update_selected_date(self, date: QDate):
        """
        更新選中的日期。

        參數:
            date (QDate): 選中的新日期。
        """
        self.selected_date = date
        if self.is_from_picker and hasattr(self.parent(), 'to_date_picker'):
            self.parent().to_date_picker.format_calendar()
            
    def update_display(self):
        """
        更新日期標籤和導航按鈕的顯示狀態。
        """
        current_date = self.calendar.selectedDate()
        month_names = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        self.date_label.setText(f"{current_date.year()}年{month_names[current_date.month()-1]}")
        prev_month_date = current_date.addMonths(-1)
        last_month_date = current_date.addMonths(1) 
        self.prev_button.setEnabled(prev_month_date >= self.min_date)
        self.next_button.setEnabled(last_month_date.year() < self.max_date.year() or (last_month_date.year() == self.max_date.year() and last_month_date.month() <= self.max_date.month()))

    def showEvent(self, event):
        """
        處理窗口顯示事件，格式化日曆。

        參數:
            event (QShowEvent): 顯示事件。
        """
        super().showEvent(event)
        self.format_calendar()

    def wheelEvent(self, event):
        """
        處理滑鼠滾輪事件，切換月份。

        參數:
            event (QWheelEvent): 滾輪事件。
        """
        delta = event.angleDelta().y()
        if delta > 0:
            self.last_month()
        elif delta < 0:
            self.next_month()
        event.accept()

    def keyPressEvent(self, event):
        """
        處理鍵盤事件，支援 Enter 確認和 Esc 取消。

        參數:
            event (QKeyEvent): 鍵盤事件。
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            event.accept()
            self.accept()
            return
        elif event.key() == Qt.Key_Escape:
            event.accept()
            self.reject()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """
        事件過濾器，處理日曆的鍵盤事件。

        參數:
            obj (QObject): 事件目標物件。
            event (QEvent): 事件物件。

        返回:
            bool: 若事件被處理，返回 True；否則返回 False。
        """
        if obj == self.calendar and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
                self.keyPressEvent(event)
                return True
        return super().eventFilter(obj, event)
    
    def set_stylesheet(self):
        """
        設置對話框的樣式表，定義 UI 外觀。
        """
        self.setStyleSheet("""
            DatePickerDialog {
                background-color: #ECF0F1;
                font-family: Yu Gothic UI;
            }
            QCalendarWidget QAbstractItemView {
                font-size: 14px;
                selection-background-color: #4A90E2;
                selection-color: white;
            }
            QCalendarWidget QWidget#qt_calendar_weekdaybar QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                padding: 5px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
            QToolButton, QPushButton {
                background-color: #BFD1E5;
                color: #333333;
                border: none;
                border-radius: 4px;
            }
            QToolButton:hover, QPushButton:hover {
                background-color: #C6D9F1;
            }
            QPushButton {
                min-width: 80px;
                padding: 8px;
                font-size: 14px;
            }
        """)