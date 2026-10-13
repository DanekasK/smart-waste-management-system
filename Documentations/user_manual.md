# Smart Waste Management System - Operations & Maintenance Manual

---

## 1. Purpose & User Roles

This manual provides operating and maintenance guidelines for facility teams:

- **System Maintainers:** Responsible for sensor calibration, script daemon management, database schemas, and dashboard updates.
- **Facility Management:** Uses the web dashboard to track real-time bin capacity, historical trash distributions, and peak usage trends.
- **Custodial Staff:** Monitors physical bin statuses and responds to automated email/SMS dispatch notifications when bins exceed capacity.

---

## 2. Component Maintenance

Maintainers manage four core software daemons:
- `sensor_led.py`: Collects ultrasonic distance measurements, calculates fill percentage, updates the database, and drives status LEDs.
- `ir_sensor.py`: Reads the MCP3008 ADC SPI stream to detect and log break-beam drop events.
- `smtp_alerts.py`: Checks latest fill percentages against configured alert thresholds and dispatches notifications.
- `data.R`: Serves the live interactive telemetry dashboard.

---

## 3. Safe Change & Testing Workflow

Before modifying hardware or scripts:
1. Stop running background daemons (`pkill -f python3`).
2. Implement wiring or code adjustments.
3. Test connectivity and database writes using dry-run scripts.
4. Confirm new records appear in `ultrasonic_readings` and `ir_sensor_events`.
5. Restart the monitoring daemons in background mode.

---

## 4. Troubleshooting Guide

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **No ultrasonic data in DB** | Sensor wiring loose / MySQL connection offline | Check network connectivity and verify `sensor_led.py` process is active. |
| **IR drops not registering** | Optical beam misaligned / baseline drift | Run automatic calibration routine in `ir_sensor.py`. |
| **LEDs dim or flickering** | Insufficient current draw | Verify 5V 3A external power supply and common ground wiring. |
| **Alerts not sending** | Threshold not exceeded / SMTP credentials unverified | Check recipient status in `smtp_contacts` table and verify `.env` settings. |
| **Dashboard not loading** | Database query failure / R packages missing | Confirm MySQL daemon is running and verify required R packages are installed. |
