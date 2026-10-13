-- Useful Analytical & Maintenance Queries
USE waste_management;

-- 1. Pull the most recent ultrasonic fill reading for each compartment
SELECT 
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
ORDER BY bin_id;

-- 2. Total trash drop count per compartment
SELECT 
    compartment_id, 
    COUNT(*) AS total_drops
FROM ir_sensor_events
WHERE beam_broken = 1
GROUP BY compartment_id
ORDER BY compartment_id;

-- 3. Busiest hours of the day across all bins
SELECT 
    HOUR(event_time) AS hour_of_day, 
    COUNT(*) AS total_drops 
FROM ir_sensor_events 
GROUP BY HOUR(event_time) 
ORDER BY total_drops DESC;

-- 4. Activity trends by date
SELECT 
    DATE(event_time) AS event_date, 
    COUNT(*) AS total_drops 
FROM ir_sensor_events 
GROUP BY DATE(event_time) 
ORDER BY event_date;

-- 5. Insert a sample notification contact
INSERT INTO smtp_contacts 
    (name, email, phone_number, carrier_gateway, is_active, alert_threshold_min, alert_threshold_max)
VALUES 
    ('Maintenance Team', 'facilities@example.com', '5551234567', 'txt.att.net', 1, 80.00, 100.00);

-- 6. Insert sample administrator (Password: "AdminPassword123")
INSERT INTO Admins (Username, PasswordHash) 
VALUES ('admin_user', SHA2('AdminPassword123', 256));
