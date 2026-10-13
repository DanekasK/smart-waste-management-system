#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import board
import neopixel
from datetime import datetime
import mysql.connector

# Import configurations
from config import (
    SENSORS,
    NUM_LEDS,
    LEDS_PER_BIN,
    MAX_DISTANCE_CM,
    ULTRASONIC_LOOP_DELAY,
    ULTRASONIC_TIMEOUT_SEC,
    REMOTE_DB_ENABLED,
    DB_TYPE,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

# --- LED Setup ---
LED_PIN = board.D12
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.3, auto_write=False)

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
for trig, echo in SENSORS:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)
    GPIO.output(trig, False)

time.sleep(2)

# --- Database Connection Logic ---
db_conn = None
db_cursor = None

def connect_db():
    global db_conn, db_cursor
    if REMOTE_DB_ENABLED and DB_TYPE == "mysql":
        try:
            db_conn = mysql.connector.connect( host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=5
            )
            db_cursor = db_conn.cursor()
            print(f"[{datetime.now()}] MySQL connected successfully.")
        except Exception as e:
            print(f"[{datetime.now()}] MySQL connect failed: {e}")
            db_conn = None

def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    start_time = time.time()
    pulse_start = start_time
    pulse_end = start_time

    while GPIO.input(echo) == 0:
        pulse_start = time.time()
        if pulse_start - start_time > ULTRASONIC_TIMEOUT_SEC:
            return None

    while GPIO.input(echo) == 1:
        pulse_end = time.time()
        if pulse_end - pulse_start > ULTRASONIC_TIMEOUT_SEC:
            return None

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

def distance_to_fill(distance, max_cm=MAX_DISTANCE_CM):
    if distance is None:
        return 0.0  # Default to empty if sensor fails
    if distance <= 2: # Physical limit of sensor
        return 100.0
    if distance >= max_cm:
        return 0.0
    return round(100.0 * (1.0 - distance / max_cm), 1)

def get_color(distance):
    if distance is None:if distance is None:
        return (0, 0, 255)      # Blue = Error
    elif distance < 10:
        return (255, 0, 0)      # Red = Full
    elif distance < 25:
        return (255, 255, 0)    # Yellow = Warning
    else:
        return (0, 255, 0)      # Green = OK

# Initial connection
connect_db()

try:
    while True:
        # Check database health and reconnect if lost
        if REMOTE_DB_ENABLED and (db_conn is None or not db_conn.is_connected()):
            connect_db()

        pixels.fill((0, 0, 0))

        for i, (trig, echo) in enumerate(SENSORS):
            compartment_id = i + 1
            distance = get_distance(trig, echo)
            fill = distance_to_fill(distance)
            color = get_color(distance)

            # Update LED Array
            start = i * LEDS_PER_BIN
            end = start + LEDS_PER_BIN
            for j in range(start, end):
                if j < NUM_LEDS:
                    pixels[j] = color

            # Database Updates
            if db_cursor is not None:
                try:
                    # 1. Insert into history table
                    sql_raw = "INSERT INTO ultrasonic_readings (bin_id, distance_cm, fill_percent) VALUES (%s, %s, %s)"
                    db_cursor.execute(sql_raw, (compartment_id, distance, fill))

                except mysql.connector.Error as err:
                    print(f"Iteration error for bin {compartment_id}: {err}")

        # Commit all changes for this loop at once
        if db_conn and db_conn.is_connected():
            try:
                db_conn.commit()
            except Exception as e:
                print(f"Commit failed: {e}")

        pixels.show()
        time.sleep(ULTRASONIC_LOOP_DELAY)

except KeyboardInterrupt:
    print("\\nScript stopped by user.")

finally:
    if db_cursor:
        db_cursor.close()
    if db_conn:
        db_conn.close()

    # Cleanup hardware
    GPIO.cleanup()
    pixels.fill((0, 0, 0))
    pixels.show()
    print("Cleanup complete.")
