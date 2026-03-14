import SwiftUI

struct StatusBanner: View {
    let isConnected: Bool
    let isArmed: Bool
    
    var body: some View {
        HStack {
            Circle()
                .fill(isConnected ? Theme.accentGreen : Theme.accentOrange)
                .frame(width: 10, height: 10)
            
            Text(isConnected ? "Connected to Security System" : "Disconnected")
                .font(.subheadline)
                .foregroundColor(Theme.textSecondary)
            
            Spacer()
            
            if isArmed {
                HStack(spacing: 4) {
                    Image(systemName: "lock.shield.fill")
                        .font(.caption)
                    Text("ARMED")
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .foregroundColor(Theme.accentGreen)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Theme.accentGreen.opacity(0.2))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct ThreatLevelToggle: View {
    @Binding var isHighThreat: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Test Mode")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
            
            HStack(spacing: 0) {
                Button(action: { isHighThreat = false }) {
                    Text("Low Threat")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(!isHighThreat ? Theme.backgroundPrimary : Theme.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(!isHighThreat ? Theme.accentGreen : Theme.backgroundTertiary)
                        .cornerRadius(8)
                }
                
                Button(action: { isHighThreat = true }) {
                    Text("High Threat")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(isHighThreat ? Theme.backgroundPrimary : Theme.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(isHighThreat ? Theme.accentRed : Theme.backgroundTertiary)
                        .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct AlertCard: View {
    let alert: Alert
    
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(alert.severity.color.opacity(0.2))
                    .frame(width: 44, height: 44)
                
                Image(systemName: alert.icon)
                    .foregroundColor(alert.severity.color)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(alert.message)
                    .font(.subheadline)
                    .foregroundColor(Theme.textPrimary)
                    .lineLimit(2)
                
                Text(alert.timestamp, style: .relative)
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
            }
            
            Spacer()
            
            Circle()
                .fill(alert.severity.color)
                .frame(width: 8, height: 8)
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct QuickActionButton: View {
    let icon: String
    let label: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                ZStack {
                    Circle()
                        .fill(color.opacity(0.2))
                        .frame(width: 56, height: 56)
                    
                    Image(systemName: icon)
                        .font(.title3)
                        .foregroundColor(color)
                }
                
                Text(label)
                    .font(.caption)
                    .foregroundColor(Theme.textSecondary)
            }
        }
    }
}

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()
    @StateObject private var videoService = VideoStreamService.shared
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    StatusBanner(
                        isConnected: viewModel.isConnected,
                        isArmed: viewModel.isArmed
                    )
                    
                    statusIndicator
                    
                    videoPreview
                    
                    ThreatLevelToggle(isHighThreat: $viewModel.isHighThreat)
                    
                    quickActions
                    
                    alertsSection
                }
                .padding()
            }
            .background(Theme.backgroundPrimary.ignoresSafeArea())
            .navigationTitle("Alert")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { viewModel.toggleArm() }) {
                        Image(systemName: viewModel.isArmed ? "lock.fill" : "lock.open.fill")
                            .foregroundColor(viewModel.isArmed ? Theme.accentGreen : Theme.accentOrange)
                    }
                }
            }
            .onAppear {
                videoService.startStreaming()
            }
            .onDisappear {
                videoService.stopStreaming()
            }
        }
    }
    
    private var statusIndicator: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle()
                    .stroke(Theme.backgroundTertiary, lineWidth: 8)
                    .frame(width: 160, height: 160)
                
                Circle()
                    .trim(from: 0, to: viewModel.statusProgress)
                    .stroke(viewModel.statusColor, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                    .frame(width: 160, height: 160)
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 0.5), value: viewModel.statusProgress)
                
                VStack(spacing: 4) {
                    Image(systemName: viewModel.statusIcon)
                        .font(.system(size: 40))
                        .foregroundColor(viewModel.statusColor)
                    
                    Text(viewModel.statusText)
                        .font(.headline)
                        .foregroundColor(Theme.textPrimary)
                }
            }
            
            Text(viewModel.statusDescription)
                .font(.subheadline)
                .foregroundColor(Theme.textSecondary)
                .multilineTextAlignment(.center)
        }
            .padding()
            .frame(maxWidth: .infinity)
            .background(Theme.backgroundSecondary)
            .cornerRadius(16)
    }
    
    private var videoPreview: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Live Camera")
                    .font(.headline)
                    .foregroundColor(Theme.textPrimary)
                
                Spacer()
                
                Circle()
                    .fill(videoService.isStreaming ? Theme.accentGreen : Theme.textTertiary)
                    .frame(width: 8, height: 8)
                
                Text(videoService.isStreaming ? "Live" : "Offline")
                    .font(.caption)
                    .foregroundColor(videoService.isStreaming ? Theme.accentGreen : Theme.textTertiary)
            }
            
            if let frame = videoService.currentFrame {
                frame
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(height: 180)
                    .clipped()
                    .cornerRadius(8)
            } else {
                ZStack {
                    Theme.backgroundTertiary
                    
                    VStack(spacing: 8) {
                        Image(systemName: "video.slash.fill")
                            .font(.system(size: 30))
                            .foregroundColor(Theme.textTertiary)
                        
                        Text("Camera offline")
                            .font(.caption)
                            .foregroundColor(Theme.textTertiary)
                    }
                }
                .frame(height: 180)
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
    
    private var quickActions: some View {
        HStack(spacing: 24) {
            QuickActionButton(
                icon: "bell.badge.fill",
                label: "Silent Alarm",
                color: Theme.accentRed,
                action: { viewModel.triggerSilentAlarm() }
            )
            
            QuickActionButton(
                icon: "phone.fill",
                label: "Contact F/F",
                color: Theme.accentBlue,
                action: { }
            )
            
            QuickActionButton(
                icon: "gearshape.fill",
                label: "Settings",
                color: Theme.textSecondary,
                action: { }
            )
        }
        .padding(.vertical, 8)
    }
    
    private var alertsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Alerts")
                    .font(.headline)
                    .foregroundColor(Theme.textPrimary)
                
                Spacer()
                
                Button("See All") { }
                    .font(.subheadline)
                    .foregroundColor(Theme.accentBlue)
            }
            
            if viewModel.alerts.isEmpty {
                Text("No recent alerts")
                    .font(.subheadline)
                    .foregroundColor(Theme.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                ForEach(viewModel.alerts) { alert in
                    AlertCard(alert: alert)
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

#Preview {
    DashboardView()
}
