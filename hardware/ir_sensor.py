#!/usr/bin/env python3

import time
from datetime import datetime

import spidev
import mysql.connector

from config import (
    DEBOUNCE_S,
    IR_LOOP_DELAY,           
    SPI_BUS,
    SPI_DEVICE,
    SPI_MAX_SPEED_HZ,
    REMOTE_DB_ENABLED,
    DB_TYPE,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

SAMPLES = 3
CALIBRATION_SECONDS = 5

CHANNEL_TO_BIN = [3, 1, 4, 2]

# Per-channel tuning
TRIGGER_MARGINS = [120, 55, 70, 70]
RESET_MARGINS = [100, 30, 35, 35]
CONFIRM_READS = [3, 3, 2, 2]

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_MAX_SPEED_HZ

db_conn = None
db_cursor = None


def connect_db():
    global db_conn, db_cursor

    if not REMOTE_DB_ENABLED or DB_TYPE.lower() != "mysql":
        print("Remote MySQL disabled.")
        db_conn = None
        db_cursor = None
        return

    try:
        db_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True,
        )
        db_cursor = db_conn.cursor()
        print("MySQL connected for IR events.")
    except Exception as e:
        print("MySQL connect failed:", e)
        db_conn = None
        db_cursor = None


def ensure_db():
    global db_conn, db_cursor

    if db_conn is None or db_cursor is None:
        connect_db()
        return

    try:
        if not db_conn.is_connected():
            print("MySQL connection lost. Reconnecting...")
            connect_db()
        else:
            db_conn.ping(reconnect=True, attempts=3, delay=2)
    except Exception as e:
        print("MySQL ping/reconnect failed:", e)
        connect_db()


def read_adc(ch):
    adc = spi.xfer2([1, (8 + ch) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]


def read_adc_avg(ch, samples=SAMPLES):
    total = 0
    for _ in range(samples):
        total += read_adc(ch)
        time.sleep(0.003)
    return total / samples


def calibrate_baselines():
    print(f"Calibrating for {CALIBRATION_SECONDS} seconds...")
    print("Make sure NO object is in front of the sensors during calibration.")

    sums = [0.0, 0.0, 0.0, 0.0]
    counts = [0, 0, 0, 0]
    end_time = time.time() + CALIBRATION_SECONDS

    while time.time() < end_time:
        for ch in range(4):
            val = read_adc_avg(ch)
            sums[ch] += val
            counts[ch] += 1
        time.sleep(0.02)

    return [round(sums[i] / counts[i], 1) for i in range(4)]


def save_trigger(compartment_id, ts):
    global db_cursor

    if db_cursor is None:
        return

    try:
        sql_status = """
            INSERT INTO ir_sensor_status (compartment_id, beam_broken, last_changed)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                beam_broken = VALUES(beam_broken),
                last_changed = VALUES(last_changed)
        """
        db_cursor.execute(sql_status, (compartment_id, 1, ts))

        sql_event = """
            INSERT INTO ir_sensor_events (compartment_id, beam_broken, event_time)
            VALUES (%s, %s, %s)
        """
        db_cursor.execute(sql_event, (compartment_id, 1, ts))

        print(f"  -> Bin {compartment_id} event saved to MySQL")
    except Exception as e:
        print(f"MySQL trigger write failed for bin {compartment_id}: {e}")


def save_reset(compartment_id, ts):
    global db_cursor

    if db_cursor is None:
        return

    try:
        sql_status_reset = """
            INSERT INTO ir_sensor_status (compartment_id, beam_broken, last_changed)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                beam_broken = VALUES(beam_broken),
                last_changed = VALUES(last_changed)
        """
        db_cursor.execute(sql_status_reset, (compartment_id, 0, ts))
        print(f"  -> Bin {compartment_id} reset saved to MySQL")
    except Exception as e:
        print(f"MySQL reset write failed for bin {compartment_id}: {e}")


connect_db()

BASELINES = calibrate_baselines()
TRIGGER_LEVELS = [BASELINES[i] + TRIGGER_MARGINS[i] for i in range(4)]
RESET_LEVELS = [BASELINES[i] + RESET_MARGINS[i] for i in range(4)]

last_trigger = [0, 0, 0, 0]
armed = [True, True, True, True]
hit_count = [0, 0, 0, 0]

print("\n4-Compartment Trash Drop Detector")
print("CHANNEL_TO_BIN:", CHANNEL_TO_BIN)
print("BASELINES:", BASELINES)
print("TRIGGER_LEVELS:", TRIGGER_LEVELS)
print("RESET_LEVELS:", RESET_LEVELS)
print("Ch | Bin | Raw | Hits | Armed | Time")
print("-" * 55)

try:
    while True:
        now = time.time()
        ensure_db()

        for ch in range(4):
            adc = read_adc_avg(ch)
            compartment_id = CHANNEL_TO_BIN[ch]

            if armed[ch]:
                if adc > TRIGGER_LEVELS[ch] and (now - last_trigger[ch]) > DEBOUNCE_S:
                    hit_count[ch] += 1
                else:
		     hit_count[ch] = 0

                print(
                    f"{ch+1}  | {compartment_id}   | {adc:6.1f} | {hit_count[ch]:4d} | True  | {datetime.now().strftime('%H:%M:%S')}"
                )

                if hit_count[ch] >= CONFIRM_READS[ch]:
                    ts = datetime.now()
                    print(f"*** BIN {compartment_id} TRIGGERED (channel {ch+1}) at {ts.strftime('%H:%M:%S')} ***")
                    last_trigger[ch] = now
                    armed[ch] = False
                    hit_count[ch] = 0
                    save_trigger(compartment_id, ts)

            else:
                print(
                    f"{ch+1}  | {compartment_id}   | {adc:6.1f} | {hit_count[ch]:4d} | False | {datetime.now().strftime('%H:%M:%S')}"
                )

                if adc < RESET_LEVELS[ch]:
                    ts = datetime.now()
                    print(f"*** BIN {compartment_id} RESET (channel {ch+1}) at {ts.strftime('%H:%M:%S')} ***")
                    armed[ch] = True
                    hit_count[ch] = 0
                    save_reset(compartment_id, ts)

        time.sleep(IR_LOOP_DELAY)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    try:
        if db_cursor is not None:
            db_cursor.close()
    except Exception:
        pass

    try:
        if db_conn is not None and db_conn.is_connected():
            db_conn.close()
    except Exception:
        pass

    spi.close()
    print("IR sensor cleanup complete.")
