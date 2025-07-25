import Foundation

/// Concrete implementation of GeideaDeviceProtocol
public class GeideaDeviceImpl: GeideaDeviceProtocol {
    public private(set) var device: GeideaDevice
    public private(set) var isConnected: Bool = false
    
    private let connectionManager = GeideaConnectionManager.shared
    private let paymentProcessor = GeideaPaymentProcessor.shared
    
    public init(device: GeideaDevice) {
        self.device = device
    }
    
    public func connect() async throws {
        try await connectionManager.connect(to: device)
        
        // Update connection status
        if let connectedDevice = connectionManager.activeDevices[device.id] {
            self.device = connectedDevice
            self.isConnected = connectedDevice.isConnected
        } else {
            throw GeideaDeviceError.connectionFailed
        }
    }
    
    public func disconnect() async {
        await connectionManager.disconnect(deviceId: device.id)
        self.isConnected = false
        
        // Update device status
        self.device = GeideaDevice(
            id: device.id,
            name: device.name,
            bluetoothIdentifier: device.bluetoothIdentifier,
            isConnected: false
        )
    }
    
    public func processPayment(_ amount: Decimal) async throws -> PaymentResult {
        guard isConnected else {
            throw GeideaDeviceError.connectionFailed
        }
        
        return try await paymentProcessor.processPayment(amount: amount, device: device)
    }
}