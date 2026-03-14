import Foundation

struct DetectionFeature: Identifiable, Equatable {
    let id = UUID()
    let name: String
    let icon: String
    var isEnabled: Bool
    var lastTriggered: Date?
    let description: String
}

extension DetectionFeature {
    static let mockFeatures: [DetectionFeature] = [
        DetectionFeature(name: "Forced Entry Noise", icon: "waveform", isEnabled: true, lastTriggered: Date().addingTimeInterval(-1800), description: "Detects forced entry sounds"),
        DetectionFeature(name: "Hands Up Gesture", icon: "hand.raised.fill", isEnabled: true, lastTriggered: nil, description: "Recognizes hands up gesture"),
        DetectionFeature(name: "Fire/Smoke Detection", icon: "flame.fill", isEnabled: true, lastTriggered: Date().addingTimeInterval(-3600), description: "Detects fire and smoke"),
        DetectionFeature(name: "Screaming Voice", icon: "person.bust", isEnabled: true, lastTriggered: nil, description: "Detects screaming/voice stress"),
        DetectionFeature(name: "Night Vision", icon: "moon.fill", isEnabled: false, lastTriggered: nil, description: "Night vision camera support"),
        DetectionFeature(name: "Unusual Person", icon: "person.fill.questionmark", isEnabled: true, lastTriggered: Date().addingTimeInterval(-7200), description: "Detects unrecognized persons"),
        DetectionFeature(name: "Silence Detection", icon: "speaker.slash.fill", isEnabled: false, lastTriggered: nil, description: "Alerts when home goes quiet unexpectedly"),
        DetectionFeature(name: "Motion Detection", icon: "figure.walk.motion", isEnabled: true, lastTriggered: Date().addingTimeInterval(-300), description: "Detects motion when away")
    ]
}
