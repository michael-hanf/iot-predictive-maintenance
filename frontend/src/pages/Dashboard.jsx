import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function Dashboard() {
  const [sensorData, setSensorData] = useState([]);
  const [latestReading, setLatestReading] = useState(null);
  const [mlPrediction, setMlPrediction] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Fetch initial data
    fetch('http://localhost:8080/api/sensors/latest')
      .then(res => res.json())
      .then(data => {
        setSensorData(data);
        if (data.length > 0) {
          setLatestReading(data[data.length - 1]);
          if (data[data.length - 1].ml_prediction) {
            setMlPrediction(data[data.length - 1].ml_prediction);
          }
        }
      })
      .catch(err => console.error('Error fetching data:', err));

    // WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8080/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLatestReading(data);
      
      if (data.ml_prediction) {
        setMlPrediction(data.ml_prediction);
      }
      
      // Update chart data (keep last 50)
      setSensorData(prev => {
        const newData = [...prev, data].slice(-50);
        return newData;
      });
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">
            Predictive Maintenance Dashboard
          </h1>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* ML Prediction Alert */}
        {mlPrediction && mlPrediction.risk_level !== 'normal' && mlPrediction.risk_level !== 'initializing' && (
          <div className={`mb-6 p-6 rounded-lg border-l-4 ${
            mlPrediction.risk_level === 'critical' 
              ? 'bg-red-100 border-red-500' 
              : 'bg-yellow-100 border-yellow-500'
          }`}>
            <div className="flex items-center gap-4">
              <span className="text-4xl">
                {mlPrediction.risk_level === 'critical' ? '🚨' : '⚠️'}
              </span>
              <div>
                <h3 className="text-xl font-bold">
                  {mlPrediction.risk_level === 'critical' 
                    ? 'CRITICAL: Failure Imminent' 
                    : 'Warning: Elevated Risk'}
                </h3>
                <p className="text-sm mt-1">
                  ML Model Confidence: {(mlPrediction.prediction * 100).toFixed(1)}%
                  {mlPrediction.rule_based > 0 && ' (Rule-based trigger)'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Current Status Cards */}
        {latestReading && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <MetricCard 
              title="Temperature" 
              value={`${latestReading.temperature.toFixed(1)}°C`}
              status={getStatus(latestReading.temperature, 85, 80)}
              threshold="85°C"
            />
            <MetricCard 
              title="Vibration" 
              value={`${latestReading.vibration.toFixed(3)} mm/s`}
              status={getStatus(latestReading.vibration, 1.0, 0.8)}
              threshold="1.0 mm/s"
            />
            <MetricCard 
              title="Pressure" 
              value={`${latestReading.pressure.toFixed(1)} PSI`}
              status="normal"
            />
            <MetricCard 
              title="ML Risk Score" 
              value={mlPrediction 
                ? mlPrediction.risk_level === 'initializing'
                  ? `${mlPrediction.buffer_size}/50`
                  : `${(mlPrediction.prediction * 100).toFixed(0)}%`
                : '---'
              }
              status={mlPrediction?.risk_level || 'normal'}
              threshold={mlPrediction?.risk_level === 'initializing' ? 'Collecting data...' : '50%'}
            />
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <ChartCard title="Temperature Trend">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" hide />
                <YAxis domain={[60, 110]} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="temperature" 
                  stroke="#ef4444" 
                  strokeWidth={2} 
                  dot={false}
                  name="Temperature (°C)"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Vibration Trend">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" hide />
                <YAxis domain={[0, 3]} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="vibration" 
                  stroke="#3b82f6" 
                  strokeWidth={2} 
                  dot={false}
                  name="Vibration (mm/s)"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Mode Indicator */}
        {latestReading && (
          <div className="text-center text-sm text-gray-600">
            Mode: <span className="font-bold">{latestReading.mode?.toUpperCase()}</span>
            {latestReading.mode === 'manual' && ' (Controlled via Control Panel)'}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ title, value, status, threshold }) {
  const colors = {
    normal: 'bg-green-50 border-green-500 text-green-900',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    critical: 'bg-red-50 border-red-500 text-red-900',
    initializing: 'bg-blue-50 border-blue-500 text-blue-900'
  };

  return (
    <div className={`p-6 rounded-lg border-l-4 ${colors[status] || colors.normal}`}>
      <h3 className="text-sm font-medium opacity-75">{title}</h3>
      <p className="text-3xl font-bold mt-2">{value}</p>
      {threshold && <p className="text-xs mt-2 opacity-75">{threshold}</p>}
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-bold mb-4">{title}</h3>
      {children}
    </div>
  );
}

function getStatus(value, criticalThreshold, warningThreshold) {
  if (value > criticalThreshold) return 'critical';
  if (value > warningThreshold) return 'warning';
  return 'normal';
}

export default Dashboard;