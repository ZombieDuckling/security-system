import SwiftUI
import Combine

class SettingsViewModel: ObservableObject {
    @Published var sleepTimeStart: Date = Calendar.current.date(bySettingHour: 22, minute: 0, second: 0, of: Date())!
    @Published var sleepTimeEnd: Date = Calendar.current.date(bySettingHour: 7, minute: 0, second: 0, of: Date())!
    @Published var sensitivity: Double = 0.7
    @Published var notificationsEnabled: Bool = true
    @Published var locationSharing: Bool = true
    @Published var safeWordRecorded: Bool = false
}

struct SettingsRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    var subtitle: String? = nil
    var showChevron: Bool = true
    var toggle: Bool? = nil
    var value: String? = nil
    
    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(iconColor.opacity(0.2))
                    .frame(width: 36, height: 36)
                
                Image(systemName: icon)
                    .foregroundColor(iconColor)
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body)
                    .foregroundColor(Theme.textPrimary)
                
                if let subtitle = subtitle {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundColor(Theme.textTertiary)
                }
            }
            
            Spacer()
            
            if let toggle = toggle {
                Toggle("", isOn: Binding(
                    get: { toggle },
                    set: { _ in }
                ))
                .tint(Theme.accentGreen)
            } else if let value = value {
                Text(value)
                    .font(.subheadline)
                    .foregroundColor(Theme.textSecondary)
            }
            
            if showChevron {
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @State private var showTimePicker: Bool = false
    @State private var showSafeWordAlert: Bool = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    systemSettings
                    communicationSettings
                    informationSection
                }
                .padding()
            }
            .background(Theme.backgroundPrimary.ignoresSafeArea())
            .navigationTitle("Settings")
        }
    }
    
    private var systemSettings: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("System Settings")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
                .padding(.leading, 4)
            
            VStack(spacing: 8) {
                Button(action: { showTimePicker = true }) {
                    SettingsRow(
                        icon: "moon.fill",
                        iconColor: Theme.accentPurple,
                        title: "Sleep Time",
                        subtitle: "More sensitive during sleep",
                        showChevron: false
                    )
                }
                .buttonStyle(.plain)
                
                SettingsRow(
                    icon: "waveform.path",
                    iconColor: Theme.accentOrange,
                    title: "Noise Sensitivity",
                    subtitle: "Detection threshold",
                    showChevron: false
                )
                
                VStack(spacing: 4) {
                    HStack {
                        Text("Low")
                            .font(.caption)
                            .foregroundColor(Theme.textTertiary)
                        Spacer()
                        Text("High")
                            .font(.caption)
                            .foregroundColor(Theme.textTertiary)
                    }
                    Slider(value: $viewModel.sensitivity)
                        .tint(Theme.accentGreen)
                }
                .padding()
                .background(Theme.backgroundSecondary)
                .cornerRadius(12)
                
                Button(action: { showSafeWordAlert = true }) {
                    SettingsRow(
                        icon: "key.fill",
                        iconColor: Theme.accentGreen,
                        title: "Safe Word",
                        subtitle: viewModel.safeWordRecorded ? "Recorded" : "Tap to record",
                        showChevron: false
                    )
                }
                .buttonStyle(.plain)
                
                SettingsRow(
                    icon: "location.fill",
                    iconColor: Theme.accentBlue,
                    title: "Location Sharing",
                    subtitle: "Share GPS with responders",
                    showChevron: false
                )
                .onTapGesture {
                    viewModel.locationSharing.toggle()
                }
            }
        }
    }
    
    private var communicationSettings: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Communication")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
                .padding(.leading, 4)
            
            VStack(spacing: 8) {
                SettingsRow(
                    icon: "bell.fill",
                    iconColor: Theme.accentRed,
                    title: "Notifications",
                    subtitle: "Alert notifications",
                    showChevron: false
                )
                .onTapGesture {
                    viewModel.notificationsEnabled.toggle()
                }
                
                SettingsRow(
                    icon: "exclamationmark.triangle.fill",
                    iconColor: Theme.accentOrange,
                    title: "False Alarm",
                    subtitle: "Communication settings",
                    showChevron: true
                )
            }
        }
    }
    
    private var informationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Information")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
                .padding(.leading, 4)
            
            VStack(spacing: 8) {
                SettingsRow(
                    icon: "info.circle.fill",
                    iconColor: Theme.accentBlue,
                    title: "About",
                    subtitle: "Version 1.0.0",
                    showChevron: true
                )
                
                SettingsRow(
                    icon: "questionmark.circle.fill",
                    iconColor: Theme.textSecondary,
                    title: "Help & Support",
                    showChevron: true
                )
                
                SettingsRow(
                    icon: "doc.text.fill",
                    iconColor: Theme.textSecondary,
                    title: "Privacy Policy",
                    showChevron: true
                )
            }
        }
    }
}

#Preview {
    SettingsView()
}
