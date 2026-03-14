import SwiftUI
import Combine

class DetectionViewModel: ObservableObject {
    @Published var features: [DetectionFeature] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var faceStatus: String = "none"
    @Published var safeFaceSet: Bool = false
    @Published var captureMessage: String?
    
    private let networkService = NetworkService.shared
    private var pollingTask: Task<Void, Never>?
    
    init() {
        startPolling()
    }
    
    deinit {
        pollingTask?.cancel()
    }
    
    func startPolling() {
        pollingTask = Task { [weak self] in
            guard let self = self else { return }
            
            while !Task.isCancelled {
                await self.fetchData()
                try? await Task.sleep(nanoseconds: 5_000_000_000)
            }
        }
    }
    
    @MainActor
    func fetchData() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let features = try await networkService.fetchDetectionFeatures()
            let faceInfo = try await networkService.fetchSafeFaceStatus()
            
            self.faceStatus = faceInfo.faceStatus
            self.safeFaceSet = faceInfo.safeFaceSet
            self.captureMessage = faceInfo.captureMessage
            
            self.features = [
                DetectionFeature(
                    name: "Hands Up Gesture",
                    icon: "hand.raised.fill",
                    isEnabled: features.gestureDetection,
                    lastTriggered: nil,
                    description: "Recognizes hands up distress gesture"
                ),
                DetectionFeature(
                    name: "Weapon Detection",
                    icon: "exclamationmark.triangle.fill",
                    isEnabled: features.weaponDetection,
                    lastTriggered: nil,
                    description: "Detects weapons in camera view"
                ),
                DetectionFeature(
                    name: "Face Recognition",
                    icon: "person.fill.questionmark",
                    isEnabled: features.faceRecognition,
                    lastTriggered: nil,
                    description: "Identifies known vs unknown faces"
                )
            ]
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func toggleFeature(_ feature: DetectionFeature) {
        Task {
            await toggleFeatureAsync(feature)
        }
    }
    
    @MainActor
    func toggleFeatureAsync(_ feature: DetectionFeature) async {
        guard let index = features.firstIndex(where: { $0.id == feature.id }) else { return }
        
        let newEnabled = !features[index].isEnabled
        features[index].isEnabled = newEnabled
        
        do {
            let currentGesture = features.first(where: { $0.name == "Hands Up Gesture" })?.isEnabled ?? true
            let currentWeapon = features.first(where: { $0.name == "Weapon Detection" })?.isEnabled ?? true
            let currentFace = features.first(where: { $0.name == "Face Recognition" })?.isEnabled ?? true
            
            try await networkService.updateDetectionFeatures(
                DetectionFeatures(
                    gestureDetection: features[0].isEnabled,
                    weaponDetection: features[1].isEnabled,
                    faceRecognition: features[2].isEnabled
                )
            )
        } catch {
            features[index].isEnabled = !newEnabled
            errorMessage = "Failed to update: \(error.localizedDescription)"
        }
    }
    
    func captureSafeFace() {
        Task {
            await captureSafeFaceAsync()
        }
    }
    
    @MainActor
    func captureSafeFaceAsync() async {
        do {
            let result = try await networkService.captureSafeFace()
            captureMessage = result.message
        } catch {
            errorMessage = "Failed to capture: \(error.localizedDescription)"
        }
    }
    
    func clearSafeFace() {
        Task {
            await clearSafeFaceAsync()
        }
    }
    
    @MainActor
    func clearSafeFaceAsync() async {
        do {
            let result = try await networkService.clearSafeFace()
            captureMessage = result.message
        } catch {
            errorMessage = "Failed to clear: \(error.localizedDescription)"
        }
    }
}
