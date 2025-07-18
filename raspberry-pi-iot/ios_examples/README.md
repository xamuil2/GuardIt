# iOS App Integration Examples

This directory contains example code snippets and documentation for integrating with the Raspberry Pi IoT device from an iOS application.

## API Integration

### Swift URLSession Example

```swift
import Foundation

class IoTDeviceAPI {
    let baseURL: String
    
    init(deviceIP: String, port: Int = 8000) {
        self.baseURL = "http://\(deviceIP):\(port)"
    }
    
    // Get IMU sensor data
    func getIMUData(completion: @escaping (Result<IMUData, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/imu") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let response = try JSONDecoder().decode(IMUResponse.self, from: data)
                completion(.success(response.data))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // Control RGB LED
    func setLEDColor(red: Int, green: Int, blue: Int, brightness: Double = 1.0,
                     completion: @escaping (Result<Void, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/led") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        let ledRequest = LEDRequest(red: red, green: green, blue: blue, brightness: brightness)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONEncoder().encode(ledRequest)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { _, response, error in
            if let error = error {
                completion(.failure(error))
            } else {
                completion(.success(()))
            }
        }.resume()
    }
    
    // Play buzzer
    func playBuzzer(frequency: Int = 1000, duration: Double = 0.5, count: Int = 1,
                    completion: @escaping (Result<Void, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/buzzer") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        let buzzerRequest = BuzzerRequest(frequency: frequency, duration: duration, count: count)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            request.httpBody = try JSONEncoder().encode(buzzerRequest)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { _, response, error in
            if let error = error {
                completion(.failure(error))
            } else {
                completion(.success(()))
            }
        }.resume()
    }
}

// Data models
struct IMUResponse: Codable {
    let status: String
    let data: IMUData
}

struct IMUData: Codable {
    let accelerometer: SensorReading
    let gyroscope: SensorReading
    let temperature: TemperatureReading
    let timestamp: Double
}

struct SensorReading: Codable {
    let x: Double
    let y: Double
    let z: Double
    let unit: String
}

struct TemperatureReading: Codable {
    let value: Double
    let unit: String
}

struct LEDRequest: Codable {
    let red: Int
    let green: Int
    let blue: Int
    let brightness: Double
}

struct BuzzerRequest: Codable {
    let frequency: Int
    let duration: Double
    let count: Int
}

enum APIError: Error {
    case invalidURL
    case noData
}
```

## WebSocket Integration

### Swift Starscream Example

```swift
import Starscream

class IoTWebSocketManager: WebSocketDelegate {
    private var socket: WebSocket?
    private let deviceIP: String
    
    weak var delegate: IoTWebSocketDelegate?
    
    init(deviceIP: String, port: Int = 8000) {
        self.deviceIP = deviceIP
        
        var request = URLRequest(url: URL(string: "ws://\(deviceIP):\(port)/ws")!)
        request.timeoutInterval = 5
        
        socket = WebSocket(request: request)
        socket?.delegate = self
    }
    
    func connect() {
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
    }
    
    func sendLEDCommand(red: Int, green: Int, blue: Int, brightness: Double = 1.0) {
        let command = [
            "type": "led_control",
            "data": [
                "red": red,
                "green": green,
                "blue": blue,
                "brightness": brightness
            ]
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: command),
           let string = String(data: data, encoding: .utf8) {
            socket?.write(string: string)
        }
    }
    
    func sendBuzzerCommand(frequency: Int = 1000, duration: Double = 0.5) {
        let command = [
            "type": "buzzer_control",
            "data": [
                "frequency": frequency,
                "duration": duration
            ]
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: command),
           let string = String(data: data, encoding: .utf8) {
            socket?.write(string: string)
        }
    }
    
    // MARK: - WebSocketDelegate
    
    func didReceive(event: WebSocketEvent, client: WebSocket) {
        switch event {
        case .connected(let headers):
            print("WebSocket connected: \(headers)")
            delegate?.webSocketDidConnect()
            
        case .disconnected(let reason, let code):
            print("WebSocket disconnected: \(reason) with code: \(code)")
            delegate?.webSocketDidDisconnect()
            
        case .text(let string):
            if let data = string.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                handleMessage(json)
            }
            
        case .binary(let data):
            print("Received binary data: \(data.count) bytes")
            
        case .error(let error):
            print("WebSocket error: \(error?.localizedDescription ?? "Unknown error")")
            delegate?.webSocketDidReceiveError(error)
            
        default:
            break
        }
    }
    
    private func handleMessage(_ message: [String: Any]) {
        guard let type = message["type"] as? String else { return }
        
        switch type {
        case "sensor_data":
            if let data = message["data"] as? [String: Any] {
                delegate?.webSocketDidReceiveSensorData(data)
            }
            
        case "status":
            if let data = message["data"] as? [String: Any] {
                delegate?.webSocketDidReceiveStatus(data)
            }
            
        default:
            print("Unknown message type: \(type)")
        }
    }
}

protocol IoTWebSocketDelegate: AnyObject {
    func webSocketDidConnect()
    func webSocketDidDisconnect()
    func webSocketDidReceiveError(_ error: Error?)
    func webSocketDidReceiveSensorData(_ data: [String: Any])
    func webSocketDidReceiveStatus(_ data: [String: Any])
}
```

