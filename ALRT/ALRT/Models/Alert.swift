import Foundation
import SwiftUI

struct Alert: Identifiable, Equatable {
    let id = UUID()
    let message: String
    let timestamp: Date
    let severity: AlertSeverity
    let icon: String
    
    init(message: String, timestamp: Date, severity: AlertSeverity, icon: String) {
        self.message = message
        self.timestamp = timestamp
        self.severity = severity
        self.icon = icon
    }
}

enum AlertSeverity: String {
    case low
    case medium
    case high
    
    var color: SwiftUI.Color {
        switch self {
        case .low: return Theme.accentGreen
        case .medium: return Theme.accentOrange
        case .high: return Theme.accentRed
        }
    }
}

extension Alert {
    static let mockAlerts: [Alert] = [
        Alert(message: "Motion detected in backyard", timestamp: Date().addingTimeInterval(-300), severity: .medium, icon: "figure.walk"),
        Alert(message: "Noise detected - Glass break", timestamp: Date().addingTimeInterval(-1800), severity: .high, icon: "wineglass"),
        Alert(message: "Fire alarm triggered", timestamp: Date().addingTimeInterval(-3600), severity: .high, icon: "flame"),
        Alert(message: "Unknown person at front door", timestamp: Date().addingTimeInterval(-7200), severity: .medium, icon: "person.fill.questionmark"),
        Alert(message: "System armed", timestamp: Date().addingTimeInterval(-10800), severity: .low, icon: "lock.shield.fill")
    ]
}
