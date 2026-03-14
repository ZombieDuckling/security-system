import SwiftUI

struct Theme {
    static let backgroundPrimary = Color(hex: "0D0D0D")
    static let backgroundSecondary = Color(hex: "1A1A1A")
    static let backgroundTertiary = Color(hex: "262626")
    
    static let accentGreen = Color(hex: "00C853")
    static let accentRed = Color(hex: "FF1744")
    static let accentOrange = Color(hex: "FF9100")
    static let accentBlue = Color(hex: "2979FF")
    static let accentPurple = Color(hex: "7C4DFF")
    
    static let textPrimary = Color.white
    static let textSecondary = Color(hex: "B3B3B3")
    static let textTertiary = Color(hex: "666666")
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
