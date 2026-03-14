import Foundation
import SwiftUI
import Combine
import UIKit

class VideoStreamService: ObservableObject {
    static let shared = VideoStreamService()
    
    @Published var currentFrame: Image?
    @Published var isStreaming: Bool = false
    @Published var errorMessage: String?
    
    private var streamingTask: Task<Void, Never>?
    private var baseURL: String = "http://127.0.0.1:8765"
    
    private init() {}
    
    func setBaseURL(_ url: String) {
        baseURL = url
    }
    
    func startStreaming() {
        guard !isStreaming else { return }
        isStreaming = true
        
        streamingTask = Task { [weak self] in
            guard let self = self else { return }
            
            await self.fetchSnapshots()
        }
    }
    
    func stopStreaming() {
        isStreaming = false
        streamingTask?.cancel()
        streamingTask = nil
    }
    
    private func fetchSnapshots() async {
        while self.isStreaming && !Task.isCancelled {
            if let image = await fetchSnapshot() {
                await MainActor.run {
                    self.currentFrame = image
                    self.errorMessage = nil
                }
            } else {
                await MainActor.run {
                    self.errorMessage = "Failed to fetch snapshot"
                }
            }
            try? await Task.sleep(nanoseconds: 500_000_000)
        }
    }
    
    func fetchSnapshot() async -> Image? {
        guard let url = URL(string: "\(baseURL)/api/snapshot") else { 
            print("Invalid URL: \(baseURL)/api/snapshot")
            return nil 
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                print("HTTP Error: \((response as? HTTPURLResponse)?.statusCode ?? 0)")
                return nil
            }
            
            if data.isEmpty {
                print("Empty data received")
                return nil
            }
            
            if let uiImage = UIImage(data: data) {
                return Image(uiImage: uiImage)
            }
            print("Failed to create UIImage from data")
            return nil
        } catch {
            return nil
        }
    }
}
