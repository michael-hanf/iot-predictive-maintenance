FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator code
COPY simulator/sensor_simulator.py .

# Run the simulator with unbuffered output
CMD ["python", "-u", "sensor_simulator.py"]
