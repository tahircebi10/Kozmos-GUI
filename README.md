# KOZMOS Aviation Ground Station

## Overview

The KOZMOS Aviation Ground Station is a GUI application designed for monitoring and controlling UAV (Unmanned Aerial Vehicle) operations. It features real-time data visualization including speed, altitude, battery level, signal strength, and a HUD (Heads-Up Display) for orientation. The application also integrates with a camera feed and a map display.

## Features

- **Real-time Data Display**: Monitors and displays UAV telemetry such as speed, altitude, roll, and pitch.
- **Battery and Signal Strength Indicators**: Visual indicators for battery level and signal strength.
- **HUD Visualization**: A graphical representation of roll and pitch values.
- **Camera Feed Integration**: Live camera feed with yaw indicator.
- **Map Display**: Visualizes UAV's location on a map.
- **ARM/DISARM Control**: Button to toggle UAV's operational state.

## Requirements

- Python 3.x
- PySide6
- PyQtWebEngine
- Additional libraries (e.g., pyautogui, pygetwindow)

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd kozmoss-ground-station

2. Install the required packages:

    '''bash
    pip install PySide6 PyQtWebEngine pyautogui pygetwindow

3. Make sure you have a working Python environment and all dependencies are installed.

## Usage

1. Run the application:,

   ```bash
    python ui.py

## Architecture

The application is structured into several main components:
    MainWindow: The primary window containing all widgets.
    HUDWidget: Displays the roll and pitch in a graphical format.
    BatteryWidget: Visualizes battery level.
    SignalStrengthWidget: Displays signal strength with bar indicators.
    PitchWidget: Shows pitch values.
    DataThread: Handles data retrieval and updates.
    CameraThread: Manages the camera feed.
    MapThread: Integrates map data and location tracking.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Thanks to all contributors and the open-source community for the libraries and resources used in this project.
