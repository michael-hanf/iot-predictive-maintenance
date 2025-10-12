from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow import keras
import numpy as np
import joblib
import os

app = Flask(__name__)
CORS(app)

# Load model and scaler
model_path = os.path.join(os.path.dirname(__file__), 'models', 'predictive_model.h5')
scaler_path = os.path.join(os.path.dirname(__file__), 'models', 'scaler.pkl')

model = keras.models.load_model(model_path)
scaler = joblib.load(scaler_path)

# Buffer für RAW values (nicht scaled!)
buffer = []

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model_loaded': True})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    # RAW values (BEFORE scaling)
    reading = [
        data['temperature'], 
        data['vibration'], 
        data['pressure']
    ]
    
    # Add RAW to buffer
    buffer.append(reading)
    if len(buffer) > 50:
        buffer.pop(0)
    
    # Need 50 readings for LSTM
    if len(buffer) < 50:
        return jsonify({
            'prediction': 0.0,
            'risk_level': 'initializing',
            'buffer_size': len(buffer),
            'message': f'Collecting data... {len(buffer)}/50'
        })
    
    # Scale for ML model
    scaled = scaler.transform(buffer)
    X = np.array([scaled])
    ml_prediction = float(model.predict(X, verbose=0)[0][0])
    
    # Rule-based on RAW values (not scaled!)
    latest_raw = buffer[-1]
    temp_critical = latest_raw[0] > 85
    vib_critical = latest_raw[1] > 1.0
    pressure_critical = latest_raw[2] < 70 or latest_raw[2] > 120
    
    rule_based_risk = 0.9 if (temp_critical or vib_critical or pressure_critical) else 0.0
    
    # Combine: Max of ML and Rules
    final_prediction = max(ml_prediction, rule_based_risk)
    
    # Risk level
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
    print("Ready to predict!")
    app.run(host='0.0.0.0', port=5000, debug=False)