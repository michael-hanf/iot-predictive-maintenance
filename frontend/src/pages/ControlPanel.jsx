import { useState, useEffect } from 'react';

function ControlPanel() {
  const [mqttConnected, setMqttConnected] = useState(false);
  
  // Control values
  const [temperature, setTemperature] = useState(70);
  const [pressure, setPressure] = useState(100);
  const [vibration, setVibration] = useState(0.5);
  const [degradationSpeed, setDegradationSpeed] = useState(0.5);
  const [autoMode, setAutoMode] = useState(true);

  useEffect(() => {
    // Check if MQTT broker is accessible
    // For now just assume it's connected if backend is running
    fetch('http://localhost:8080/api/health')
      .then(() => setMqttConnected(true))
      .catch(() => setMqttConnected(false));
  }, []);

  const sendControl = () => {
    const control = autoMode ? 
      { reset: true } : 
      { 
        temperature: parseFloat(temperature),
        pressure: parseFloat(pressure),
        vibration: parseFloat(vibration),
        degradation_speed: parseFloat(degradationSpeed)
      };
    
    // Send via HTTP to backend (backend will publish to MQTT)
    fetch('http://localhost:8080/api/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(control)
    })
    .then(() => console.log('Control sent:', control))
    .catch(err => console.error('Error sending control:', err));
  };

  const presets = {
    normal: () => {
      setTemperature(70);
      setPressure(100);
      setVibration(0.5);
      setAutoMode(false);
    },
    warning: () => {
      setTemperature(82);
      setPressure(105);
      setVibration(0.85);
      setAutoMode(false);
    },
    critical: () => {
      setTemperature(92);
      setPressure(115);
      setVibration(1.2);
      setAutoMode(false);
    },
    failure: () => {
      setTemperature(98);
      setPressure(120);
      setVibration(1.5);
      setAutoMode(false);
    }
  };

  return (
      <div className="bg-white p-4">
                <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Simulator Control Panel</h1>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${mqttConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm">{mqttConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>

          {/* Mode Toggle */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={autoMode}
                onChange={(e) => setAutoMode(e.target.checked)}
                className="w-5 h-5"
              />
              <span className="font-medium text-lg">
                {autoMode ? '🤖 Automatic Mode (gradual degradation)' : '🎮 Manual Control'}
              </span>
            </label>
            <p className="text-sm text-gray-600 mt-2">
              {autoMode 
                ? 'Simulator runs autonomously with gradual machine degradation'
                : 'Manually control all sensor values in real-time'}
            </p>
          </div>

          {/* Manual Controls */}
          {!autoMode && (
            <div className="space-y-6 mb-6">
              {/* Temperature */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="block font-medium">
                    Temperature: {temperature}°C
                  </label>
                  <span className={`text-sm font-medium ${
                    temperature > 85 ? 'text-red-600' : 
                    temperature > 80 ? 'text-yellow-600' : 
                    'text-green-600'
                  }`}>
                    {temperature > 85 ? 'CRITICAL' : 
                     temperature > 80 ? 'WARNING' : 
                     'NORMAL'}
                  </span>
                </div>
                <input
                  type="range"
                  min="60"
                  max="110"
                  step="1"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>60°C (Cool)</span>
                  <span className="text-yellow-600">80°C (Warn)</span>
                  <span className="text-red-600">85°C+ (Critical)</span>
                  <span>110°C (Max)</span>
                </div>
              </div>

              {/* Vibration */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="block font-medium">
                    Vibration: {vibration} mm/s
                  </label>
                  <span className={`text-sm font-medium ${
                    vibration > 1.0 ? 'text-red-600' : 
                    vibration > 0.8 ? 'text-yellow-600' : 
                    'text-green-600'
                  }`}>
                    {vibration > 1.0 ? 'CRITICAL' : 
                     vibration > 0.8 ? 'WARNING' : 
                     'NORMAL'}
                  </span>
                </div>
                <input
                  type="range"
                  min="0.3"
                  max="3.0"
                  step="0.1"
                  value={vibration}
                  onChange={(e) => setVibration(e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.3 (Low)</span>
                  <span className="text-yellow-600">0.8 (Warn)</span>
                  <span className="text-red-600">1.0+ (Critical)</span>
                  <span>3.0 (Max)</span>
                </div>
              </div>

              {/* Pressure */}
              <div>
                <div className="flex justify-between mb-2">
                  <label className="block font-medium">
                    Pressure: {pressure} PSI
                  </label>
                  <span className={`text-sm font-medium ${
                    pressure < 70 || pressure > 120 ? 'text-red-600' : 
                    'text-green-600'
                  }`}>
                    {pressure < 70 || pressure > 120 ? 'CRITICAL' : 'NORMAL'}
                  </span>
                </div>
                <input
                  type="range"
                  min="60"
                  max="140"
                  step="5"
                  value={pressure}
                  onChange={(e) => setPressure(e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>60 (Low)</span>
                  <span>100 (Normal)</span>
                  <span>140 (High)</span>
                </div>
              </div>

              {/* Degradation Speed */}
              <div>
                <label className="block font-medium mb-2">
                  Degradation Speed: {degradationSpeed}x
                </label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.5"
                  value={degradationSpeed}
                  onChange={(e) => setDegradationSpeed(e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0x (Frozen)</span>
                  <span>0.5x (Slow)</span>
                  <span>5x (Fast)</span>
                </div>
              </div>
            </div>
          )}

          {/* Quick Presets */}
          <div className="mb-6">
            <h3 className="font-medium mb-3 text-lg">Quick Scenarios:</h3>
            <div className="grid grid-cols-4 gap-3">
              <button
                onClick={presets.normal}
                className="px-4 py-4 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium transition-colors shadow-md"
              >
                <div className="text-2xl mb-1">✅</div>
                <div>Normal</div>
                <div className="text-xs opacity-80">70°C, 0.5 mm/s</div>
              </button>
              <button
                onClick={presets.warning}
                className="px-4 py-4 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 font-medium transition-colors shadow-md"
              >
                <div className="text-2xl mb-1">⚠️</div>
                <div>Warning</div>
                <div className="text-xs opacity-80">82°C, 0.85 mm/s</div>
              </button>
              <button
                onClick={presets.critical}
                className="px-4 py-4 bg-orange-500 text-white rounded-lg hover:bg-orange-600 font-medium transition-colors shadow-md"
              >
                <div className="text-2xl mb-1">🔥</div>
                <div>Critical</div>
                <div className="text-xs opacity-80">92°C, 1.2 mm/s</div>
              </button>
              <button
                onClick={presets.failure}
                className="px-4 py-4 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium transition-colors shadow-md"
              >
                <div className="text-2xl mb-1">💥</div>
                <div>Failure</div>
                <div className="text-xs opacity-80">98°C, 1.5 mm/s</div>
              </button>
            </div>
          </div>

          {/* Apply Button */}
          <button
            onClick={sendControl}
            disabled={!mqttConnected}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-bold text-lg 
                     hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                     transition-colors shadow-lg"
          >
            {autoMode ? 'Reset to Auto Mode' : 'Apply Manual Settings'}
          </button>

          {/* Info Box */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-900">
              <strong>💡 Tip:</strong> Use presets to quickly simulate different scenarios and 
              watch how the ML model predicts failures in real-time on the Dashboard.
            </p>
          </div>

          {/* Status Info */}
          {!mqttConnected && (
            <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-900">
                <strong>⚠️ Warning:</strong> Backend not reachable. Make sure the Go backend is running on port 8080.
              </p>
            </div>
          )}
        </div>
      </div>
  );
}

export default ControlPanel;