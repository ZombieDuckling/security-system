import SwiftUI
import Combine

class DashboardViewModel: ObservableObject {
    @Published var isConnected: Bool = false
    @Published var isArmed: Bool = true
    @Published var isHighThreat: Bool = false
    @Published var alerts: [Alert] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    private let networkService = NetworkService.shared
    private var cancellables = Set<AnyCancellable>()
    private var pollingTask: Task<Void, Never>?
    
    var statusProgress: CGFloat {
        isArmed ? 1.0 : 0.3
    }
    
    var statusColor: Color {
        if !isConnected { return Theme.accentOrange }
        return isArmed ? Theme.accentGreen : Theme.textTertiary
    }
    
    var statusIcon: String {
        if !isConnected { return "wifi.slash" }
        return isArmed ? "shield.checkmark.fill" : "shield.fill"
    }
    
    var statusText: String {
        if !isConnected { return "Offline" }
        return isArmed ? "Secure" : "Disarmed"
    }
    
    var statusDescription: String {
        if !isConnected { return "Unable to reach security system" }
        return isArmed ? "Your home is protected" : "Security system is off"
    }
    
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
                try? await Task.sleep(nanoseconds: 2_000_000_000)
            }
        }
    }
    
    func stopPolling() {
        pollingTask?.cancel()
        pollingTask = nil
    }
    
    @MainActor
    func fetchData() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let status = try await networkService.fetchStatus()
            self.isConnected = status.connected
            self.isArmed = status.armed
            
            let fetchedAlerts = try await networkService.fetchAlerts(limit: 20)
            self.alerts = fetchedAlerts
        } catch {
            self.errorMessage = error.localizedDescription
            self.isConnected = false
        }
        
        isLoading = false
    }
    
    func toggleArm() {
        Task {
            await toggleArmAsync()
        }
    }
    
    @MainActor
    func toggleArmAsync() async {
        let newArmedState = !isArmed
        
        do {
            let armed = try await networkService.armSystem(armed: newArmedState)
            self.isArmed = armed
            
            let alertMessage = armed ? "System armed" : "System disarmed"
            let newAlert = Alert(
                message: alertMessage,
                timestamp: Date(),
                severity: .low,
                icon: armed ? "lock.shield.fill" : "lock.open.fill"
            )
            alerts.insert(newAlert, at: 0)
        } catch {
            errorMessage = "Failed to toggle arm state: \(error.localizedDescription)"
        }
    }
    
    func triggerSilentAlarm() {
        let newAlert = Alert(
            message: "Silent alarm triggered",
            timestamp: Date(),
            severity: .high,
            icon: "bell.badge.fill"
        )
        alerts.insert(newAlert, at: 0)
    }
    
    func setServerURL(_ url: String) {
        networkService.setBaseURL(url)
    }
}
