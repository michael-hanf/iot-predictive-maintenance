import numpy as np
from tensorflow import keras
import joblib

# Load model & scaler
model = keras.models.load_model('models/predictive_model.h5')
scaler = joblib.load('models/scaler.pkl')

print("=" * 60)
print("TESTING MODEL PREDICTIONS")
print("=" * 60)

# Test 1: Normal sequence (50 readings)
print("\n1. NORMAL SEQUENCE (all normal values)")
normal_seq = np.array([[70, 0.5, 100] for _ in range(50)])
scaled_normal = scaler.transform(normal_seq)
pred_normal = model.predict(scaled_normal.reshape(1, 50, 3), verbose=0)
print(f"   Prediction: {pred_normal[0][0]:.4f}")
print(f"   Expected: <0.2 (low risk)")

# Test 2: Critical sequence (50 readings - all critical)
print("\n2. CRITICAL SEQUENCE (all critical values)")
critical_seq = np.array([[92, 1.3, 115] for _ in range(50)])
scaled_critical = scaler.transform(critical_seq)
pred_critical = model.predict(scaled_critical.reshape(1, 50, 3), verbose=0)
print(f"   Prediction: {pred_critical[0][0]:.4f}")
print(f"   Expected: >0.8 (high risk)")

# Test 3: Gradual increase (50 readings - degrading over time)
print("\n3. GRADUAL DEGRADATION (slow increase)")
gradual_seq = np.array([
    [70 + i*0.5, 0.5 + i*0.015, 100 + i*0.3] 
    for i in range(50)
])
scaled_gradual = scaler.transform(gradual_seq)
pred_gradual = model.predict(scaled_gradual.reshape(1, 50, 3), verbose=0)
print(f"   Prediction: {pred_gradual[0][0]:.4f}")
print(f"   Expected: 0.5-0.8 (warning/high risk)")
print(f"   Start values: Temp={gradual_seq[0]}, End values: Temp={gradual_seq[-1]}")

# Test 4: Sudden spike (normal then spike)
print("\n4. SUDDEN SPIKE (40 normal, then 10 critical)")
spike_seq = np.array(
    [[70, 0.5, 100] for _ in range(40)] +
    [[92, 1.3, 115] for _ in range(10)]
)
scaled_spike = scaler.transform(spike_seq)
pred_spike = model.predict(scaled_spike.reshape(1, 50, 3), verbose=0)
print(f"   Prediction: {pred_spike[0][0]:.4f}")
print(f"   Expected: >0.7 (should detect spike)")

print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)

if pred_normal[0][0] < 0.2 and pred_critical[0][0] > 0.8:
    print("✅ Model works well! Can distinguish normal vs critical")
elif pred_normal[0][0] > 0.5 or pred_critical[0][0] < 0.5:
    print("❌ Model not learning properly - predictions too similar")
    print("   → Need better training data or different architecture")
else:
    print("⚠️  Model partially working - may need tuning")