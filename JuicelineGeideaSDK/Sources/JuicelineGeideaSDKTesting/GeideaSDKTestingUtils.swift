import Foundation
@testable import JuicelineGeideaSDK

/// Testing utilities for Juiceline Geidea SDK
public class GeideaSDKTestingUtils {
    
    /// Create a mock Geidea device for testing
    public static func createMockDevice(id: String? = nil, name: String = "Mock Geidea Device", isConnected: Bool = false) -> GeideaDevice {
        return GeideaDevice(
            id: id ?? UUID().uuidString,
            name: name,
            bluetoothIdentifier: UUID().uuidString,
            isConnected: isConnected
        )
    }
    
    /// Create a mock payment result for testing
    public static func createMockPaymentResult(
        transactionId: String? = nil,
        amount: Decimal = 10.00,
        status: PaymentStatus = .success
    ) -> PaymentResult {
        return PaymentResult(
            transactionId: transactionId ?? UUID().uuidString,
            amount: amount,
            status: status,
            timestamp: Date(),
            receiptData: "Mock receipt data".data(using: .utf8)
        )
    }
    
    /// Create a mock transaction for testing
    public static func createMockTransaction(
        id: String? = nil,
        amount: Decimal = 10.00,
        paymentResult: PaymentResult? = nil
    ) -> Transaction {
        let result = paymentResult ?? createMockPaymentResult(amount: amount)
        return Transaction(
            id: id ?? UUID().uuidString,
            amount: amount,
            timestamp: Date(),
            paymentResult: result
        )
    }
}

/// Mock implementation of GeideaDeviceProtocol for testing
public class MockGeideaDevice: GeideaDeviceProtocol {
    public let device: GeideaDevice
    public private(set) var isConnected: Bool = false
    
    public var shouldFailConnection = false
    public var shouldFailPayment = false
    public var paymentDelay: TimeInterval = 0.1
    
    public init(device: GeideaDevice) {
        self.device = device
    }
    
    public func connect() async throws {
        if shouldFailConnection {
            throw GeideaDeviceError.connectionFailed
        }
        
        // Simulate connection delay
        try await Task.sleep(nanoseconds: UInt64(paymentDelay * 1_000_000_000))
        isConnected = true
    }
    
    public func disconnect() async {
        isConnected = false
    }
    
    public func processPayment(_ amount: Decimal) async throws -> PaymentResult {
        guard isConnected else {
            throw GeideaDeviceError.connectionFailed
        }
        
        if shouldFailPayment {
            throw GeideaDeviceError.paymentFailed("Mock payment failure")
        }
        
        // Simulate payment processing delay
        try await Task.sleep(nanoseconds: UInt64(paymentDelay * 1_000_000_000))
        
        return GeideaSDKTestingUtils.createMockPaymentResult(amount: amount)
    }
}