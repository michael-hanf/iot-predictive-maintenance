from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow import keras
import numpy as np
import joblib
import os
import urllib.request
import sys

app = Flask(__name__)
CORS(app)

# Model and scaler paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
model_path = os.path.join(MODEL_DIR, 'predictive_model.h5')
scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')

# GitHub release URLs (adjust to your repo)
GITHUB_RELEASE_URL = 'https://github.com/michael-hanf/iot-predictive-maintenance/releases/download'
MODEL_DOWNLOAD_URL = f'{GITHUB_RELEASE_URL}/v0.1.0/predictive_model.h5'
SCALER_DOWNLOAD_URL = f'{GITHUB_RELEASE_URL}/v0.1.0/scaler.pkl'

def ensure_model_directory():
    """Create models directory if it doesn't exist"""
    os.makedirs(MODEL_DIR, exist_ok=True)

def download_file(url, destination):
    """Download a file from URL with progress reporting"""
    try:
        print(f"Downloading {os.path.basename(destination)}...")
        print(f"From: {url}")

        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 // total_size, 100)
            sys.stdout.write(f'\rDownload progress: {percent}%')
            sys.stdout.flush()

        urllib.request.urlretrieve(url, destination, reporthook=download_progress)
        print(f"\n✓ {os.path.basename(destination)} downloaded successfully")
        return True
    except Exception as e:
        print(f"\n✗ Error downloading {os.path.basename(destination)}: {e}")
        return False

def load_or_download_models():
    """Load models, download if necessary"""
    ensure_model_directory()

    # Check and download model
    if not os.path.exists(model_path):
        print("\n" + "="*60)
        print("ML Model not found locally")
        print("="*60)
        if not download_file(MODEL_DOWNLOAD_URL, model_path):
            raise RuntimeError("Failed to download model")
    else:
        print(f"✓ Model found at {model_path}")

    # Check and download scaler
    if not os.path.exists(scaler_path):
        print("\n" + "="*60)
        print("Scaler not found locally")
        print("="*60)
        if not download_file(SCALER_DOWNLOAD_URL, scaler_path):
            raise RuntimeError("Failed to download scaler")
    else:
        print(f"✓ Scaler found at {scaler_path}")

    # Load models
    print("\n" + "="*60)
    print("Loading models into memory...")
    print("="*60)
    try:
        model = keras.models.load_model(model_path)
        scaler = joblib.load(scaler_path)
        print("✓ Models loaded successfully")
        return model, scaler
    except Exception as e:
        print(f"✗ Error loading models: {e}")
        raise

# Load models on startup
model, scaler = load_or_download_models()

# Buffer for raw sensor values (not scaled for LSTM)
buffer = []

@app.route('/health', methods=['GET'])
def health():
    model_exists = os.path.exists(model_path)
    scaler_exists = os.path.exists(scaler_path)
    return jsonify({
        'status': 'healthy' if (model_exists and scaler_exists) else 'initializing',
        'model_loaded': model_exists,
        'scaler_loaded': scaler_exists,
        'buffer_size': len(buffer)
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    # Parse raw sensor values (before scaling)
    reading = [
        data['temperature'],
        data['vibration'],
        data['pressure']
    ]

    # Add reading to rolling buffer
    buffer.append(reading)
    if len(buffer) > 50:
        buffer.pop(0)

    # LSTM requires 50 readings for prediction
    if len(buffer) < 50:
        return jsonify({
            'prediction': 0.0,
            'risk_level': 'initializing',
            'buffer_size': len(buffer),
            'message': f'Collecting data... {len(buffer)}/50'
        })

    # Scale sensor values for LSTM model
    scaled = scaler.transform(buffer)
    X = np.array([scaled])
    ml_prediction = float(model.predict(X, verbose=0)[0][0])

    # Rule-based risk assessment on raw sensor values
    latest_raw = buffer[-1]
    temp_critical = latest_raw[0] > 85
    vib_critical = latest_raw[1] > 1.0
    pressure_critical = latest_raw[2] < 70 or latest_raw[2] > 120

    rule_based_risk = 0.9 if (temp_critical or vib_critical or pressure_critical) else 0.0

    # Hybrid approach: take maximum of ML and rule-based scores
    final_prediction = max(ml_prediction, rule_based_risk)
    
    # Classify risk level based on prediction score
    if final_prediction > 0.75:
        risk = "critical"
    elif final_prediction > 0.5:
        risk = "warning"
    else:
        risk = "normal"

    return jsonify({
        'prediction': final_prediction,
        'ml_prediction': ml_prediction,
        'rule_based': rule_based_risk,
        'risk_level': risk,
        'buffer_size': len(buffer),
        'confidence': final_prediction * 100
    })

@app.route('/reset', methods=['POST'])
def reset():
    global buffer
    buffer = []
    return jsonify({'status': 'buffer cleared'})

if __name__ == '__main__':
    print("ML Inference Service starting...")
    print(f"Model loaded: {model_path}")
    print("Ready to accept predictions!")
    app.run(host='0.0.0.0', port=5000, debug=False)