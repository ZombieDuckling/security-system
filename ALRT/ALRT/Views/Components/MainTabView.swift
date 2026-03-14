import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "shield.fill")
                }
                .tag(0)
            
            DetectionView()
                .tabItem {
                    Label("Detection", systemImage: "sensor.fill")
                }
                .tag(1)
            
            ResponseView()
                .tabItem {
                    Label("Response", systemImage: "person.badge.shield.checkmark.fill")
                }
                .tag(2)
            
            MembersView()
                .tabItem {
                    Label("Members", systemImage: "person.2.fill")
                }
                .tag(3)
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
                .tag(4)
        }
        .tint(Theme.accentGreen)
    }
}

#Preview {
    MainTabView()
}