## Camera Streaming

### Swift Camera Stream Viewer

```swift
import UIKit
import AVFoundation

class CameraStreamViewController: UIViewController {
    @IBOutlet weak var imageView: UIImageView!
    
    private let deviceIP: String
    private var streamTask: URLSessionDataTask?
    
    init(deviceIP: String) {
        self.deviceIP = deviceIP
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }
    
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        startStreaming(camera: "csi") // or "usb"
    }
    
    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        stopStreaming()
    }
    
    private func setupUI() {
        imageView.contentMode = .scaleAspectFit
        imageView.backgroundColor = .black
    }
    
    private func startStreaming(camera: String) {
        guard let url = URL(string: "http://\(deviceIP):8000/camera/\(camera)/stream") else {
            return
        }
        
        streamTask = URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            if let error = error {
                print("Stream error: \(error)")
                return
            }
            
            // Handle MJPEG stream data
            // This is a simplified example - in practice you'd need to parse the MJPEG stream
            if let data = data, let image = UIImage(data: data) {
                DispatchQueue.main.async {
                    self?.imageView.image = image
                }
            }
        }
        
        streamTask?.resume()
    }
    
    private func stopStreaming() {
        streamTask?.cancel()
        streamTask = nil
    }
}
```

## Usage Examples

### SwiftUI Integration

```swift
import SwiftUI

struct IoTDeviceView: View {
    @StateObject private var viewModel = IoTDeviceViewModel()
    
    var body: some View {
        VStack(spacing: 20) {
            // IMU Data Display
            VStack {
                Text("IMU Sensor Data")
                    .font(.headline)
                
                if let imuData = viewModel.imuData {
                    HStack {
                        VStack {
                            Text("Accelerometer")
                            Text("X: \(imuData.accelerometer.x, specifier: "%.2f")")
                            Text("Y: \(imuData.accelerometer.y, specifier: "%.2f")")
                            Text("Z: \(imuData.accelerometer.z, specifier: "%.2f")")
                        }
                        
                        VStack {
                            Text("Gyroscope")
                            Text("X: \(imuData.gyroscope.x, specifier: "%.2f")")
                            Text("Y: \(imuData.gyroscope.y, specifier: "%.2f")")
                            Text("Z: \(imuData.gyroscope.z, specifier: "%.2f")")
                        }
                    }
                }
            }
            
            // LED Control
            VStack {
                Text("LED Control")
                    .font(.headline)
                
                ColorPicker("LED Color", selection: $viewModel.selectedColor)
                
                Button("Update LED") {
                    viewModel.updateLED()
                }
                .buttonStyle(.borderedProminent)
            }
            
            // Buzzer Control
            VStack {
                Text("Buzzer Control")
                    .font(.headline)
                
                Button("Beep") {
                    viewModel.playBuzzer()
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
        .onAppear {
            viewModel.connect()
        }
        .onDisappear {
            viewModel.disconnect()
        }
    }
}

class IoTDeviceViewModel: ObservableObject {
    @Published var imuData: IMUData?
    @Published var selectedColor = Color.red
    
    private let api: IoTDeviceAPI
    private let webSocket: IoTWebSocketManager
    
    init(deviceIP: String = "192.168.1.100") {
        self.api = IoTDeviceAPI(deviceIP: deviceIP)
        self.webSocket = IoTWebSocketManager(deviceIP: deviceIP)
        self.webSocket.delegate = self
    }
    
    func connect() {
        webSocket.connect()
    }
    
    func disconnect() {
        webSocket.disconnect()
    }
    
    func updateLED() {
        let uiColor = UIColor(selectedColor)
        var red: CGFloat = 0
        var green: CGFloat = 0
        var blue: CGFloat = 0
        var alpha: CGFloat = 0
        
        uiColor.getRed(&red, green: &green, blue: &blue, alpha: &alpha)
        
        api.setLEDColor(
            red: Int(red * 255),
            green: Int(green * 255),
            blue: Int(blue * 255)
        ) { result in
            switch result {
            case .success:
                print("LED updated successfully")
            case .failure(let error):
                print("LED update failed: \(error)")
            }
        }
    }
    
    func playBuzzer() {
        api.playBuzzer { result in
            switch result {
            case .success:
                print("Buzzer played successfully")
            case .failure(let error):
                print("Buzzer play failed: \(error)")
            }
        }
    }
}

extension IoTDeviceViewModel: IoTWebSocketDelegate {
    func webSocketDidConnect() {
        print("Connected to IoT device")
    }
    
    func webSocketDidDisconnect() {
        print("Disconnected from IoT device")
    }
    
    func webSocketDidReceiveError(_ error: Error?) {
        print("WebSocket error: \(error?.localizedDescription ?? "Unknown")")
    }
    
    func webSocketDidReceiveSensorData(_ data: [String: Any]) {
        // Parse and update IMU data
        // Implementation depends on your data structure
    }
    
    func webSocketDidReceiveStatus(_ data: [String: Any]) {
        print("Received status: \(data)")
    }
}
```

## Dependencies

Add these to your iOS project:

### CocoaPods
```ruby
pod 'Starscream', '~> 4.0'  # For WebSocket support
```

### Swift Package Manager
```
https://github.com/daltoniam/Starscream  # WebSocket client
```
