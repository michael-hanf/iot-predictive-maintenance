package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/rs/cors"
)

// Data structures
type SensorData struct {
	MachineID    string      `json:"machine_id"`
	Timestamp    string      `json:"timestamp"`
	Temperature  float64     `json:"temperature"`
	Vibration    float64     `json:"vibration"`
	Pressure     float64     `json:"pressure"`
	Status       string      `json:"status"`
	Degradation  float64     `json:"degradation"`
	Mode         string      `json:"mode"`
	MLPrediction *MLResponse `json:"ml_prediction,omitempty"`
}

type MLRequest struct {
	Temperature float64 `json:"temperature"`
	Vibration   float64 `json:"vibration"`
	Pressure    float64 `json:"pressure"`
}

type MLResponse struct {
	Prediction   float64 `json:"prediction"`
	MLPrediction float64 `json:"ml_prediction"`
	RuleBased    float64 `json:"rule_based"`
	RiskLevel    string  `json:"risk_level"`
	BufferSize   int     `json:"buffer_size"`
}

// Global state
var (
	mqttClient   mqtt.Client
	sensorBuffer []SensorData
	bufferMutex  sync.RWMutex
	wsClients    = make(map[*websocket.Conn]bool)
	wsUpgrader   = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
	mlServiceURL = "http://localhost:5000/predict"
)

func main() {
	fmt.Println("===========================================")
	fmt.Println("IoT Predictive Maintenance Backend")
	fmt.Println("===========================================")

	// Connect to MQTT
	opts := mqtt.NewClientOptions()
	opts.AddBroker("tcp://localhost:1883")
	opts.SetClientID("go-backend")
	opts.SetDefaultPublishHandler(mqttMessageHandler)

	mqttClient = mqtt.NewClient(opts)
	if token := mqttClient.Connect(); token.Wait() && token.Error() != nil {
		log.Fatal("MQTT connection failed:", token.Error())
	}
	fmt.Println("✅ Connected to MQTT broker")

	// Subscribe to sensor data
	topic := "sensors/+/data"
	if token := mqttClient.Subscribe(topic, 0, nil); token.Wait() && token.Error() != nil {
		log.Fatal("MQTT subscription failed:", token.Error())
	}
	fmt.Printf("✅ Subscribed to topic: %s\n", topic)

	// Setup HTTP server
	router := mux.NewRouter()

	// API endpoints
	router.HandleFunc("/api/health", healthHandler).Methods("GET")
	router.HandleFunc("/api/sensors/latest", getLatestDataHandler).Methods("GET")
	router.HandleFunc("/api/control", controlHandler).Methods("POST")
	router.HandleFunc("/ws", handleWebSocket)

	// CORS
	handler := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders: []string{"*"},
	}).Handler(router)

	// Start server
	port := ":8080"
	fmt.Printf("✅ HTTP Server starting on %s\n", port)
	fmt.Println("===========================================")
	log.Fatal(http.ListenAndServe(port, handler))
}

// MQTT message handler
func mqttMessageHandler(client mqtt.Client, msg mqtt.Message) {
	var data SensorData

	if err := json.Unmarshal(msg.Payload(), &data); err != nil {
		log.Println("Error parsing MQTT message:", err)
		return
	}

	// Get ML prediction
	mlPrediction := getMLPrediction(data)
	data.MLPrediction = &mlPrediction

	// Add to buffer
	bufferMutex.Lock()
	sensorBuffer = append(sensorBuffer, data)
	if len(sensorBuffer) > 100 {
		sensorBuffer = sensorBuffer[1:]
	}
	bufferMutex.Unlock()

	// Log
	log.Printf("📊 [%s] Temp=%.1f°C Vib=%.3f ML_Risk=%s (%.1f%%)",
		data.MachineID,
		data.Temperature,
		data.Vibration,
		mlPrediction.RiskLevel,
		mlPrediction.Prediction*100,
	)

	// Broadcast to WebSocket clients
	broadcastToWebSockets(data)
}

// Call ML service
func getMLPrediction(data SensorData) MLResponse {
	reqBody := MLRequest{
		Temperature: data.Temperature,
		Vibration:   data.Vibration,
		Pressure:    data.Pressure,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		log.Println("Error marshaling ML request:", err)
		return MLResponse{RiskLevel: "unknown"}
	}

	resp, err := http.Post(mlServiceURL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Println("Error calling ML service:", err)
		return MLResponse{RiskLevel: "unavailable"}
	}
	defer resp.Body.Close()

	var mlResp MLResponse
	if err := json.NewDecoder(resp.Body).Decode(&mlResp); err != nil {
		log.Println("Error decoding ML response:", err)
		return MLResponse{RiskLevel: "error"}
	}

	return mlResp
}

// HTTP Handlers
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":      "healthy",
		"mqtt":        "connected",
		"buffer_size": len(sensorBuffer),
		"timestamp":   time.Now().Format(time.RFC3339),
	})
}

func getLatestDataHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	bufferMutex.RLock()
	defer bufferMutex.RUnlock()

	if len(sensorBuffer) == 0 {
		json.NewEncoder(w).Encode([]SensorData{})
		return
	}

	// Return last 50 readings
	start := 0
	if len(sensorBuffer) > 50 {
		start = len(sensorBuffer) - 50
	}

	json.NewEncoder(w).Encode(sensorBuffer[start:])
}

// WebSocket handler
func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket upgrade error:", err)
		return
	}

	wsClients[conn] = true
	log.Println("🔌 WebSocket client connected")

	defer func() {
		delete(wsClients, conn)
		conn.Close()
		log.Println("🔌 WebSocket client disconnected")
	}()

	// Keep connection alive
	for {
		_, _, err := conn.ReadMessage()
		if err != nil {
			break
		}
	}
}

// Broadcast to all WebSocket clients
func broadcastToWebSockets(data SensorData) {
	for client := range wsClients {
		err := client.WriteJSON(data)
		if err != nil {
			log.Println("WebSocket write error:", err)
			client.Close()
			delete(wsClients, client)
		}
	}
}

// Add nach den anderen handlers (vor main())

func controlHandler(w http.ResponseWriter, r *http.Request) {
	var control map[string]interface{}

	if mqttClient == nil || !mqttClient.IsConnectionOpen() {
		http.Error(w, "mqtt unavailable", http.StatusServiceUnavailable)
		return
	}

	if err := json.NewDecoder(r.Body).Decode(&control); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Publish to MQTT control topic
	topic := "control/machine_001"
	payload, _ := json.Marshal(control)

	// You need the MQTT client here - make it global
	if token := mqttClient.Publish(topic, 0, false, payload); token.Wait() && token.Error() != nil {
		http.Error(w, token.Error().Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("🎮 Control sent: %v", control)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
