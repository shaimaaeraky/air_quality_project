import serial
import asyncio
import json
import re
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

# --- PROJECT CREDENTIALS ---
DEVICE_ID = "1llitybde5a"
HUB_URL = "iotc-dccced73-b234-4baa-912e-9cab01814f4e.azure-devices.net"
PRIMARY_KEY = "KEG2K9CkgXwBiX1xvtx5d66vuZmtsedrtrbIH7J88K4="
CONNECTION_STRING = f"HostName={HUB_URL};DeviceId={DEVICE_ID};SharedAccessKey={PRIMARY_KEY}"
SERIAL_PORT = 'COM5'

async def run_gateway():
    print(f"--- Starting Device: {DEVICE_ID} ---")

    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    await client.connect()
    print(f"Connected to Hub: {HUB_URL}")
    packet_count = 0

    try:
        with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
            print(f"Serial port {SERIAL_PORT} opened successfully")
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"DEBUG: Raw data from sensor: '{line}'")

                    try:
                        # Try JSON first
                        try:
                            data = json.loads(line)
                            aqi_val = data.get("AQI", 0) if isinstance(data, dict) else float(data)

                        except (json.JSONDecodeError, ValueError):
                            # Extract number from string like "AQI Value: 45"
                            match = re.search(r'[\d.]+', line)
                            if match:
                                aqi_val = float(match.group())
                            else:
                                print(f"[{timestamp}] Could not extract number from: '{line}'")
                                continue

                        telemetry_payload = {"AQI": aqi_val}
                        msg = Message(json.dumps(telemetry_payload))
                        msg.content_encoding = "utf-8"
                        msg.content_type = "application/json"
                        await client.send_message(msg)

                        packet_count += 1
                        print(f"[{timestamp}] Packet {packet_count} Sent: {telemetry_payload}")

                    except Exception as e:
                        print(f"[{timestamp}]  Error processing '{line}': {e}")

                await asyncio.sleep(0.1)

    except serial.SerialException as e:
        print(f" Serial port error: {e}")
    except Exception as e:
        print(f" Critical Error: {e}")
    finally:
        await client.shutdown()

if __name__ == "__main__":
    asyncio.run(run_gateway())
