import Foundation
import Combine
import SwiftUI

@_exported import struct SwiftUI.Color

struct SystemStatus: Codable {
    let connected: Bool
    let armed: Bool
    let faceRecognitionAvailable: Bool
    let faceStatus: String
    let safeFaceSet: Bool
    
    enum CodingKeys: String, CodingKey {
        case connected
        case armed
        case faceRecognitionAvailable = "face_recognition_available"
        case faceStatus = "face_status"
        case safeFaceSet = "safe_face_set"
    }
}

struct AlertResponse: Codable {
    let timestamp: String
    let alertType: String
    let confidence: Double
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case alertType = "alert_type"
        case confidence
        case message
    }
    
    func toAlert() -> Alert {
        let severity: AlertSeverity
        switch alertType {
        case "weapon":
            severity = .high
        case "gesture":
            severity = .medium
        default:
            severity = .low
        }
        
        let icon: String
        switch alertType {
        case "weapon":
            icon = "exclamationmark.triangle.fill"
        case "gesture":
            icon = "hand.raised.fill"
        default:
            icon = "bell.fill"
        }
        
        let formatter = ISO8601DateFormatter()
        let date = formatter.date(from: timestamp) ?? Date()
        
        return Alert(
            message: message,
            timestamp: date,
            severity: severity,
            icon: icon
        )
    }
}

struct DetectionFeatures: Codable {
    let gestureDetection: Bool
    let weaponDetection: Bool
    let faceRecognition: Bool
    
    enum CodingKeys: String, CodingKey {
        case gestureDetection = "gesture_detection"
        case weaponDetection = "weapon_detection"
        case faceRecognition = "face_recognition"
    }
}

struct SafeFaceStatus: Codable {
    let safeFaceSet: Bool
    let faceStatus: String
    let available: Bool
    let captureMessage: String?
    
    enum CodingKeys: String, CodingKey {
        case safeFaceSet = "safe_face_set"
        case faceStatus = "face_status"
        case available
        case captureMessage = "capture_message"
    }
}

struct SafeFaceResponse: Codable {
    let ok: Bool
    let message: String
}

class NetworkService: ObservableObject {
    static let shared = NetworkService()
    
    @Published var baseURL: String = "http://127.0.0.1:8765"
    @Published var isConnected: Bool = false
    @Published var lastError: String?
    
    private var cancellables = Set<AnyCancellable>()
    
    private init() {}
    
    func setBaseURL(_ url: String) {
        baseURL = url
    }
    
    func fetchStatus() async throws -> SystemStatus {
        let url = URL(string: "\(baseURL)/api/status")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let status = try JSONDecoder().decode(SystemStatus.self, from: data)
        await MainActor.run {
            self.isConnected = status.connected
        }
        return status
    }
    
    func fetchAlerts(limit: Int = 50) async throws -> [Alert] {
        let url = URL(string: "\(baseURL)/api/alerts?limit=\(limit)")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let alerts = try JSONDecoder().decode([AlertResponse].self, from: data)
        return alerts.map { $0.toAlert() }
    }
    
    func armSystem(armed: Bool) async throws -> Bool {
        guard let url = URL(string: "\(baseURL)/api/arm") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["armed": armed])
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let result = try JSONDecoder().decode(ArmResponse.self, from: data)
        return result.armed
    }
    
    func fetchDetectionFeatures() async throws -> DetectionFeatures {
        let url = URL(string: "\(baseURL)/api/detection/features")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        let featuresResponse = try JSONDecoder().decode(FeaturesResponse.self, from: data)
        let features = featuresResponse.features
        
        return DetectionFeatures(
            gestureDetection: features["gesture_detection"] ?? true,
            weaponDetection: features["weapon_detection"] ?? true,
            faceRecognition: features["face_recognition"] ?? true
        )
    }
    
    func updateDetectionFeatures(_ features: DetectionFeatures) async throws {
        guard let url = URL(string: "\(baseURL)/api/detection/features") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let featuresDict: [String: Bool] = [
            "gesture_detection": features.gestureDetection,
            "weapon_detection": features.weaponDetection,
            "face_recognition": features.faceRecognition
        ]
        request.httpBody = try JSONEncoder().encode(["features": featuresDict])
        
        let (_, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
    }
    
    func checkConnection() async -> Bool {
        do {
            let status = try await fetchStatus()
            return status.connected
        } catch {
            return false
        }
    }
    
    func fetchSafeFaceStatus() async throws -> SafeFaceStatus {
        let url = URL(string: "\(baseURL)/api/safe-face/status")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        return try JSONDecoder().decode(SafeFaceStatus.self, from: data)
    }
    
    func captureSafeFace() async throws -> SafeFaceResponse {
        guard let url = URL(string: "\(baseURL)/api/safe-face/capture") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        return try JSONDecoder().decode(SafeFaceResponse.self, from: data)
    }
    
    func clearSafeFace() async throws -> SafeFaceResponse {
        guard let url = URL(string: "\(baseURL)/api/safe-face/clear") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw NetworkError.invalidResponse
        }
        
        return try JSONDecoder().decode(SafeFaceResponse.self, from: data)
    }
}

private struct ArmResponse: Codable {
    let ok: Bool
    let armed: Bool
}

private struct FeaturesResponse: Codable {
    let features: [String: Bool]
}

enum NetworkError: LocalizedError {
    case invalidURL
    case invalidResponse
    case decodingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError:
            return "Failed to decode response"
        }
    }
}
