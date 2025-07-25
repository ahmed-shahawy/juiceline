import Foundation

/// Base protocol for device communication
public protocol GeideaDeviceProtocol {
    /// Connect to the Geidea device
    func connect() async throws
    
    /// Disconnect from the Geidea device
    func disconnect() async
    
    /// Process a payment with the specified amount
    /// - Parameter amount: The payment amount
    /// - Returns: PaymentResult containing transaction details
    func processPayment(_ amount: Decimal) async throws -> PaymentResult
    
    /// Get the current connection status
    var isConnected: Bool { get }
    
    /// Get device information
    var device: GeideaDevice { get }
}

/// Errors that can occur during device operations
public enum GeideaDeviceError: Error, LocalizedError {
    case deviceNotFound
    case connectionFailed
    case paymentFailed(String)
    case bluetoothUnavailable
    case invalidAmount
    case deviceBusy
    case timeout
    
    public var errorDescription: String? {
        switch self {
        case .deviceNotFound:
            return "Geidea device not found"
        case .connectionFailed:
            return "Failed to connect to Geidea device"
        case .paymentFailed(let reason):
            return "Payment failed: \(reason)"
        case .bluetoothUnavailable:
            return "Bluetooth is unavailable"
        case .invalidAmount:
            return "Invalid payment amount"
        case .deviceBusy:
            return "Device is busy processing another transaction"
        case .timeout:
            return "Operation timed out"
        }
    }
}