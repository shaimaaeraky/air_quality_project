import serial
import asyncio
import json
import re
import base64
import hmac
import hashlib
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

# ✅ CORRECT FULL KEYS
ID_SCOPE    = "0ne0116EEA3"
DEVICE_ID   = "mq135"
GROUP_KEY   = "is8CGAJY9+BPY0IB8V7SYATyc28144fMxZMfL3CVx4F2mr7ktu31Nlwy3czGnHDgHGTFL2IOya6WAIoT8yZ0Kg=="

DPS_HOST    = "global.azure-devices-provisioning.net"
SERIAL_PORT = 'COM5'

def derive_device_key(group_key: str, device_id: str) -> str:
    secret  = base64.b64decode(group_key)
    derived = hmac.new(secret, device_id.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(derived).decode("utf-8")

async def run_gateway():
    print(f"--- Starting Device: {DEVICE_ID} ---")

    device_key = derive_device_key(GROUP_KEY, DEVICE_ID)
    print(f"Derived key OK: {device_key[:20]}...")

    provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host=DPS_HOST,
        registration_id=DEVICE_ID,
        id_scope=ID_SCOPE,
        symmetric_key=device_key,
    )

    print("Provisioning via DPS...")
    result = await provisioning_client.register()

    if result.status != "assigned":
        raise RuntimeError(f"Provisioning failed: {result.status}")

    hub = result.registration_state.assigned_hub
    print(f"✅ Assigned Hub: {hub}")

    conn_str = f"HostName={hub};DeviceId={DEVICE_ID};SharedAccessKey={device_key}"
    client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await client.connect()
    print("✅ Connected! Listening for sensor data...\n")

    packet_count = 0
    try:
        with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if not line:
                        continue
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    try:
                        try:
                            data = json.loads(line)
                            aqi_val = data.get("AQI", 0) if isinstance(data, dict) else float(data)
                        except (json.JSONDecodeError, ValueError):
                            match = re.search(r'[\d.]+', line)
                            aqi_val = float(match.group()) if match else None

                        if aqi_val is None:
                            print(f"[{timestamp}] Could not parse: '{line}'")
                            continue

                        payload = {"AQI": aqi_val}
                        msg = Message(json.dumps(payload))
                        msg.content_encoding = "utf-8"
                        msg.content_type = "application/json"
                        await client.send_message(msg)
                        packet_count += 1
                        print(f"[{timestamp}] ✅ Sent #{packet_count}: {payload}")

                    except Exception as e:
                        print(f"[{timestamp}] Error: {e}")
                await asyncio.sleep(0.1)

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    finally:
        await client.shutdown()

if __name__ == "__main__":
    asyncio.run(run_gateway())
