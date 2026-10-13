-- IoT Smart Waste Management System - Database Schema
-- Database: waste_management

CREATE DATABASE IF NOT EXISTS waste_management;
USE waste_management;

-- 1. Ultrasonic Sensor Depth & Fill Readings
CREATE TABLE IF NOT EXISTS ultrasonic_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT NOT NULL,
    distance_cm DECIMAL(6, 2) NOT NULL,
    fill_percent DECIMAL(5, 2) NOT NULL,
    reading_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bin_time (bin_id, reading_time)
);

-- 2. IR Break-Beam Trash Drop Events
CREATE TABLE IF NOT EXISTS ir_sensor_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    compartment_id INT NOT NULL,
    beam_broken TINYINT(1) DEFAULT 1,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_compartment_time (compartment_id, event_time)
);

-- 3. Live IR Sensor Status per Compartment
CREATE TABLE IF NOT EXISTS ir_sensor_status (
    compartment_id INT PRIMARY KEY,
    beam_broken TINYINT(1) DEFAULT 0,
    last_changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. SMTP / SMS Alert Notification Contacts
CREATE TABLE IF NOT EXISTS smtp_contacts (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NULL,
    phone_number VARCHAR(20) NULL,
    carrier_gateway VARCHAR(100) NULL,
    is_active TINYINT(1) DEFAULT 1,
    alert_threshold_min DECIMAL(5, 2) DEFAULT 80.00,
    alert_threshold_max DECIMAL(5, 2) DEFAULT 100.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Administrative Dashboard User Accounts
CREATE TABLE IF NOT EXISTS Admins (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash CHAR(64) NOT NULL, -- SHA-256 hash
    LastLogin TIMESTAMP NULL DEFAULT NULL
);
