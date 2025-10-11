import numpy as np
import pandas as pd
from tensorflow import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

def create_sequences(data, seq_length=50):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        # Predict if failure in next 10 readings (1=failure, 0=normal)
        y.append(1 if data[i+seq_length, 0] > 85 else 0)
    return np.array(X), np.array(y)

def generate_training_data():
    data = []
    scenarios = []  # Track welches Szenario
    
    for cycle in range(20):  # 20 Zyklen
        scenario = np.random.choice(['normal', 'gradual', 'temp_spike', 
                                     'vib_spike', 'pressure_drop', 'multi'])
        
        if scenario == 'normal':
            # 200 readings normal operation
            for i in range(200):
                temp = 70 + np.random.uniform(-3, 3)
                vibration = 0.5 + np.random.uniform(-0.1, 0.1)
                pressure = 100 + np.random.uniform(-5, 5)
                data.append([temp, vibration, pressure])
                scenarios.append('normal')
        
        elif scenario == 'gradual':
            # 150 readings mit gradueller Degradation
            for i in range(150):
                degradation = i / 150  # 0 → 1
                temp = 70 + degradation * 20 + np.random.uniform(-2, 2)
                vibration = 0.5 + degradation * 0.6 + np.random.uniform(-0.1, 0.1)
                pressure = 100 + np.random.uniform(-5, 5)
                data.append([temp, vibration, pressure])
                scenarios.append('failure' if i > 120 else 'warning')
        
        elif scenario == 'temp_spike':
            # Normal dann plötzlicher Temp-Anstieg
            for i in range(100):
                if i < 80:
                    temp = 70 + np.random.uniform(-2, 2)
                else:
                    temp = 70 + (i-80) * 1.2 + np.random.uniform(0, 5)
                vibration = 0.5 + np.random.uniform(-0.1, 0.1)
                pressure = 100 + np.random.uniform(-5, 5)
                data.append([temp, vibration, pressure])
                scenarios.append('failure' if i > 85 else 'normal')
        
        elif scenario == 'vib_spike':
            # Plötzlicher Vibrations-Anstieg
            for i in range(100):
                temp = 70 + np.random.uniform(-2, 2)
                if i < 80:
                    vibration = 0.5 + np.random.uniform(-0.1, 0.1)
                else:
                    vibration = 0.5 + (i-80) * 0.03 + np.random.uniform(0, 0.2)
                pressure = 100 + np.random.uniform(-5, 5)
                data.append([temp, vibration, pressure])
                scenarios.append('failure' if i > 85 else 'normal')
        
        elif scenario == 'pressure_drop':
            # Druckabfall
            for i in range(100):
                temp = 70 + np.random.uniform(-2, 2)
                vibration = 0.5 + np.random.uniform(-0.1, 0.1)
                if i < 80:
                    pressure = 100 + np.random.uniform(-5, 5)
                else:
                    pressure = 100 - (i-80) * 2 + np.random.uniform(-3, 3)
                data.append([temp, vibration, pressure])
                scenarios.append('failure' if i > 85 else 'normal')
        
        elif scenario == 'multi':
            # Multi-Failure
            for i in range(100):
                if i < 70:
                    temp = 70 + np.random.uniform(-2, 2)
                    vibration = 0.5 + np.random.uniform(-0.1, 0.1)
                    pressure = 100 + np.random.uniform(-5, 5)
                else:
                    degradation = (i-70) / 30
                    temp = 70 + degradation * 25 + np.random.uniform(-1, 3)
                    vibration = 0.5 + degradation * 0.8 + np.random.uniform(-0.05, 0.15)
                    pressure = 100 + degradation * 20 + np.random.uniform(-3, 3)
                data.append([temp, vibration, pressure])
                scenarios.append('failure' if i > 85 else 'warning' if i > 75 else 'normal')
    
    return np.array(data), scenarios

def create_sequences(data, scenarios, seq_length=50):
    X, y = [], []
    
    for i in range(len(data) - seq_length - 10):
        X.append(data[i:i+seq_length])
        
        # Check nächste 10 readings
        future_scenarios = scenarios[i+seq_length:i+seq_length+10]
        
        # Label = 1 wenn irgendein "failure" in nächsten 10
        has_failure = any(s == 'failure' for s in future_scenarios)
        
        y.append(1 if has_failure else 0)
    
    return np.array(X), np.array(y)

def generate_training_data_old():
    data = []
    degradation = 0
    
    for i in range(10000):
        # Base values
        temp = 70 + degradation * 0.5 + np.random.uniform(-2, 2)
        vibration = 0.5 + degradation * 0.1 + np.random.uniform(-0.1, 0.1)
        pressure = 100 + np.random.uniform(-5, 5)
        
        # PATTERN 1: Gradual degradation (langsam alles steigt)
        if degradation > 50:
            temp += np.random.uniform(0, 10)
            vibration += np.random.uniform(0, 0.3)
        
        # PATTERN 2: Sudden temp spike (Kühlsystem-Ausfall)
        if i % 1500 == 0 and i > 0:
            temp += np.random.uniform(15, 25)  # Plötzlicher Anstieg!
        
        # PATTERN 3: Vibration spike only (Lager-Problem)
        if i % 2000 == 0 and i > 0:
            vibration += np.random.uniform(0.5, 1.0)  # Nur Vibration!
        
        # PATTERN 4: Pressure drop (Leck)
        if i % 2500 == 0 and i > 0:
            pressure -= np.random.uniform(20, 40)  # Druckabfall
        
        # PATTERN 5: Kombiniert (mehrere Werte gleichzeitig)
        if i % 3000 == 0 and i > 0:
            temp += np.random.uniform(10, 15)
            vibration += np.random.uniform(0.3, 0.6)
            pressure += np.random.uniform(10, 20)
        
        data.append([temp, vibration, pressure])
        
        degradation += 0.5
        if degradation > 100:
            degradation = 0
            
    return np.array(data)

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Generate data
print("Generating training data...")
raw_data, scenarios = generate_training_data()

# Scale
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(raw_data)

# Create sequences
X, y = create_sequences(scaled_data, scenarios, seq_length=50)

print(f"Data shape: {X.shape}")
print(f"Labels distribution: {np.sum(y)}/{len(y)} failures ({np.mean(y)*100:.1f}%)")

# Split
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

# Build model
model = Sequential([
    LSTM(64, activation='relu', input_shape=(50, 3), return_sequences=True),
    Dropout(0.2),
    LSTM(32, activation='relu'),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train
print("Training model...")
history = model.fit(
    X_train, y_train,
    epochs=20,
    batch_size=32,
    validation_data=(X_test, y_test),
    verbose=1
)

# Save
model.save('models/predictive_model.h5')
joblib.dump(scaler, 'models/scaler.pkl')
print("Model saved!")

# Evaluate
loss, acc = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {acc:.4f}")

