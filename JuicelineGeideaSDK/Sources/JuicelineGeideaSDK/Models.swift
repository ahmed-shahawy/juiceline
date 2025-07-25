import Foundation

/// Represents a payment result from the Geidea device
public struct PaymentResult {
    public let transactionId: String
    public let amount: Decimal
    public let status: PaymentStatus
    public let timestamp: Date
    public let receiptData: Data?
    
    public init(transactionId: String, amount: Decimal, status: PaymentStatus, timestamp: Date = Date(), receiptData: Data? = nil) {
        self.transactionId = transactionId
        self.amount = amount
        self.status = status
        self.timestamp = timestamp
        self.receiptData = receiptData
    }
}

/// Payment status enumeration
public enum PaymentStatus {
    case success
    case failed
    case cancelled
    case pending
}

/// Represents a transaction
public struct Transaction {
    public let id: String
    public let amount: Decimal
    public let timestamp: Date
    public let paymentResult: PaymentResult
    
    public init(id: String, amount: Decimal, timestamp: Date = Date(), paymentResult: PaymentResult) {
        self.id = id
        self.amount = amount
        self.timestamp = timestamp
        self.paymentResult = paymentResult
    }
}

/// Represents a Geidea device
public struct GeideaDevice {
    public let id: String
    public let name: String
    public let bluetoothIdentifier: String
    public let isConnected: Bool
    
    public init(id: String, name: String, bluetoothIdentifier: String, isConnected: Bool = false) {
        self.id = id
        self.name = name
        self.bluetoothIdentifier = bluetoothIdentifier
        self.isConnected = isConnected
    }
}