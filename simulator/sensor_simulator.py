import paho.mqtt.client as mqtt
import json
import time
import random
import numpy as np
from datetime import datetime
import threading

class SensorSimulator:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_message = self.on_control_message
        self.client.connect(broker, port)
        self.client.loop_start()
        
        # Base values
        self.degradation = 0
        self.running = True
        
        # Control overrides (None = automatic)
        self.temp_override = None
        self.pressure_override = None
        self.vibration_override = None
        self.degradation_speed = 0.5  # Can be controlled
        
    def on_control_message(self, client, userdata, msg):
        """Handle control commands from MQTT"""
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
        """Reset to normal operation"""
        self.degradation = 0
        self.temp_override = None
        self.pressure_override = None
        self.vibration_override = None
        self.degradation_speed = 0.5
        print("Simulator reset to normal operation")
        
    def generate_sensor_data(self, machine_id):
        # Calculate base values with degradation
        base_temp = 70 + self.degradation * 0.5
        base_vibration = 0.5 + self.degradation * 0.1
        base_pressure = 100
        
        # Add noise
        temperature = base_temp + random.uniform(-2, 2)
        vibration = base_vibration + random.uniform(-0.1, 0.1)
        pressure = base_pressure + random.uniform(-5, 5)
        
        # Apply manual overrides if set
        if self.temp_override is not None:
            temperature = self.temp_override + random.uniform(-1, 1)
        if self.pressure_override is not None:
            pressure = self.pressure_override + random.uniform(-2, 2)
        if self.vibration_override is not None:
            vibration = self.vibration_override + random.uniform(-0.05, 0.05)
        
        # Simulate failure approaching (if in auto mode)
        if self.temp_override is None and self.degradation > 50:
            temperature += random.uniform(0, 10)
            vibration += random.uniform(0, 0.5)
        
        # Determine status
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
        # Subscribe to control topic
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
            
            # Increment degradation (unless overridden)
            if self.temp_override is None:
                self.degradation += self.degradation_speed
                if self.degradation > 100:
                    self.degradation = 0
                    
            time.sleep(interval)

if __name__ == "__main__":
    simulator = SensorSimulator()
    simulator.run()