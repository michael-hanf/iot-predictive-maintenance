import paho.mqtt.client as mqtt
import json
import time
import random
import numpy as np
from datetime import datetime
import threading
import os

class SensorSimulator:
    def __init__(self, broker=None, port=None, max_retries=30, retry_delay=1):
        # Get broker from environment or use defaults
        if broker is None:
            broker = os.getenv("MQTT_BROKER", "localhost")
        if port is None:
            port = int(os.getenv("MQTT_PORT", "1883"))

        self.broker = broker
        self.port = port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_message = self.on_control_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        # Connect with retry logic
        self._connect_with_retry()
        self.client.loop_start()

        # Initial sensor values
        self.degradation = 0
        self.running = True

        # Control overrides (None = use automatic mode)
        self.temp_override = None
        self.pressure_override = None
        self.vibration_override = None
        self.degradation_speed = 0.5  # Degradation rate multiplier

    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker}:{self.port}")
        else:
            print(f"✗ Connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects from MQTT broker"""
        if rc != 0:
            print(f"✗ Unexpected disconnection (code {rc}), will attempt to reconnect...")

    def _connect_with_retry(self):
        """Connect to MQTT broker with exponential backoff retry logic"""
        retry_count = 0
        delay = self.retry_delay

        while retry_count < self.max_retries:
            try:
                print(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
                self.client.connect(self.broker, self.port, keepalive=60)
                print(f"✓ MQTT connection successful")
                return
            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    print(f"✗ Failed to connect after {self.max_retries} attempts")
                    raise RuntimeError(f"Could not connect to MQTT broker: {e}")

                print(f"⚠ Connection attempt {retry_count}/{self.max_retries} failed: {e}")
                print(f"  Retrying in {delay} seconds...")
                time.sleep(delay)
                # Exponential backoff: increase delay up to 5 seconds
                delay = min(delay * 1.5, 5.0)
        
    def on_control_message(self, client, userdata, msg):
        """Process control commands from MQTT"""
        try:
            control = json.loads(msg.payload)

            if "temperature" in control:
                self.temp_override = control["temperature"]
            if "pressure" in control:
                self.pressure_override = control["pressure"]
            if "vibration" in control:
                self.vibration_override = control["vibration"]
            if "degradation_speed" in control:
                self.degradation_speed = control["degradation_speed"]
            if "reset" in control and control["reset"]:
                self.reset()

            print(f"Control received: {control}")

        except Exception as e:
            print(f"Error parsing control: {e}")

    def reset(self):
        """Reset simulator to normal operation"""
        self.degradation = 0
        self.temp_override = None
        self.pressure_override = None
        self.vibration_override = None
        self.degradation_speed = 0.5
        print("Simulator reset to normal operation")
        
    def generate_sensor_data(self, machine_id):
        # Calculate base sensor values considering degradation
        base_temp = 70 + self.degradation * 0.5
        base_vibration = 0.5 + self.degradation * 0.1
        base_pressure = 100

        # Add realistic noise to sensor readings
        temperature = base_temp + random.uniform(-2, 2)
        vibration = base_vibration + random.uniform(-0.1, 0.1)
        pressure = base_pressure + random.uniform(-5, 5)

        # Apply manual sensor overrides if set
        if self.temp_override is not None:
            temperature = self.temp_override + random.uniform(-1, 1)
        if self.pressure_override is not None:
            pressure = self.pressure_override + random.uniform(-2, 2)
        if self.vibration_override is not None:
            vibration = self.vibration_override + random.uniform(-0.05, 0.05)

        # Simulate failure approaching in auto-degradation mode
        if self.temp_override is None and self.degradation > 50:
            temperature += random.uniform(0, 10)
            vibration += random.uniform(0, 0.5)

        # Determine machine status based on thresholds
        status = "normal"
        if temperature > 85 or vibration > 1.0:
            status = "critical"
        elif temperature > 80 or vibration > 0.8:
            status = "warning"
            
        return {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            "temperature": round(temperature, 2),
            "vibration": round(vibration, 3),
            "pressure": round(pressure, 2),
            "status": status,
            "degradation": round(self.degradation, 1),
            "mode": "manual" if any([self.temp_override, self.pressure_override, 
                                     self.vibration_override]) else "auto"
        }
    
    def run(self, machine_id="machine_001", interval=2):
        # Subscribe to control commands for this machine
        control_topic = f"control/{machine_id}"
        self.client.subscribe(control_topic)
        print(f"Starting simulator for {machine_id}")
        print(f"Listening for controls on: {control_topic}")

        while self.running:
            data = self.generate_sensor_data(machine_id)
            topic = f"sensors/{machine_id}/data"

            self.client.publish(topic, json.dumps(data))
            print(f"Published: Temp={data['temperature']}°C, "
                  f"Vib={data['vibration']}, Mode={data['mode']}")

            # Increase degradation over time (unless in manual override mode)
            if self.temp_override is None:
                self.degradation += self.degradation_speed
                if self.degradation > 100:
                    self.degradation = 0

            time.sleep(interval)

if __name__ == "__main__":
    machine_id = os.getenv("MACHINE_ID", "machine_001")
    simulator = SensorSimulator()
    simulator.run(machine_id=machine_id)