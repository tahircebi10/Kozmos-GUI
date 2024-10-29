import threading
import folium
import io
from PySide6.QtCore import QThread, Signal
from pymavlink import mavutil
from PySide6.QtGui import QImage
import cv2
import math
from folium.features import DivIcon
import base64
import sys


class DataThread(QThread):
    data_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.latest_data = {
            'latitude': 0,
            'longitude': 0,
            'altitude': 0,
            'relative_altitude': 0,
            'vx': 0,
            'vy': 0,
            'vz': 0,
            'heading': 0,
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'airspeed': 0,
            'ground_speed': 0,
            'battery_level': 100,
            'signal_strength': 100,
            'armed': False,
            'mode': 'UNKNOWN'  # Varsayılan mod değeri
        }
        self.home_latitude = None
        self.home_longitude = None

    def run(self):
        the_connection = mavutil.mavlink_connection('tcp:127.0.0.1:5762')
        the_connection.wait_heartbeat()

        while True:
            try:
                msg = the_connection.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE', 'VFR_HUD', 'SYS_STATUS', 'RADIO', 'HEARTBEAT'], blocking=True, timeout=5)
                if msg:
                    # Mode bilgilerini güncellemek için önce orijinal msg nesnesini kontrol et
                    if msg.get_type() == 'HEARTBEAT':
                        self.latest_data['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                        self.latest_data['mode'] = mavutil.mode_string_v10(msg)

                    msg_dict = msg.to_dict()

                    if msg_dict['mavpackettype'] == 'GLOBAL_POSITION_INT':
                        self.latest_data['latitude'] = msg_dict.get('lat', self.latest_data['latitude']) / 1e7 if 'lat' in msg_dict else self.latest_data['latitude']
                        self.latest_data['longitude'] = msg_dict.get('lon', self.latest_data['longitude']) / 1e7 if 'lon' in msg_dict else self.latest_data['longitude']
                        self.latest_data['altitude'] = msg_dict.get('alt', self.latest_data['altitude']) / 1e3 if 'alt' in msg_dict else self.latest_data['altitude']
                        self.latest_data['relative_altitude'] = msg_dict.get('relative_alt', self.latest_data['relative_altitude']) / 1e3 if 'relative_alt' in msg_dict else self.latest_data['relative_altitude']
                        self.latest_data['vx'] = msg_dict.get('vx', self.latest_data['vx']) / 100 if 'vx' in msg_dict else self.latest_data['vx']
                        self.latest_data['vy'] = msg_dict.get('vy', self.latest_data['vy']) / 100 if 'vy' in msg_dict else self.latest_data['vy']
                        self.latest_data['vz'] = msg_dict.get('vz', self.latest_data['vz']) / 100 if 'vz' in msg_dict else self.latest_data['vz']
                        self.latest_data['heading'] = msg_dict.get('hdg', self.latest_data['heading']) / 100 if 'hdg' in msg_dict else self.latest_data['heading']

                        # İlk konumu home noktası olarak kaydet
                        if self.home_latitude is None and self.home_longitude is None:
                            self.home_latitude = self.latest_data['latitude']
                            self.home_longitude = self.latest_data['longitude']

                        # Home noktasından olan uzaklığı hesapla
                        self.latest_data['distance_to_home'] = self.calculate_distance(
                            self.home_latitude, self.home_longitude, 
                            self.latest_data['latitude'], self.latest_data['longitude']
                        )

                    elif msg_dict['mavpackettype'] == 'ATTITUDE':
                        self.latest_data['roll'] = math.degrees(msg_dict.get('roll', self.latest_data['roll']))
                        self.latest_data['pitch'] = math.degrees(msg_dict.get('pitch', self.latest_data['pitch']))
                        self.latest_data['yaw'] = math.degrees(msg_dict.get('yaw', self.latest_data['yaw']))

                    elif msg_dict['mavpackettype'] == 'VFR_HUD':
                        self.latest_data['airspeed'] = msg_dict.get('airspeed', self.latest_data['airspeed'])
                        self.latest_data['ground_speed'] = msg_dict.get('groundspeed', self.latest_data['ground_speed'])

                    elif msg_dict['mavpackettype'] == 'SYS_STATUS':
                        self.latest_data['battery_level'] = msg_dict.get('battery_remaining', self.latest_data['battery_level'])

                    elif msg_dict['mavpackettype'] == 'RADIO':
                        self.latest_data['signal_strength'] = msg_dict.get('rssi', self.latest_data['signal_strength'])

                    self.data_changed.emit(self.latest_data)
            except Exception as e:
                print(f"Error receiving MAVLink message: {e}")

            QThread.msleep(100)

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        # Haversine formülü ile iki nokta arasındaki mesafeyi hesapla
        R = 6371  # Dünya'nın yarıçapı, kilometre cinsinden
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c  # Kilometre cinsinden mesafe
        return distance


class CameraThread(QThread):
    camera_data_changed = Signal(QImage, float)

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print(f"Error: Camera with index {camera_index} could not be opened.")
            sys.exit()
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.yaw = 0.0

    def run(self):
        while True:
            ret, frame = self.capture.read()
            if ret:
                # Resize the frame to 450x350
                frame_resized = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)

                # Convert the resized frame to QImage
                image = QImage(frame_resized.data, frame_resized.shape[0], frame_resized.shape[0], frame_resized.strides[0], QImage.Format_RGB888).rgbSwapped()

                # Emit the image and yaw angle
                self.camera_data_changed.emit(image, self.yaw)
            self.msleep(100)  # Adjust this value to control the frame rate

    def update_yaw(self, yaw):
        self.yaw = yaw

    def __del__(self):
        self.capture.release()




