from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QCalendarWidget, QDialogButtonBox, QHBoxLayout, QToolButton, QLabel)
from PyQt5.QtCore import Qt, QDate
from utils import center_window

class DatePickerDialog(QDialog):
    """
    Date picker dialog class providing a calendar interface for users to select a date.

    Attributes:
        selected_date (QDate): The date selected by the user.
        is_from_picker (bool): Whether this dialog serves as the start date picker.
        min_date (QDate): The earliest selectable date.
        max_date (QDate): The latest selectable date.
        calendar (QCalendarWidget): The calendar widget control.
    """
    def __init__(self, parent=None, initial_date=None, is_from_picker=False):
        """
        Initialize DatePickerDialog instance.

        Parameters:
            parent (QWidget): Parent window, defaults to None.
            initial_date (QDate): Initially selected date, defaults to current date.
            is_from_picker (bool): Whether this is a start date picker, defaults to False.
        """
        super().__init__(parent)
        self.setWindowTitle("Date Selection")
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
        Set up the dialog's UI interface, including navigation bar, calendar, and buttons.
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
        buttons.addButton("Confirm", QDialogButtonBox.AcceptRole).clicked.connect(self.accept)
        buttons.addButton("Cancel", QDialogButtonBox.RejectRole).clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.update_display()

    def format_calendar(self):
        """
        Format the calendar, disabling dates earlier than the start date.
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
        Switch to the previous month.
        """
        new_date = self.calendar.selectedDate().addMonths(-1)
        if new_date >= self.min_date:
            self.calendar.setSelectedDate(new_date)
            self.update_display()
            self.format_calendar()

    def next_month(self):
        """
        Switch to the next month.
        """
        current_date = self.calendar.selectedDate()
        new_date = current_date.addMonths(1)
        if (new_date.year() < self.max_date.year() or (new_date.year() == self.max_date.year() and new_date.month() <= self.max_date.month())):
            self.calendar.setSelectedDate(new_date)
            self.update_display()
            self.format_calendar()

    def month_changed(self, year: int, month: int):
        """
        Handle month change events and update the display.

        Parameters:
            year (int): Current year.
            month (int): Current month.
        """
        self.update_display()
        self.format_calendar()

    def get_selected_date(self) -> QDate:
        """
        Get the date selected by the user.

        Returns:
            QDate: Selected date.
        """
        return self.selected_date

    def update_selected_date(self, date: QDate):
        """
        Update the selected date.

        Parameters:
            date (QDate): Newly selected date.
        """
        self.selected_date = date
        if self.is_from_picker and hasattr(self.parent(), 'to_date_picker'):
            self.parent().to_date_picker.format_calendar()
            
    def update_display(self):
        """
        Update the display status of the date label and navigation buttons.
        """
        current_date = self.calendar.selectedDate()
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.date_label.setText(f"{month_names[current_date.month()-1]} {current_date.year()}")
        prev_month_date = current_date.addMonths(-1)
        last_month_date = current_date.addMonths(1) 
        self.prev_button.setEnabled(prev_month_date >= self.min_date)
        self.next_button.setEnabled(last_month_date.year() < self.max_date.year() or (last_month_date.year() == self.max_date.year() and last_month_date.month() <= self.max_date.month()))

    def showEvent(self, event):
        """
        Handle window show events and format the calendar.

        Parameters:
            event (QShowEvent): Window show event.
        """
        super().showEvent(event)
        self.format_calendar()

    def wheelEvent(self, event):
        """
        Handle mouse wheel events to switch months.

        Parameters:
            event (QWheelEvent): Mouse wheel event.
        """
        delta = event.angleDelta().y()
        if delta > 0:
            self.last_month()
        elif delta < 0:
            self.next_month()
        event.accept()

    def keyPressEvent(self, event):
        """
        Handle keyboard events, supporting Enter to confirm and Esc to cancel.

        Parameters:
            event (QKeyEvent): Keyboard event.
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
        Event filter to handle calendar keyboard events.

        Parameters:
            obj (QObject): Event target object.
            event (QEvent): Event object.

        Returns:
            bool: True if event was handled; False otherwise.
        """
        if obj == self.calendar and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
                self.keyPressEvent(event)
                return True
        return super().eventFilter(obj, event)
    
    def set_stylesheet(self):
        """
        Set stylesheet for the dialog to define UI appearance.
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