from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import QRect, Signal, Slot, Qt, QPointF, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont, QPolygonF
import sys
import math
from thread import DataThread, CameraThread, MapThread
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime
import pyautogui
import pygetwindow as gw
import time
import ctypes
from ctypes import wintypes
from datetime import datetime



class BatteryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.battery_level = 100  # Varsayılan batarya seviyesi
        self.setFixedSize(100, 50)
        self.setStyleSheet("background: transparent;")

    def set_battery_level(self, level):
        self.battery_level = max(0, min(level, 100))  # Batarya seviyesini 0 ile 100 arasında tut
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            rect = self.rect()

            # Batarya çerçevesi çizimi
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawRoundedRect(rect.adjusted(1, 1, -2, -2), 10, 10)

            # Batarya seviyesi dolumu
            if self.battery_level < 20:
                fill_color = QColor(255, 0, 0)  # Kırmızı renk
            else:
                fill_color = QColor(0, 255, 0)  # Yeşil renk

            painter.setBrush(fill_color)
            fill_width = (self.battery_level / 100) * (rect.width() - 6)  # Dolum genişliği
            painter.drawRoundedRect(rect.adjusted(2, 2, -(rect.width() - 6 - fill_width), -2), 10, 10)

            # Batarya seviyesi metni
            painter.setPen(Qt.black)
            painter.drawText(rect, Qt.AlignCenter, f"{self.battery_level}%")
        finally:
            painter.end()

class SignalStrengthWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signal_strength = 100  # Varsayılan sinyal gücü
        self.setFixedSize(30, 50)
        self.setStyleSheet("background: transparent;")

    def set_signal_strength(self, strength):
        self.signal_strength = max(0, min(strength, 100))  # Sinyal gücünü 0 ile 100 arasında tut
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            rect = self.rect()
            painter.setRenderHint(QPainter.Antialiasing)

            # Sinyal gücü çubukları çizimi
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)

            num_bars = 5
            bar_width = rect.width() / num_bars
            max_bar_height = rect.height() - 10

            for i in range(num_bars):
                bar_height = (self.signal_strength / 100) * max_bar_height * ((i + 1) / num_bars)
                painter.setBrush(QColor(0, 255, 0) if self.signal_strength > 20 else QColor(255, 0, 0))
                painter.drawRect(i * bar_width + 2, rect.height() - bar_height - 5, bar_width - 4, bar_height)
        finally:
            painter.end()
class PitchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pitch = 0  # Başlangıç pitch değeri
        self.setFixedSize(300, 400)  # Widget boyutlarını büyüttük

    def set_pitch(self, pitch):
        self.pitch = pitch
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Widget boyutları
        width = self.width()
        height = self.height()

        # Orta noktayı hesapla
        center_y = height // 2

        # Çizgiler için ayarlar
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        font = QFont("Arial", 12)  # Yazı boyutu biraz daha büyük
        painter.setFont(font)

        # Sabit yeşil çizgi
        pen.setColor(Qt.green)
        painter.setPen(pen)
        green_line_length = width // 3  # Yeşil çizgiyi kısalttık
        start_x = (width - green_line_length) // 2
        end_x = start_x + green_line_length
        painter.drawLine(start_x, center_y, end_x, center_y)
        painter.drawText(end_x + 5, center_y + 5, "0")

        # Siyah çizgiler ve pitch değerleri
        pen.setColor(Qt.black)
        painter.setPen(pen)
        pitch_values = [-20, -15, -10, -5, 5, 10, 15, 20]  # Yeni pitch değerleri
        line_height = 40  # Çizgiler arası mesafe

        for value in pitch_values:
            line_y = center_y - (value - self.pitch) * line_height / 10
            if abs(value) == 10 or abs(value) == 20:
                line_length = width // 2  # Uzun çizgi
            else:
                line_length = width // 3  # Kısa çizgi

            # Çizgiyi ortada hizalama
            start_x = (width - line_length) // 2
            end_x = start_x + line_length

            painter.drawLine(start_x, line_y, end_x, line_y)
            painter.drawText(end_x + 5, line_y + 5, str(value))

        painter.end()


class HUDWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0
        self.roll_scale_factor = 0.5  # Ölçekleme faktörü
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        

    def update_hud(self, data):
        self.roll = data.get('roll', 0) * self.roll_scale_factor  # Ölçekleme faktörünü uygulayarak roll değerini güncelleyin
        self.update()

    def draw_curve(self, painter):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        center_x = self.width() // 2
        center_y = 160
        radius = 120
        start_angle = -60
        end_angle = 60

        painter.setRenderHint(QPainter.Antialiasing)

        for angle in range(start_angle, end_angle + 1):
            rad = math.radians(angle)
            x = center_x + radius * math.sin(rad)
            y = center_y - radius * math.cos(rad)
            painter.drawPoint(int(x), int(y))

        font = QFont("Arial", 10)
        painter.setFont(font)
        for i in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:  # Güncellenmiş açılar ve ortadaki 0
            rad = math.radians(i)
            x = center_x + radius * math.sin(rad)
            y = center_y - radius * math.cos(rad)
            painter.drawText(int(x) - 10, int(y) - 10, str(abs(i)))

    def draw_additional_shapes(self, painter):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        center_x = self.width() // 2
        center_y = self.height() // 2

        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawLine(center_x - 90, center_y, center_x - 30, center_y)
        painter.drawLine(center_x + 30, center_y, center_x + 90, center_y)
        painter.drawEllipse(center_x - 10, center_y - 10, 20, 20)

    def draw_triangle(self, painter):
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)

        center_x = self.width() // 2
        center_y = 50

        points = [
            QPointF(center_x - 10, center_y + 10),
            QPointF(center_x + 10, center_y + 10),
            QPointF(center_x, center_y - 10)
        ]

        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPolygon(QPolygonF(points))

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.save()
        painter.translate(self.width() // 2, self.height() // 2)
        painter.rotate(self.roll)
        painter.translate(-self.width() // 2, -self.height() // 2)

        self.draw_curve(painter)
        self.draw_additional_shapes(painter)
        painter.restore()

        self.draw_triangle(painter)

        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KOZMOS AVIATION GROUND STATION")
        self.setGeometry(100, 100, 1920, 1080) 
        self.setStyleSheet("background-color: #2e5a88;")

        self.add_top_centered_label("KOZMOS YER İSTASYONU", "bahnschrift", 24, "#FFFFFF")

        # ARM/DISARM Butonu
        self.button = QPushButton("ARM/DISARM", self)
        self.button.setGeometry(QRect(10, 650, 80, 40))
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #FF0000; 
                color: white;
                border-radius: 15px;
                font-size: 8px;
                font-weight: bold;
                padding: 10px;
                border: 2px solid #8B0000;
            }
            QPushButton:hover {
                background-color: #FF3333;
            }
            QPushButton:pressed {
                background-color: #CC0000;
            }
        """)
        self.button.clicked.connect(self.toggle_arm_disarm)

        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(QRect(10, 150, 640, 480))
        self.camera_label.setStyleSheet("background: black;")

        self.hud_widget = HUDWidget(self)
        self.hud_widget.setGeometry(self.camera_label.geometry())
        self.hud_widget.raise_()

        self.map_view = QWebEngineView(self)
        self.map_view.setGeometry(QRect(890, 150, 640, 480))

        self.create_side_display("Hız: 0.0 m/s", "speed_label", side='right')
        self.create_side_display("Yükseklik: 0.0 m", "altitude_label", side='left')

        self.battery_widget = BatteryWidget(self)
        self.battery_widget.setGeometry(QRect(10, 70, 150, 70))

        self.signal_widget = SignalStrengthWidget(self)
        self.signal_widget.setGeometry(QRect(1350, 70, 30, 60))

        self.armed_label = QLabel("DISARMED", self)
        self.armed_label.setGeometry(QRect(585, 590, 100, 50))
        self.armed_label.setStyleSheet("""
            background-color: transparent;
            color: red;
            font-weight: bold;
        """)

        self.mode_label = QLabel("MODE: UNKNOWN", self)
        self.mode_label.setGeometry(QRect(30, 590, 200, 50))
        self.mode_label.setStyleSheet("""
            background-color: transparent;
            color: red;
            font-weight: bold;
        """)

        self.clock_label = QLabel(self)
        self.clock_label.setGeometry(QRect(1430, 70, 200, 50))
        self.clock_label.setStyleSheet("""
            background-color: transparent;
            color: white;
            font-weight: bold;
            font-size: 18px;
        """)

        self.middle_widget = QWidget(self)
        self.middle_widget.setGeometry(QRect(650, 150, 240, 480))
        self.middle_layout = QVBoxLayout(self.middle_widget)
        self.middle_widget.setStyleSheet("background-color: #959595 ;")

        self.middle_widget = QWidget(self)
        self.middle_widget.setGeometry(QRect(650, 150, 240, 480))
        self.middle_layout = QVBoxLayout(self.middle_widget)
        self.middle_widget.setStyleSheet("background-color: #959595 ;")

        self.add_image_to_layout('2_milli-tek-hamlesi.png', 'tubitak.png')

        self.middle_layout.addStretch(0)
        self.add_image_to_layout_single('kozmossaydam.png', 300, 200)
        self.middle_layout.addStretch(0)
        self.add_image_to_layout_single('3_teknofest_logo.png', 120, 70)

        self.middle_layout.setAlignment(Qt.AlignCenter)



        self.middle_layout.setAlignment(Qt.AlignCenter)

        self.pitch_widget = PitchWidget(self)
        self.pitch_widget.setGeometry(QRect(180 , 190, 200, 200))
        self.pitch_widget.setStyleSheet("background: transparent;")

        self.start_threads()
        self.update_clock()

    def add_image_to_layout(self, image_path_1, image_path_2):
        layout = QHBoxLayout()
        label1 = QLabel(self)
        pixmap1 = QPixmap(image_path_1)
        if pixmap1.isNull():
            print(f"Error: Unable to load image from {image_path_1}")
        pixmap1 = pixmap1.scaled(200, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label1.setPixmap(pixmap1)

        label2 = QLabel(self)
        pixmap2 = QPixmap(image_path_2)
        if pixmap2.isNull():
            print(f"Error: Unable to load image from {image_path_2}")
        pixmap2 = pixmap2.scaled(250, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label2.setPixmap(pixmap2)

        layout.addWidget(label1)
        layout.addWidget(label2)
        self.middle_layout.addLayout(layout)

    def add_image_to_layout_single(self, image_path, width, height):
        label = QLabel(self)
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            print(f"Error: Unable to load image from {image_path}")
            return

        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)
        self.middle_layout.addWidget(label, alignment=Qt.AlignCenter)


    def add_top_centered_label(self, text, font_family, font_size, color):
        label = QLabel(text, self)
        font = QFont(font_family, font_size)
        label.setFont(font)
        label.setStyleSheet(f"color: {color} ; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        label.setGeometry(QRect(250 , 30 , 1000,50))

    def create_side_display(self, text, label_attr, side):
        label = QLabel(text, self.camera_label)
        label.setStyleSheet("""
            background-color: transparent;
            border: 2px solid black;
            border-radius: 10px;
            color: black;
            font-weight: bold;
        """)
        label_width = 80
        label_height = 30
        y_center = (self.camera_label.height() - label_height) // 2

        if side == 'left':
            label.setGeometry(10, y_center, label_width, label_height)
        elif side == 'right':
            label.setGeometry(self.camera_label.width() - label_width - 10, y_center, label_width, label_height)

        setattr(self, label_attr, label)

    def start_threads(self):
        self.data_thread = DataThread(self)
        self.data_thread.data_changed.connect(self.update_data)
        self.data_thread.start()

        self.camera_thread = CameraThread(camera_index=1, parent=self)  # FPV kameranızı başlatmak için indeks 1
        self.camera_thread.camera_data_changed.connect(self.update_camera)
        self.camera_thread.start()

        self.map_thread = MapThread(self)
        self.data_thread.data_changed.connect(self.update_map_location)
        self.map_thread.map_data_changed.connect(self.update_map)
        self.map_thread.start()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

    @Slot(dict)
    def update_data(self, data):
        self.speed_label.setText(f"{data.get('airspeed', 0):.2f} m/s")
        self.altitude_label.setText(f"{data.get('altitude', 0):.2f} m")

        if 'roll' in data:
            self.hud_widget.update_hud(data)

        if 'pitch' in data:
            self.pitch_widget.set_pitch(data['pitch'])

        if 'battery_level' in data:
            self.battery_widget.set_battery_level(data['battery_level'])

        if 'signal_strength' in data:
            self.signal_widget.set_signal_strength(data['signal_strength'])

        if 'armed' in data:
            if data['armed']:
                self.armed_label.setText("ARMED")
                self.armed_label.setStyleSheet("""
                    background-color: transparent;
                    color: red;
                    font-weight: bold;
                """)
            else:
                self.armed_label.setText("DISARMED")
                self.armed_label.setStyleSheet("""
                    background-color: transparent;
                    color: red;
                    font-weight: bold;
                """)

        if 'mode' in data:
            self.mode_label.setText(f"{data['mode']}")

    @Slot(QImage, float)
    def update_camera(self, image, yaw):
        pixmap = QPixmap.fromImage(image)
        painter = QPainter(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        center_x, center_y = pixmap.width() // 2, pixmap.height() // 2
        end_x = center_x + int(50 * math.sin(math.radians(yaw)))
        end_y = center_y - int(50 * math.cos(math.radians(yaw)))
        painter.drawLine(center_x, center_y, end_x, end_y)
        painter.end()
        self.camera_label.setPixmap(pixmap)

    @Slot(dict)
    def update_map_location(self, data):
        if 'latitude' in data and 'longitude' in data:
            self.map_thread.set_location(data['latitude'], data['longitude'])

    @Slot(str)
    def update_map(self, map_html):
        self.map_view.setHtml(map_html)

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(f"{current_time}")

    def toggle_arm_disarm(self):
        # ARM/DISARM butonuna tıklama işlevi
        self.bring_mission_planner_to_front()
        button_x, button_y = 261, 773  # Kendi koordinatlarınızı girin
        pyautogui.click(button_x, button_y)
    
        self.send_mission_planner_to_back()

    def bring_mission_planner_to_front(self):
        mission_planner = gw.getWindowsWithTitle('Mission Planner')[0]
        hwnd = mission_planner._hWnd
        if mission_planner.isMinimized:
            mission_planner.restore()
        self.set_window_transparency(hwnd, 1)
        mission_planner.activate()
        time.sleep(1)

    def send_mission_planner_to_back(self):
        time.sleep(1)
        mission_planner = gw.getWindowsWithTitle('Mission Planner')[0]
        hwnd = mission_planner._hWnd
        self.set_window_transparency(hwnd, 1)
        mission_planner.minimize()
        main_window = gw.getWindowsWithTitle(self.windowTitle())[0]
        main_window.activate()

    def set_window_transparency(self, hwnd, alpha):
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        LWA_ALPHA = 0x2

        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
            ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)

    def closeEvent(self, event):
        self.camera_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())