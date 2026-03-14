import SwiftUI
import Combine

class MembersViewModel: ObservableObject {
    @Published var members: [Member] = Member.mockMembers
    @Published var showAddMember: Bool = false
    
    func addMember(_ member: Member) {
        members.append(member)
    }
    
    func deleteMember(_ member: Member) {
        members.removeAll { $0.id == member.id }
    }
}

struct MemberRow: View {
    let member: Member
    
    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(Theme.backgroundTertiary)
                    .frame(width: 50, height: 50)
                
                Image(systemName: member.imageName)
                    .font(.title3)
                    .foregroundColor(Theme.textSecondary)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(member.name)
                    .font(.headline)
                    .foregroundColor(Theme.textPrimary)
                
                Text("Added \(member.addedDate, style: .date)")
                    .font(.caption)
                    .foregroundColor(Theme.textTertiary)
            }
            
            Spacer()
            
            HStack(spacing: 6) {
                Circle()
                    .fill(member.status.color)
                    .frame(width: 8, height: 8)
                
                Text(member.status.rawValue)
                    .font(.caption)
                    .foregroundColor(member.status.color)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(member.status.color.opacity(0.2))
            .cornerRadius(12)
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(Theme.textTertiary)
        }
        .padding()
        .background(Theme.backgroundSecondary)
        .cornerRadius(12)
    }
}

struct FaceScanSheet: View {
    @Environment(\.dismiss) var dismiss
    @State private var isScanning: Bool = false
    @State private var scanComplete: Bool = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                Theme.backgroundPrimary.ignoresSafeArea()
                
                VStack(spacing: 32) {
                    Spacer()
                    
                    ZStack {
                        Circle()
                            .stroke(scanComplete ? Theme.accentGreen : Theme.backgroundTertiary, lineWidth: 4)
                            .frame(width: 200, height: 200)
                        
                        if isScanning && !scanComplete {
                            Circle()
                                .trim(from: 0, to: 0.3)
                                .stroke(Theme.accentGreen, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                                .frame(width: 200, height: 200)
                                .rotationEffect(.degrees(isScanning ? 360 : 0))
                                .animation(.linear(duration: 1).repeatForever(autoreverses: false), value: isScanning)
                        }
                        
                        Image(systemName: scanComplete ? "checkmark" : "faceid")
                            .font(.system(size: 60))
                            .foregroundColor(scanComplete ? Theme.accentGreen : Theme.textSecondary)
                    }
                    
                    VStack(spacing: 8) {
                        Text(scanComplete ? "Face Recognized" : isScanning ? "Scanning..." : "Ready to Scan")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(Theme.textPrimary)
                        
                        Text(scanComplete ? "Person marked as safe" : "Position face within frame")
                            .font(.subheadline)
                            .foregroundColor(Theme.textSecondary)
                    }
                    
                    Spacer()
                    
                    if !scanComplete {
                        Button(action: {
                            isScanning = true
                            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                                isScanning = false
                                scanComplete = true
                            }
                        }) {
                            Text("Start Scan")
                                .font(.headline)
                                .foregroundColor(Theme.backgroundPrimary)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Theme.accentGreen)
                                .cornerRadius(12)
                        }
                    } else {
                        Button(action: { dismiss() }) {
                            Text("Done")
                                .font(.headline)
                                .foregroundColor(Theme.backgroundPrimary)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Theme.accentBlue)
                                .cornerRadius(12)
                        }
                    }
                }
                .padding()
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }
}

struct MembersView: View {
    @StateObject private var viewModel = MembersViewModel()
    @State private var showFaceScan = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                Theme.backgroundPrimary.ignoresSafeArea()
                
                if viewModel.members.isEmpty {
                    emptyState
                } else {
                    membersList
                }
                
                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        Button(action: { showFaceScan = true }) {
                            ZStack {
                                Circle()
                                    .fill(Theme.accentGreen)
                                    .frame(width: 60, height: 60)
                                
                                Image(systemName: "faceid")
                                    .font(.title2)
                                    .foregroundColor(Theme.backgroundPrimary)
                            }
                            .shadow(color: Theme.accentGreen.opacity(0.4), radius: 8, x: 0, y: 4)
                        }
                        .padding(.trailing, 24)
                        .padding(.bottom, 24)
                    }
                }
            }
            .navigationTitle("Members")
            .sheet(isPresented: $showFaceScan) {
                FaceScanSheet()
            }
        }
    }
    
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.2.slash")
                .font(.system(size: 60))
                .foregroundColor(Theme.textTertiary)
            
            Text("No Members Yet")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(Theme.textPrimary)
            
            Text("Add your first trusted member\nto get started")
                .font(.subheadline)
                .foregroundColor(Theme.textSecondary)
                .multilineTextAlignment(.center)
            
            Button(action: { showFaceScan = true }) {
                Text("Add Member")
                    .font(.headline)
                    .foregroundColor(Theme.backgroundPrimary)
                    .padding(.horizontal, 32)
                    .padding(.vertical, 12)
                    .background(Theme.accentGreen)
                    .cornerRadius(12)
            }
        }
        .padding()
    }
    
    private var membersList: some View {
        ScrollView {
            VStack(spacing: 12) {
                ForEach(viewModel.members) { member in
                    MemberRow(member: member)
                }
            }
            .padding()
        }
    }
}

#Preview {
    MembersView()
}
