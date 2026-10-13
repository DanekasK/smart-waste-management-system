# Raspberry Pi Hardware Setup & Pinout Documentation

**Platform:** Raspberry Pi (Raspberry Pi OS 64-bit / Bookworm)  
**Project:** Multi-Compartment IoT Smart Waste Monitoring System

---

## 1. System Configuration & Interfaces

1. Flash **Raspberry Pi OS (64-bit)** using Raspberry Pi Imager.
2. Enable **SSH** and configure local Wi-Fi settings.
3. Enable the **SPI Interface** via terminal:
   ```bash
   sudo raspi-config
   # Interface Options -> SPI -> Enable
   ```

---

## 2. Hardware Wiring Table

| Component | Pin Function | Raspberry Pi BCM Pin | Physical Pin | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **WS2812B NeoPixel** | Data In | GPIO 12 | Pin 32 | PWM control |
| **HC-SR04 (Bin 1 - Trash)** | Trig / Echo | GPIO 17 / GPIO 27 | Pin 11 / Pin 13 | Depth sensor |
| **HC-SR04 (Bin 2 - Paper)** | Trig / Echo | GPIO 23 / GPIO 24 | Pin 16 / Pin 18 | Depth sensor |
| **HC-SR04 (Bin 3 - Compost)**| Trig / Echo | GPIO 7 / GPIO 3 | Pin 26 / Pin 5 | Depth sensor |
| **HC-SR04 (Bin 4 - Glass)** | Trig / Echo | GPIO 22 / GPIO 25 | Pin 15 / Pin 22 | Depth sensor |
| **MCP3008 ADC** | SCLK / MISO / MOSI | GPIO 11 / GPIO 9 / GPIO 10 | Pin 23 / Pin 21 / Pin 19 | SPI Bus 0 |
| **MCP3008 ADC** | Chip Select (CS) | GPIO 8 (CE0) | Pin 24 | SPI Chip Select |
| **IR Break-Beam (1–4)** | Analog Output | Channels CH0 – CH3 | MCP3008 Pins 1–4 | Drop detection |

---

## 3. Power Supply Notes

- **Sensors & Pi:** Powered via 5V rail.
- **WS2812B LED Ring:** For a full 144-LED strip, use an external 5V 3A DC power supply with a shared common ground to the Raspberry Pi to avoid brownouts or flickering.
