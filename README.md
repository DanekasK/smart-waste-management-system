# IoT Multi-Compartment Smart Waste Management System

An automated, multi-compartment smart waste monitoring and analytics system built with a Raspberry Pi, hardware sensors, MySQL database, automated SMTP alert pipeline, and an interactive R Shiny real-time dashboard.

---

## Overview

Traditional waste bins often overflow before collection or get emptied while nearly empty. This system automates capacity tracking, usage-pattern detection, visual status indicators, and dispatch alerts for a 4-compartment waste receptacle (Trash, Paper/Aluminum, Compost, Glass/Plastic).

### Key Features
- **Ultrasonic Fill-Level Sensing:** Periodically measures distance in each bin compartment and calculates real-time fullness percentages.
- **IR Beam-Break Event Tracking:** Captures drop/usage events and logs timestamped interactions per compartment.
- **Visual Status Feedback:** Addressable WS2812B LED rings dynamically update color indicators (Green: `< 50%`, Yellow: `50%–84%`, Red: `≥ 85%`).
- **Automated Dispatch Alerts:** Background monitor triggers email and SMS-gateway alerts to facility managers when bins reach critical capacity.
- **Interactive Web Dashboard:** Real-time R Shiny interface visualizing current fill levels, total trash distribution, and peak usage hours/days.

---

## System Architecture & Workflow
Hardware Layer:
  -  Ultrasonic Sensors  ──►  Calculate Fill %  ──►  WS2812B LEDs (Status Colors)
  -  IR Break Sensors    ──►  Detect Drop Events

Database Layer:
  -  Sensor Data         ──►  MySQL Database (waste_management)

Application Layer:
  -  MySQL Database      ──►  SMTP Alert Daemon  ──►  SMS & Email Alerts
  -  MySQL Database      ──►  R Shiny Dashboard  ──►  Live Fill Levels & Charts
---

## Hardware Components

- **Controller:** Raspberry Pi (Raspberry Pi OS)
- **Depth Sensors:** 4x HC-SR04 Ultrasonic Distance Sensors
- **Drop Detection:** 4x Infrared (IR) Break-Beam Sensors via MCP3008 ADC (SPI Interface)
- **Status Indicators:** WS2812B Addressable RGB LED Strip / Rings (144 LEDs total)
- **Structure:** Custom 4-compartment enclosure with sensor mounting lid

---

## Repository Structure

```text
├── hardware/
│   ├── config.py             # Hardware pinouts & baseline sensor configurations
│   ├── sensor_led.py         # Ultrasonic distance loop & LED controller
│   ├── ir_sensor.py          # MCP3008 ADC SPI loop for beam break detection
│   └── smtp_alerts.py        # Automated email & SMS threshold notification daemon
├── dashboard/
│   ├── app.R                 # Real-time R Shiny administrative dashboard
│   └── setup_apache.md       # Apache / Shiny server reverse proxy instructions
├── database/
│   └── schema.sql            # Table definitions for readings, IR events, and contacts
├── docs/                     # Schematics, design diagrams, and hardware photos
├── .env.example              # Template for database & SMTP credentials
├── .gitignore                # Files excluded from version control
└── README.md
```

---

## Database Schema

The system relies on a centralized MySQL schema (`waste_management`):

- `ultrasonic_readings`: Stores `bin_id`, `distance_cm`, `fill_percent`, and `reading_time`.
- `ir_sensor_events`: Logs `compartment_id`, `beam_broken` flags, and `event_time`.
- `smtp_contacts`: Stores notification recipient emails, carrier gateways, and alert thresholds.
- `Admins`: Stores administrator credentials and hashed passwords.

---

## Setup & Installation

### 1. Prerequisites
- Python 3.9+ with `pip`
- R 4.0+ with `shiny`, `bslib`, `DBI`, `RMariaDB`, `dplyr`, and `plotly`
- MySQL Server 8.0+

### 2. Environment Configuration
Copy the sample environment file and configure your credentials:

```bash
cp .env.example .env
```

Set your values in `.env`:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=waste_management
DB_USER=your_db_user
DB_PASSWORD=your_db_password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### 3. Running Hardware Daemons
```bash
# Start ultrasonic and LED monitoring
python hardware/sensor_led.py &

# Start IR beam drop detection
python hardware/ir_sensor.py &

# Start notification service
python hardware/smtp_alerts.py &
```

### 4. Running the Dashboard
```bash
Rscript -e "shiny::runApp('dashboard/app.R', port=3838, host='0.0.0.0')"
```

---

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
