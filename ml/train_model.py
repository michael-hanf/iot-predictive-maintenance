import numpy as np
import pandas as pd
from tensorflow import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

def generate_training_data():
    """Generate realistic sensor data with clear failure patterns"""
    data = []
    labels = []
    
    # Generate 100 cycles für mehr Daten
    for cycle in range(100):
        scenario = np.random.choice([
            'normal', 'normal', 'normal', 'normal',  # 4x
            'gradual', 'temp_spike', 'extreme'  # 3x
        ])
        if scenario == 'normal':
            # 150 readings normale Operation
            for i in range(150):
                temp = np.random.normal(70, 2)
                vibration = np.random.normal(0.5, 0.08)
                pressure = np.random.normal(100, 3)
                
                data.append([temp, vibration, pressure])
                labels.append(0)
        
        elif scenario == 'gradual':
            # 120 readings mit Degradation bis 100°C
            for i in range(120):
                progress = i / 120
                
                # Erweitert bis 100°C, Vib bis 2.0
                temp = 70 + progress * 30 + np.random.normal(0, 1.5)
                vibration = 0.5 + progress * 1.5 + np.random.normal(0, 0.06)
                pressure = 100 + np.random.normal(0, 3)
                
                data.append([temp, vibration, pressure])
                labels.append(1 if progress > 0.85 else 0) 
        
        elif scenario == 'temp_spike':
            # Plötzlicher Temperatur-Anstieg
            spike_point = 80
            for i in range(100):
                if i < spike_point:
                    temp = np.random.normal(70, 2)
                    vibration = np.random.normal(0.5, 0.08)
                else:
                    temp = 70 + (i - spike_point) * 1.5 + np.random.normal(0, 2)
                    vibration = np.random.normal(0.5, 0.08)
                
                pressure = np.random.normal(100, 3)
                data.append([temp, vibration, pressure])
                labels.append(1 if i >= spike_point + 5 else 0)
        
        elif scenario == 'vib_spike':
            # Plötzlicher Vibrations-Anstieg
            spike_point = 80
            for i in range(100):
                temp = np.random.normal(70, 2)
                
                if i < spike_point:
                    vibration = np.random.normal(0.5, 0.08)
                else:
                    vibration = 0.5 + (i - spike_point) * 0.04 + np.random.normal(0, 0.1)
                
                pressure = np.random.normal(100, 3)
                data.append([temp, vibration, pressure])
                labels.append(1 if i >= spike_point + 5 else 0)
        
        elif scenario == 'pressure_drop':
            # Druckabfall
            drop_point = 80
            for i in range(100):
                temp = np.random.normal(70, 2)
                vibration = np.random.normal(0.5, 0.08)
                
                if i < drop_point:
                    pressure = np.random.normal(100, 3)
                else:
                    pressure = 100 - (i - drop_point) * 2 + np.random.normal(0, 2)
                
                data.append([temp, vibration, pressure])
                labels.append(1 if i >= drop_point + 5 else 0)
        
        elif scenario == 'multi':
            # Multi-Failure
            fail_point = 70
            for i in range(100):
                if i < fail_point:
                    temp = np.random.normal(70, 2)
                    vibration = np.random.normal(0.5, 0.08)
                    pressure = np.random.normal(100, 3)
                else:
                    progress = (i - fail_point) / 30
                    temp = 70 + progress * 28 + np.random.normal(0, 2)
                    vibration = 0.5 + progress * 0.9 + np.random.normal(0, 0.1)
                    pressure = 100 + progress * 25 + np.random.normal(0, 3)
                
                data.append([temp, vibration, pressure])
                labels.append(1 if i >= fail_point + 10 else 0)
        
        elif scenario == 'extreme':
            # Hardware-Failure: Sehr hohe Werte
            spike_point = 80
            for i in range(100):
                if i < spike_point:
                    temp = np.random.normal(70, 2)
                    vibration = np.random.normal(0.5, 0.08)
                else:
                    # EXTREME values
                    temp = 85 + (i - spike_point) * 1.2 + np.random.normal(0, 2)
                    vibration = 0.5 + (i - spike_point) * 0.12 + np.random.normal(0, 0.1)
                
                pressure = np.random.normal(100, 3)
                data.append([temp, vibration, pressure])
                labels.append(1 if i >= spike_point + 3 else 0)
    
    return np.array(data), np.array(labels)

def create_sequences(data, labels, seq_length=50):
    """Create sequences for LSTM"""
    X, y = [], []
    
    for i in range(len(data) - seq_length - 10):
        X.append(data[i:i+seq_length])
        
        # Label: ANY failure in next 10 readings?
        future_labels = labels[i+seq_length:i+seq_length+10]
        y.append(1 if np.any(future_labels == 1) else 0)
    
    return np.array(X), np.array(y)

# Create models directory
os.makedirs('models', exist_ok=True)

print("=" * 60)
print("GENERATING TRAINING DATA")
print("=" * 60)

raw_data, raw_labels = generate_training_data()

print(f"Total data points: {len(raw_data)}")
print(f"Failure samples: {np.sum(raw_labels)} ({np.mean(raw_labels)*100:.1f}%)")

# Scale data
print("\nScaling data...")
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(raw_data)

# Create sequences
print("Creating sequences...")
X, y = create_sequences(scaled_data, raw_labels, seq_length=50)

print(f"Sequence samples: {len(X)}")
print(f"Failure sequences: {np.sum(y)} ({np.mean(y)*100:.1f}%)")

# Split train/test
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

print(f"\nTraining samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")

print("\n" + "=" * 60)
print("BUILDING MODEL")
print("=" * 60)

# Model
model = Sequential([
    LSTM(128, activation='relu', input_shape=(50, 3), return_sequences=True),
    Dropout(0.3),
    LSTM(64, activation='relu', return_sequences=True),
    Dropout(0.3),
    LSTM(32, activation='relu'),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
)

print(model.summary())

print("\n" + "=" * 60)
print("TRAINING MODEL")
print("=" * 60)

# Train with callbacks
history = model.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_data=(X_test, y_test),
    verbose=1,
    callbacks=[
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            verbose=1,
            min_lr=0.00001
        )
    ]
)

print("\n" + "=" * 60)
print("EVALUATING MODEL")
print("=" * 60)

# Evaluate
results = model.evaluate(X_test, y_test, verbose=0)
print(f"Test Loss: {results[0]:.4f}")
print(f"Test Accuracy: {results[1]:.4f}")
print(f"Test Precision: {results[2]:.4f}")
print(f"Test Recall: {results[3]:.4f}")

# Save
print("\n" + "=" * 60)
print("SAVING MODEL")
print("=" * 60)

model.save('models/predictive_model.h5')
joblib.dump(scaler, 'models/scaler.pkl')

print("✅ Model saved to models/predictive_model.h5")
print("✅ Scaler saved to models/scaler.pkl")

print("\n" + "=" * 60)
print("TRAINING COMPLETE!")
print("=" * 60)