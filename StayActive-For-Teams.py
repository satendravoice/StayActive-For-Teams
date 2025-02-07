import sys
import time
import pyautogui
from PyQt5 import QtWidgets, QtGui, QtCore

class AutomationThread(QtCore.QThread):
    update_status = QtCore.pyqtSignal(str)
    dashboard_update = QtCore.pyqtSignal(int, str)  # (row, status)
    progress_update = QtCore.pyqtSignal(int)         # (progress percent)

    def __init__(self, parent=None):
        super(AutomationThread, self).__init__(parent)
        self._running = False

    def run(self):
        self._running = True
        self.update_status.emit("Automation started.")
        self.dashboard_update.emit(4, "Running")
        while self._running:
            try:
                # Get current mouse position.
                current_position = pyautogui.position()
                # Simulate activity: Move mouse by 10 pixels right, then return.
                pyautogui.moveRel(10, 0, duration=0.1)
                time.sleep(0.2)
                pyautogui.moveTo(current_position[0], current_position[1], duration=0.1)
                # Automation cycle: 60 seconds with progress updates.
                for i in range(60):
                    if not self._running:
                        break
                    progress_value = int(((i + 1) / 60) * 100)
                    self.progress_update.emit(progress_value)
                    time.sleep(1)
                # After each cycle, update the dashboard.
                self.dashboard_update.emit(4, "Running")
            except Exception as e:
                self.update_status.emit(f"Error: {e}")
        self.update_status.emit("Automation stopped.")
        self.dashboard_update.emit(4, "Stopped")
        self.progress_update.emit(0)

    def stop(self):
        self._running = False

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Teams Active Tool")
        self.setFixedSize(600, 650)  # Increased window size for all UI elements
        self.automation_start_time = None
        self.elapsed_timer = QtCore.QTimer()
        self.elapsed_timer.setInterval(1000)
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        self.init_ui()
        self.automation_thread = None
        self.create_tray_icon()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Overall Status Label
        self.status_label = QtWidgets.QLabel("Status: Not Running")
        font = QtGui.QFont()
        font.setPointSize(12)
        self.status_label.setFont(font)
        main_layout.addWidget(self.status_label)

        # Dashboard GroupBox for process steps.
        dashboard_box = QtWidgets.QGroupBox("Dashboard")
        dashboard_box.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        main_layout.addWidget(dashboard_box)
        dash_layout = QtWidgets.QVBoxLayout(dashboard_box)

        # Dashboard Table: 5 processes shown without scrolling.
        self.dashboard_table = QtWidgets.QTableWidget()
        self.dashboard_table.setColumnCount(2)
        self.dashboard_table.setRowCount(5)
        self.dashboard_table.setHorizontalHeaderLabels(["Process", "Status"])
        self.dashboard_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_table.verticalHeader().setVisible(False)
        self.dashboard_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.dashboard_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        # Fixed height to fit 5 rows (adjust as needed)
        self.dashboard_table.setFixedHeight(5 * 35 + 30)

        self.processes = [
            "Initialization",
            "Prevent System Sleep",
            "Auto Mouse Movement",
            "Keep Teams Active",
            "Automation Loop"
        ]
        for row, process in enumerate(self.processes):
            process_item = QtWidgets.QTableWidgetItem(process)
            status_item = QtWidgets.QTableWidgetItem("Pending")
            self.dashboard_table.setItem(row, 0, process_item)
            self.dashboard_table.setItem(row, 1, status_item)
        dash_layout.addWidget(self.dashboard_table)

        # Automation Info GroupBox for Start Time and Elapsed Time.
        info_box = QtWidgets.QGroupBox("Automation Info")
        info_box.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        main_layout.addWidget(info_box)
        info_layout = QtWidgets.QHBoxLayout(info_box)
        info_layout.setSpacing(20)

        self.start_time_label = QtWidgets.QLabel("App Start Time: Not Started")
        self.start_time_label.setFont(QtGui.QFont("Arial", 10))
        info_layout.addWidget(self.start_time_label)

        self.elapsed_time_label = QtWidgets.QLabel("Elapsed Time: 00:00:00")
        self.elapsed_time_label.setFont(QtGui.QFont("Arial", 10))
        info_layout.addWidget(self.elapsed_time_label)

        # Progress Bar for automation cycle.
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Cycle Progress: %p%")
        self.progress_bar.setFixedHeight(25)
        main_layout.addWidget(self.progress_bar)

        # Buttons Layout.
        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start Automation")
        self.start_button.setFixedHeight(40)
        self.start_button.clicked.connect(self.start_automation)
        button_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton("Stop & Restore")
        self.stop_button.setFixedHeight(40)
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        # Watermark Label with clickable GitHub hyperlink.
        self.watermark = QtWidgets.QLabel()
        self.watermark.setTextFormat(QtCore.Qt.RichText)
        self.watermark.setText(
            '<a style="color:#555555; text-decoration: none;" href="https://github.com/satendravoice?tab=repositories">'
            'App is Developed By Satendra Goswami – satendravoice</a>'
        )
        self.watermark.setAlignment(QtCore.Qt.AlignCenter)
        self.watermark.setOpenExternalLinks(True)
        watermark_font = QtGui.QFont("Arial", 9)
        self.watermark.setFont(watermark_font)
        main_layout.addWidget(self.watermark)

        # Joke Label at the bottom.
        self.joke_label = QtWidgets.QLabel("Joke: This app is so active, even your coffee might get jealous!")
        self.joke_label.setAlignment(QtCore.Qt.AlignCenter)
        joke_font = QtGui.QFont("Arial", 10, QtGui.QFont.StyleItalic)
        self.joke_label.setFont(joke_font)
        self.joke_label.setStyleSheet("color: #555555;")
        main_layout.addWidget(self.joke_label)

    def create_tray_icon(self):
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        show_action = QtWidgets.QAction("Show", self)
        hide_action = QtWidgets.QAction("Hide", self)
        quit_action = QtWidgets.QAction("Exit", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QtWidgets.qApp.quit)
        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def update_dashboard_row(self, row, status):
        self.dashboard_table.item(row, 1).setText(status)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_elapsed_time(self):
        if self.automation_start_time is None:
            return
        elapsed = int(time.time() - self.automation_start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        self.elapsed_time_label.setText("Elapsed Time: {:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))

    def start_automation(self):
        # Update dashboard statuses.
        self.update_dashboard_row(0, "Done")
        self.update_dashboard_row(1, "Done")
        self.update_dashboard_row(2, "Running")
        self.update_dashboard_row(3, "Running")
        self.update_dashboard_row(4, "Starting...")
        # Record and display the start time.
        self.automation_start_time = time.time()
        formatted_start = time.strftime("%H:%M:%S", time.localtime(self.automation_start_time))
        self.start_time_label.setText("App Start Time: " + formatted_start)
        self.elapsed_time_label.setText("Elapsed Time: 00:00:00")
        self.elapsed_timer.start()

        if not self.automation_thread or not self.automation_thread.isRunning():
            self.automation_thread = AutomationThread()
            self.automation_thread.update_status.connect(self.update_status)
            self.automation_thread.dashboard_update.connect(self.update_dashboard_row)
            self.automation_thread.progress_update.connect(self.update_progress)
            self.automation_thread.start()
            self.status_label.setText("Status: Automation Running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def stop_automation(self):
        if self.automation_thread and self.automation_thread.isRunning():
            self.automation_thread.stop()
            self.automation_thread.wait()
            self.elapsed_timer.stop()
            self.status_label.setText("Status: Not Running")
            self.update_dashboard_row(2, "Stopped")
            self.update_dashboard_row(3, "Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setValue(0)

    def update_status(self, message):
        self.status_label.setText("Status: " + message)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Teams Active Tool",
            "Application minimized to tray.",
            QtWidgets.QSystemTrayIcon.Information,
            2000
        )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F0F0F0;
        }
        QLabel {
            color: #333333;
        }
        QGroupBox {
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:disabled {
            background-color: #A5D6A7;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #CCCCCC;
        }
        QProgressBar {
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            width: 10px;
        }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
