import SwiftUI
import Combine

class ResponseViewModel: ObservableObject {
    @Published var isResponseMode: Bool = false
    @Published var incidents: [Incident] = Incident.mockIncidents
    @Published var selectedIncident: Incident?
    
    func updateStatus(for incident: Incident, to status: IncidentStatus) {
        if let index = incidents.firstIndex(where: { $0.id == incident.id }) {
            incidents[index].status = status
        }
    }
}

struct ModeToggle: View {
    @Binding var isResponseMode: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Mode")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
            
            HStack(spacing: 0) {
                Button(action: { isResponseMode = false }) {
                    Text("User")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(!isResponseMode ? Theme.backgroundPrimary : Theme.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(!isResponseMode ? Theme.accentBlue : Theme.backgroundTertiary)
                        .cornerRadius(8)
                }
                
                Button(action: { isResponseMode = true }) {
                    Text("Response Officer")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(isResponseMode ? Theme.backgroundPrimary : Theme.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(isResponseMode ? Theme.accentPurple : Theme.backgroundTertiary)
                        .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct StatusButton: View {
    let status: IncidentStatus
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(status.rawValue)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(isSelected ? Theme.backgroundPrimary : status.color)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(isSelected ? status.color : status.color.opacity(0.2))
                .cornerRadius(8)
        }
    }
}

struct MapPlaceholder: View {
    var body: some View {
        ZStack {
            Theme.backgroundTertiary
            
            VStack(spacing: 12) {
                Image(systemName: "map.fill")
                    .font(.system(size: 40))
                    .foregroundColor(Theme.textTertiary)
                
                Text("GPS Map View")
                    .font(.headline)
                    .foregroundColor(Theme.textTertiary)
                
                Text("Location tracking enabled")
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
            }
        }
        .frame(height: 200)
        .cornerRadius(12)
    }
}

struct IncidentCard: View {
    let incident: Incident
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(incident.title)
                    .font(.headline)
                    .foregroundColor(Theme.textPrimary)
                
                Spacer()
                
                Text(incident.status.rawValue)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(incident.status.color)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(incident.status.color.opacity(0.2))
                    .cornerRadius(6)
            }
            
            HStack {
                Image(systemName: "location.fill")
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
                
                Text(incident.location)
                    .font(.subheadline)
                    .foregroundColor(Theme.textSecondary)
            }
            
            HStack {
                Image(systemName: "clock")
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
                
                Text(incident.timestamp, style: .relative)
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
                
                Spacer()
                
                if let responder = incident.responderName {
                    Text(responder)
                        .font(.caption)
                        .foregroundColor(Theme.accentBlue)
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct ResponseView: View {
    @StateObject private var viewModel = ResponseViewModel()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    ModeToggle(isResponseMode: $viewModel.isResponseMode)
                    
                    if viewModel.isResponseMode {
                        MapPlaceholder()
                        
                        statusButtons
                    } else {
                        userModeContent
                    }
                    
                    incidentsList
                }
                .padding()
            }
            .background(Theme.backgroundPrimary.ignoresSafeArea())
            .navigationTitle("Response")
        }
    }
    
    private var statusButtons: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Update Status")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                ForEach(IncidentStatus.allCases, id: \.self) { status in
                    StatusButton(status: status, isSelected: false) { }
                }
            }
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
    
    private var userModeContent: some View {
        VStack(spacing: 16) {
            HStack {
                Image(systemName: "person.badge.shield.checkmark.fill")
                    .font(.largeTitle)
                    .foregroundColor(Theme.accentGreen)
                
                VStack(alignment: .leading) {
                    Text("Your Response Team")
                        .font(.headline)
                        .foregroundColor(Theme.textPrimary)
                    
                    Text("3 responders available")
                        .font(.subheadline)
                        .foregroundColor(Theme.textSecondary)
                }
                
                Spacer()
            }
            .padding()
            .background(Theme.backgroundSecondary)
            .cornerRadius(12)
            
            Button(action: {}) {
                HStack {
                    Image(systemName: "phone.fill")
                    Text("Contact Responders")
                }
                .font(.headline)
                .foregroundColor(Theme.backgroundPrimary)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Theme.accentGreen)
                .cornerRadius(12)
            }
        }
    }
    
    private var incidentsList: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Active Incidents")
                .font(.headline)
                .foregroundColor(Theme.textPrimary)
            
            ForEach(viewModel.incidents) { incident in
                IncidentCard(incident: incident)
            }
        }
    }
}

#Preview {
    ResponseView()
}