class MapThread(QThread):
    map_data_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lat = None
        self.lon = None
        self.route = []  # Konumları saklamak için bir liste ekledik
        self.home_lat = None
        self.home_lon = None

    def update_map(self, lat, lon):
        if lat is None or lon is None:
            return ""  # Return empty string if lat or lon is None

        folium_map = folium.Map(location=[lat, lon], zoom_start=15)

        # HOME noktasını ekle
        if self.home_lat is not None and self.home_lon is not None:
            folium.Marker([self.home_lat, self.home_lon], tooltip='HOME', icon=folium.Icon(color='green')).add_to(folium_map)

        # Add custom icon for the current location
        custom_icon_path = r'C:\Users\tahir\Documents\GUI-KOZMOS\Kozmos-GUI\assets\images\ucak.png'  # Raw string kullanıldı
        custom_icon = folium.CustomIcon(custom_icon_path, icon_size=(30, 30))  # Adjust the size as necessary
        folium.Marker([lat, lon], tooltip='Current Location', icon=custom_icon).add_to(folium_map)

        if self.home_lat is not None and self.home_lon is not None:
            folium.PolyLine([(self.home_lat, self.home_lon), (lat, lon)], color="blue", weight=2.5, opacity=1).add_to(folium_map)

            # Mesafeyi hesapla ve göster
            distance = self.calculate_distance(self.home_lat, self.home_lon, lat, lon)
            folium.Marker(
                [(self.home_lat + lat) / 2, (self.home_lon + lon) / 2],
                icon=DivIcon(icon_size=(150, 36), icon_anchor=(0, 0), html=f'<div style="font-size: 12pt; color: black;">{distance:.2f} km</div>')
            ).add_to(folium_map)

            # Mesafe kadar yarıçaplı bir daire ekle
            folium.Circle(
                radius=distance * 1000,  # Mesafeyi metre cinsinden veriyoruz
                location=[self.home_lat, self.home_lon],
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.1
            ).add_to(folium_map)
        else:
            folium.Marker([lat, lon], tooltip='Current Location', icon=custom_icon).add_to(folium_map)

        if self.route:
            folium.PolyLine(self.route, color="blue", weight=2.5, opacity=1).add_to(folium_map)

        data = io.BytesIO()
        folium_map.save(data, close_file=False)
        return data.getvalue().decode()

    def run(self):
        while True:
            if self.lat is not None and self.lon is not None:
                if self.home_lat is None and self.home_lon is None:
                    self.home_lat = self.lat
                    self.home_lon = self.lon
                self.route.append([self.lat, self.lon])  # Her yeni konumu rotaya ekleyin
                map_html = self.update_map(self.lat, self.lon)
                self.map_data_changed.emit(map_html)
            QThread.msleep(1000)  # Adjust the sleep time as necessary

    def set_location(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        # Haversine formülü ile iki nokta arasındaki mesafeyi hesapla
        R = 6371  # Dünya'nın yarıçapı, kilometre cinsinden
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c  # Kilometre cinsinden mesafe
        return distance