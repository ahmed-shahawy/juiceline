import Foundation

/// Main SDK module for Juiceline Geidea integration
public class JuicelineGeideaSDK {
    public static let shared = JuicelineGeideaSDK()
    
    public let connectionManager = GeideaConnectionManager.shared
    public let paymentProcessor = GeideaPaymentProcessor.shared
    
    private init() {}
    
    /// Initialize the SDK with configuration
    public func initialize() async throws {
        // Perform any necessary initialization
        print("JuicelineGeideaSDK initialized successfully")
    }
    
    /// Get available Geidea devices
    public func getAvailableDevices() async throws -> [GeideaDevice] {
        return try await connectionManager.scanForDevices()
    }
    
    /// Create a device instance for interaction
    public func createDeviceInstance(for device: GeideaDevice) -> GeideaDeviceProtocol {
        return GeideaDeviceImpl(device: device)
    }
    
    /// Quick payment method for simple transactions
    public func processQuickPayment(amount: Decimal, deviceId: String) async throws -> PaymentResult {
        guard let device = connectionManager.activeDevices[deviceId] else {
            throw GeideaDeviceError.deviceNotFound
        }
        
        return try await paymentProcessor.processPayment(amount: amount, device: device)
    }
}