import Foundation
import SwiftUI

struct Member: Identifiable, Equatable {
    let id = UUID()
    let name: String
    let imageName: String
    var status: MemberStatus
    let addedDate: Date
}

enum MemberStatus: String {
    case safe = "Safe"
    case unknown = "Unknown"
    case pending = "Pending"
    
    var color: SwiftUI.Color {
        switch self {
        case .safe: return Theme.accentGreen
        case .unknown: return Theme.accentOrange
        case .pending: return Theme.textTertiary
        }
    }
}

extension Member {
    static let mockMembers: [Member] = [
        Member(name: "John Smith", imageName: "person.fill", status: .safe, addedDate: Date().addingTimeInterval(-86400 * 30)),
        Member(name: "Sarah Smith", imageName: "person.fill", status: .safe, addedDate: Date().addingTimeInterval(-86400 * 25)),
        Member(name: "Mike Johnson", imageName: "person.fill", status: .unknown, addedDate: Date().addingTimeInterval(-86400 * 10)),
        Member(name: "Emily Davis", imageName: "person.fill", status: .pending, addedDate: Date().addingTimeInterval(-86400 * 2))
    ]
}
