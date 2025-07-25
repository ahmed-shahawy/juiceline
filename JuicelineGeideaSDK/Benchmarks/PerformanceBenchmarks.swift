import Foundation
@testable import JuicelineGeideaSDK
@testable import JuicelineGeideaSDKTesting

/// Performance benchmarks for the Geidea SDK
class GeideaPerformanceBenchmarks {
    
    private let sdk = JuicelineGeideaSDK.shared
    private let paymentProcessor = GeideaPaymentProcessor.shared
    
    /// Benchmark payment processing performance
    func benchmarkPaymentProcessing() async throws {
        print("Starting payment processing benchmark...")
        
        let device = GeideaSDKTestingUtils.createMockDevice(isConnected: true)
        let mockDeviceInstance = MockGeideaDevice(device: device)
        mockDeviceInstance.paymentDelay = 0.01 // Fast mock processing
        
        let startTime = Date()
        let numberOfPayments = 100
        
        for i in 1...numberOfPayments {
            let amount = Decimal(i)
            _ = try await mockDeviceInstance.processPayment(amount)
        }
        
        let endTime = Date()
        let totalTime = endTime.timeIntervalSince(startTime)
        let averageTime = totalTime / Double(numberOfPayments)
        
        print("Processed \(numberOfPayments) payments in \(totalTime) seconds")
        print("Average payment processing time: \(averageTime) seconds")
        print("Payments per second: \(Double(numberOfPayments) / totalTime)")
    }
    
    /// Benchmark concurrent payment processing
    func benchmarkConcurrentPayments() async throws {
        print("Starting concurrent payment benchmark...")
        
        let startTime = Date()
        let numberOfConcurrentPayments = 50
        
        try await withThrowingTaskGroup(of: PaymentResult.self) { group in
            for i in 1...numberOfConcurrentPayments {
                group.addTask {
                    let device = GeideaSDKTestingUtils.createMockDevice(
                        id: "device-\(i)",
                        isConnected: true
                    )
                    let mockDevice = MockGeideaDevice(device: device)
                    mockDevice.paymentDelay = 0.01
                    
                    return try await mockDevice.processPayment(Decimal(i))
                }
            }
            
            for try await _ in group {
                // Process each result
            }
        }
        
        let endTime = Date()
        let totalTime = endTime.timeIntervalSince(startTime)
        
        print("Processed \(numberOfConcurrentPayments) concurrent payments in \(totalTime) seconds")
        print("Concurrent payments per second: \(Double(numberOfConcurrentPayments) / totalTime)")
    }
    
    /// Benchmark device scanning performance
    func benchmarkDeviceScanning() async throws {
        print("Starting device scanning benchmark...")
        
        let startTime = Date()
        let numberOfScans = 10
        
        for _ in 1...numberOfScans {
            _ = try await sdk.getAvailableDevices()
        }
        
        let endTime = Date()
        let totalTime = endTime.timeIntervalSince(startTime)
        let averageTime = totalTime / Double(numberOfScans)
        
        print("Performed \(numberOfScans) device scans in \(totalTime) seconds")
        print("Average scan time: \(averageTime) seconds")
    }
    
    /// Run all benchmarks
    func runAllBenchmarks() async throws {
        print("=== Geidea SDK Performance Benchmarks ===\n")
        
        try await benchmarkPaymentProcessing()
        print()
        
        try await benchmarkConcurrentPayments()
        print()
        
        try await benchmarkDeviceScanning()
        print()
        
        print("=== Benchmarks Complete ===")
    }
}

// Example usage:
// let benchmarks = GeideaPerformanceBenchmarks()
// try await benchmarks.runAllBenchmarks()