import SwiftUI
import Combine

struct DetectionFeatureCard: View {
    let feature: DetectionFeature
    let onToggle: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    Circle()
                        .fill(feature.isEnabled ? Theme.accentGreen.opacity(0.2) : Theme.backgroundTertiary)
                        .frame(width: 44, height: 44)
                    
                    Image(systemName: feature.icon)
                        .foregroundColor(feature.isEnabled ? Theme.accentGreen : Theme.textTertiary)
                }
                
                Spacer()
                
                Toggle("", isOn: Binding(
                    get: { feature.isEnabled },
                    set: { _ in onToggle() }
                ))
                .tint(Theme.accentGreen)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(feature.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(Theme.textPrimary)
                
                if let lastTriggered = feature.lastTriggered {
                    Text("Last triggered: \(lastTriggered, style: .relative) ago")
                        .font(.caption)
                        .foregroundColor(Theme.textTertiary)
                } else {
                    Text("Never triggered")
                        .font(.caption)
                        .foregroundColor(Theme.textTertiary)
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct DetectionView: View {
    @StateObject private var viewModel = DetectionViewModel()
    @State private var selectedFeature: DetectionFeature?
    
    let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Detection Features")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(Theme.textPrimary)
                        .padding(.horizontal)
                    
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(viewModel.features) { feature in
                            DetectionFeatureCard(feature: feature) {
                                viewModel.toggleFeature(feature)
                            }
                            .onTapGesture {
                                selectedFeature = feature
                            }
                        }
                    }
                    .padding(.horizontal)
                    
                    safeFaceSection
                }
                .padding(.vertical)
            }
            .background(Theme.backgroundPrimary.ignoresSafeArea())
            .navigationTitle("Detection")
            .sheet(item: $selectedFeature) { feature in
                FeatureDetailSheet(feature: feature)
            }
        }
    }
    
    private var safeFaceSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Safe Face")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(Theme.textPrimary)
            
            HStack {
                Circle()
                    .fill(viewModel.safeFaceSet ? Theme.accentGreen : Theme.accentOrange)
                    .frame(width: 12, height: 12)
                
                Text(viewModel.safeFaceSet ? "Safe face is set" : "No safe face registered")
                    .foregroundColor(Theme.textSecondary)
                
                Spacer()
            }
            
            if let message = viewModel.captureMessage {
                Text(message)
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
            }
            
            HStack(spacing: 12) {
                Button(action: { viewModel.captureSafeFace() }) {
                    HStack {
                        Image(systemName: "camera.fill")
                        Text("Capture Safe Face")
                    }
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(Theme.backgroundPrimary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Theme.accentGreen)
                    .cornerRadius(8)
                }
                
                if viewModel.safeFaceSet {
                    Button(action: { viewModel.clearSafeFace() }) {
                        HStack {
                            Image(systemName: "trash.fill")
                            Text("Clear")
                        }
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(Theme.accentRed)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Theme.accentRed.opacity(0.2))
                        .cornerRadius(8)
                    }
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

struct FeatureDetailSheet: View {
    let feature: DetectionFeature
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                ZStack {
                    Circle()
                        .fill(Theme.accentGreen.opacity(0.2))
                        .frame(width: 100, height: 100)
                    
                    Image(systemName: feature.icon)
                        .font(.system(size: 40))
                        .foregroundColor(Theme.accentGreen)
                }
                
                Text(feature.name)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(Theme.textPrimary)
                
                Text(feature.description)
                    .font(.body)
                    .foregroundColor(Theme.textSecondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                VStack(spacing: 12) {
                    DetailRow(label: "Status", value: feature.isEnabled ? "Active" : "Inactive")
                    DetailRow(label: "Last Triggered", value: feature.lastTriggered?.formatted(date: .abbreviated, time: .shortened) ?? "Never")
                }
                .padding()
                .background(Theme.backgroundSecondary)
                .cornerRadius(12)
                
                Spacer()
            }
            .padding()
            .background(Theme.backgroundPrimary)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(Theme.textSecondary)
            Spacer()
            Text(value)
                .foregroundColor(Theme.textPrimary)
                .fontWeight(.medium)
        }
    }
}

#Preview {
    DetectionView()
}
