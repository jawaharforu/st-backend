-- Get device and farm IDs
DO $$
DECLARE
    v_device_id uuid;
    v_farm_id uuid;
BEGIN
    SELECT id, farm_id INTO v_device_id, v_farm_id FROM device LIMIT 1;
    
    -- Insert sample telemetry data with all new fields
    INSERT INTO telemetry (ts, device_id, farm_id, seq, temp_c, hum_pct, primary_heater, secondary_heater, exhaust_fan, sv_valve, fan, turning_motor, limit_switch, door_light, heater, rssi, ip) VALUES
    (NOW() - interval '10 minutes', v_device_id, v_farm_id, 1, 99.5, 65, true, false, false, true, true, false, false, true, true, -55, '192.168.1.101'),
    (NOW() - interval '9 minutes', v_device_id, v_farm_id, 2, 99.8, 66, true, true, false, true, true, false, false, true, true, -54, '192.168.1.101'),
    (NOW() - interval '8 minutes', v_device_id, v_farm_id, 3, 100.2, 64, false, true, true, false, true, true, false, true, false, -53, '192.168.1.101'),
    (NOW() - interval '7 minutes', v_device_id, v_farm_id, 4, 100.5, 63, false, false, true, false, true, true, true, false, false, -52, '192.168.1.101'),
    (NOW() - interval '6 minutes', v_device_id, v_farm_id, 5, 100.1, 65, true, false, false, true, true, false, false, true, true, -51, '192.168.1.101'),
    (NOW() - interval '5 minutes', v_device_id, v_farm_id, 6, 99.7, 66, true, true, false, true, false, false, false, true, true, -50, '192.168.1.101'),
    (NOW() - interval '4 minutes', v_device_id, v_farm_id, 7, 99.4, 67, false, true, true, false, false, true, false, false, false, -49, '192.168.1.101'),
    (NOW() - interval '3 minutes', v_device_id, v_farm_id, 8, 99.9, 64, true, false, true, true, true, true, false, true, true, -48, '192.168.1.101'),
    (NOW() - interval '2 minutes', v_device_id, v_farm_id, 9, 100.3, 63, false, true, false, true, true, false, true, true, false, -47, '192.168.1.101'),
    (NOW() - interval '1 minutes', v_device_id, v_farm_id, 10, 99.6, 65, true, false, false, false, true, false, false, true, true, -46, '192.168.1.101');
    
    RAISE NOTICE 'Inserted 10 telemetry records for device % in farm %', v_device_id, v_farm_id;
END $$;
