#!/usr/bin/env python3
import os
import sys
import time
import logging
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Any

import mysql.connector
from mysql.connector import Error

import config

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_gmail_app_password")
SMTP_FROM = SMTP_USER
DEFAULT_THRESHOLD = 80.0
CHECK_INTERVAL_SECONDS = 300

DB_CONFIG = {
    "host": config.DB_HOST,
    "port": config.DB_PORT,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
    "database": config.DB_NAME,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

CARRIER_GATEWAYS = {
    "att": "txt.att.net",
    "at&t": "txt.att.net",
    "verizon": "vtext.com",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "uscellular": "email.uscc.net",
    "xfinity": "vtext.com",
}

EMAIL_ONLY_MARKERS = {
    "att", "at&t", "cricket",
    "txt.att.net", "mms.att.net", "sms.cricketwireless.net"
}

def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        autocommit=True
    )

def normalize_gateway(phone_number: str, carrier_gateway: str) -> str:
    if not phone_number or not carrier_gateway:
        return ""
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    domain = carrier_gateway.strip().lower()
    domain = CARRIER_GATEWAYS.get(domain, domain)
    if "@" in domain:
        return domain
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if not digits:
        return ""
    return f"{digits}@{domain}"

def is_email_only_carrier(carrier_gateway: str) -> bool:
    value = (carrier_gateway or "").strip().lower()
    return value in EMAIL_ONLY_MARKERS

def get_latest_bin_fill(cursor) -> List[Dict[str, Any]]:
    query = """
        SELECT
            id,
            bin_id,
            distance_cm,
            fill_percent,
            reading_time
        FROM ultrasonic_readings
        WHERE id IN (
            SELECT MAX(id)
            FROM ultrasonic_readings
            GROUP BY bin_id
        )
        ORDER BY bin_id
    """
    cursor.execute(query)
    return cursor.fetchall()

def get_matching_contacts(cursor, fill_percent: float) -> List[Dict[str, Any]]:
    query = """
        SELECT
            contact_id,
            name,
            email,
            phone_number,
            carrier_gateway,
            COALESCE(alert_threshold_min, %s) AS threshold_min,
            COALESCE(alert_threshold_max, 100) AS threshold_max
        FROM smtp_contacts
        WHERE is_active = 1
          AND %s BETWEEN COALESCE(alert_threshold_min, %s)
                      AND COALESCE(alert_threshold_max, 100)
    """
    cursor.execute(query, (DEFAULT_THRESHOLD, fill_percent, DEFAULT_THRESHOLD))
    return cursor.fetchall()

def send_single(recipient: str, subject: str, body: str):
    if not recipient:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = recipient
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)

def run_check_cycle():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

        readings = get_latest_bin_fill(cursor)
        if not readings:
            logger.info("No ultrasonic readings found.")
            return

        for reading in readings:
            row_id = int(reading["id"])
            bin_id = int(reading["bin_id"])
            distance_cm_raw = reading.get("distance_cm")
            fill_percent_raw = reading.get("fill_percent")
            reading_time = reading.get("reading_time")

            distance_cm = float(distance_cm_raw) if distance_cm_raw is not None else 0.0
            fill_percent = float(fill_percent_raw) if fill_percent_raw is not None else 0.0

            logger.info(
                "Row %s | Bin %s → %.1f cm | %.1f%% fill | %s",
                row_id, bin_id, distance_cm, fill_percent, reading_time
            )

            if fill_percent < DEFAULT_THRESHOLD:
                logger.info("Bin %s below threshold (%.1f%%) — no alert.", bin_id, fill_percent)
                continue

            contacts = get_matching_contacts(cursor, fill_percent)
            if not contacts:
                logger.info(
                    "Bin %s at %.1f%% — no contacts matched threshold.",
                    bin_id, fill_percent
                )
                continue

            email_subject = f"ALERT: BIN {bin_id} IS AT THRESHOLD"
            email_body = (
                f"Bin: {bin_id}\n"
                f"Fill Percentage: {fill_percent:.1f}%\n"
                f"Reading Time: {reading_time}"
            )
            sms_body = (
                f"ALERT: BIN {bin_id} IS AT THRESHOLD | "
                f"{fill_percent:.1f}% | {reading_time}"
            )

            for contact in contacts:
                contact_id = contact.get("contact_id")
                email_addr = (contact.get("email") or "").strip()
                carrier = (contact.get("carrier_gateway") or "").strip().lower()
                sms_addr = normalize_gateway(
                    contact.get("phone_number") or "",
                    contact.get("carrier_gateway") or ""
                )

                logger.info(
                    "Contact %s | email=%s | carrier=%s | sms=%s",
                    contact_id,
                    email_addr or "<none>",
                    carrier or "<none>",
                    sms_addr or "<none>"
                )

                if is_email_only_carrier(carrier):
                    if email_addr:
                        try:
                            send_single(email_addr, email_subject, email_body)
                            logger.info("Email-only alert sent to contact %s (%s).", contact_id, email_addr)
                        except smtplib.SMTPException as err:
                            logger.error("Email-only send failed for contact %s (%s): %s", contact_id, email_addr, err)
                    else:
                        logger.warning("Contact %s requires email-only fallback but has no email.", contact_id)
                    continue

                sent_any = False

                if email_addr:
                    try:
                        send_single(email_addr, email_subject, email_body)
                        logger.info("Email sent to contact %s (%s).", contact_id, email_addr)
                        sent_any = True
                    except smtplib.SMTPException as err:
                        logger.error("Email failed for contact %s (%s): %s", contact_id, email_addr, err)

                if sms_addr:
                    try:
                        send_single(sms_addr, email_subject, sms_body)
                        logger.info("SMS gateway sent to contact %s (%s).", contact_id, sms_addr)
                        sent_any = True
                    except smtplib.SMTPException as err:
                        logger.error("SMS gateway failed for contact %s (%s): %s", contact_id, sms_addr, err)

                if not sent_any:
                    logger.warning("Contact %s had no working destinations.", contact_id)

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def main():
    if SMTP_PASSWORD == "PUT_NEW_APP_PASSWORD_HERE":
        logger.error("Set SMTP_PASSWORD in smtp.py before running.")
        sys.exit(1)

    logger.info("SMTP monitor started. Checking every %s seconds.", CHECK_INTERVAL_SECONDS)

    try:
        while True:
            try:
                run_check_cycle()
            except Error as err:
                logger.error("MySQL error: %s", err)
            except smtplib.SMTPException as err:
                logger.error("SMTP error: %s", err)
            except Exception as err:
                logger.exception("Unexpected error: %s", err)

            logger.info("Sleeping for %s seconds before next check.", CHECK_INTERVAL_SECONDS)
            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("SMTP monitor stopped by user.")

if __name__ == "__main__":
    main()
