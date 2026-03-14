import Foundation
import SwiftUI

struct Incident: Identifiable, Equatable {
    let id = UUID()
    let title: String
    let location: String
    let timestamp: Date
    var status: IncidentStatus
    let responderName: String?
}

enum IncidentStatus: String, CaseIterable {
    case enRoute = "En Route"
    case onScene = "On Scene"
    case secured = "Secured"
    case clear = "Clear"
    
    var color: SwiftUI.Color {
        switch self {
        case .enRoute: return Theme.accentBlue
        case .onScene: return Theme.accentOrange
        case .secured: return Theme.accentPurple
        case .clear: return Theme.accentGreen
        }
    }
}

extension Incident {
    static let mockIncidents: [Incident] = [
        Incident(title: "Break-in Alert", location: "123 Main Street", timestamp: Date().addingTimeInterval(-1800), status: .enRoute, responderName: "Officer Davis"),
        Incident(title: "Fire Alarm", location: "123 Main Street", timestamp: Date().addingTimeInterval(-3600), status: .clear, responderName: "Fire Dept"),
        Incident(title: "Medical Emergency", location: "456 Oak Ave", timestamp: Date().addingTimeInterval(-7200), status: .clear, responderName: "EMS")
    ]
}
