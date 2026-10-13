# /home/pi/trash_monitor/config.py

import os

# ==========================================
# 1. Ultrasonic Sensor Pin Configuration
# ==========================================
# Format: (Trig BCM, Echo BCM) per bin compartment
SENSORS = [
    (17, 27),  # Compartment 1 (Trash)
    (23, 24),  # Compartment 2 (Paper / Aluminum)
    (7, 3),    # Compartment 3 (Compost)
    (22, 25)   # Compartment 4 (Glass / Plastic)
]

MAX_DISTANCE_CM = 43.0
ULTRASONIC_LOOP_DELAY = 300       # 5 minutes between readings
ULTRASONIC_TIMEOUT_SEC = 0.03

# ==========================================
# 2. Addressable LED (WS2812B) Configuration
# ==========================================
NUM_LEDS = 144
LEDS_PER_BIN = 30

# ==========================================
# 3. IR Break-Beam / ADC (MCP3008) Settings
# ==========================================
BASELINES = [70, 80, 70, 30]
DEBOUNCE_S = 3.0
IR_LOOP_DELAY = 0.1
SPI_BUS = 0
SPI_DEVICE = 0
SPI_MAX_SPEED_HZ = 1000000
SAMPLES = 5

# ==========================================
# 4. Database & Storage Configuration
# ==========================================
LOCAL_DB_PATH = "trash_fallback.db"

# Remote Database Connection (Sanitized: Loaded from Environment)
REMOTE_DB_ENABLED = True
DB_TYPE = "mysql"
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "waste_management")
DB_USER = os.getenv("DB_USER", "db_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password_here")
