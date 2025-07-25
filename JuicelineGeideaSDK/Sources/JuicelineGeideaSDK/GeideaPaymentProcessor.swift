import Foundation

/// Payment processor for handling Geidea transactions
public class GeideaPaymentProcessor {
    public static let shared = GeideaPaymentProcessor()
    
    private let connectionManager = GeideaConnectionManager.shared
    private var processingTransactions: Set<String> = []
    private let processingQueue = DispatchQueue(label: "com.juiceline.geidea.processing", attributes: .concurrent)
    
    private init() {}
    
    /// Process a payment with the specified amount using a Geidea device
    /// - Parameters:
    ///   - amount: The payment amount
    ///   - device: The GeideaDevice to use for processing
    /// - Returns: PaymentResult containing transaction details
    public func processPayment(amount: Decimal, device: GeideaDevice) async throws -> PaymentResult {
        // Validate input
        guard amount > 0 else {
            throw GeideaDeviceError.invalidAmount
        }
        
        guard device.isConnected else {
            throw GeideaDeviceError.connectionFailed
        }
        
        // Check if device is busy (thread-safe)
        let isBusy = await withCheckedContinuation { continuation in
            processingQueue.async(flags: .barrier) {
                let busy = self.processingTransactions.contains(device.id)
                if !busy {
                    self.processingTransactions.insert(device.id)
                }
                continuation.resume(returning: busy)
            }
        }
        
        guard !isBusy else {
            throw GeideaDeviceError.deviceBusy
        }
        
        defer {
            // Always remove from processing set when done (thread-safe)
            processingQueue.async(flags: .barrier) {
                self.processingTransactions.remove(device.id)
            }
        }
        
        // Simulate payment processing
        // In a real implementation, this would communicate with the actual Geidea device
        return try await performPaymentTransaction(amount: amount, device: device)
    }
    
    /// Handle receipt processing for a transaction
    /// - Parameter transaction: The Transaction to process receipt for
    public func handleReceipt(_ transaction: Transaction) async throws {
        // Simulate receipt handling
        // In a real implementation, this would format and send/print the receipt
        print("Processing receipt for transaction: \(transaction.id)")
        
        // Generate receipt data
        let receiptData = generateReceiptData(for: transaction)
        
        // Store or transmit receipt data
        try await storeReceiptData(receiptData, for: transaction)
    }
    
    // MARK: - Private Methods
    
    private func performPaymentTransaction(amount: Decimal, device: GeideaDevice) async throws -> PaymentResult {
        // Simulate processing delay
        try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        // Generate transaction ID
        let transactionId = UUID().uuidString
        
        // Simulate payment processing with random success/failure
        let isSuccessful = Bool.random() // In real implementation, this would be based on actual device response
        
        let status: PaymentStatus = isSuccessful ? .success : .failed
        
        // Generate receipt data for successful transactions
        let receiptData = isSuccessful ? generateReceiptData(transactionId: transactionId, amount: amount) : nil
        
        return PaymentResult(
            transactionId: transactionId,
            amount: amount,
            status: status,
            timestamp: Date(),
            receiptData: receiptData
        )
    }
    
    private func generateReceiptData(transactionId: String, amount: Decimal) -> Data {
        let receiptText = """
        ================================
        PAYMENT RECEIPT
        ================================
        Transaction ID: \(transactionId)
        Amount: $\(amount)
        Date: \(DateFormatter.receiptFormatter.string(from: Date()))
        Status: APPROVED
        ================================
        """
        
        return receiptText.data(using: .utf8) ?? Data()
    }
    
    private func generateReceiptData(for transaction: Transaction) -> Data {
        return generateReceiptData(transactionId: transaction.id, amount: transaction.amount)
    }
    
    private func storeReceiptData(_ data: Data, for transaction: Transaction) async throws {
        // Simulate storing receipt data
        // In a real implementation, this might store to a database or cloud service
        print("Stored receipt data for transaction: \(transaction.id)")
    }
}

// MARK: - Extensions
private extension DateFormatter {
    static let receiptFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .medium
        return formatter
    }()
}