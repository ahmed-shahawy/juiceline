# Juiceline Geidea SDK - Example Usage

This directory contains examples of how to use the Juiceline Geidea SDK for payment processing.

## Basic Usage Example

```swift
import JuicelineGeideaSDK

class PaymentViewController: UIViewController {
    private let sdk = JuicelineGeideaSDK.shared
    private var connectedDevice: GeideaDeviceProtocol?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        Task {
            try await initializeSDK()
        }
    }
    
    private func initializeSDK() async throws {
        // Initialize the SDK
        try await sdk.initialize()
        
        // Scan for available devices
        let devices = try await sdk.getAvailableDevices()
        
        if let firstDevice = devices.first {
            // Create device instance and connect
            connectedDevice = sdk.createDeviceInstance(for: firstDevice)
            try await connectedDevice?.connect()
            print("Connected to device: \(firstDevice.name)")
        }
    }
    
    @IBAction func processPaymentTapped(_ sender: UIButton) {
        guard let device = connectedDevice else {
            showAlert("No device connected")
            return
        }
        
        Task {
            do {
                let amount: Decimal = 25.99
                let result = try await device.processPayment(amount)
                
                switch result.status {
                case .success:
                    showAlert("Payment successful! Transaction ID: \(result.transactionId)")
                case .failed:
                    showAlert("Payment failed")
                case .cancelled:
                    showAlert("Payment cancelled")
                case .pending:
                    showAlert("Payment pending")
                }
            } catch {
                showAlert("Payment error: \(error.localizedDescription)")
            }
        }
    }
    
    private func showAlert(_ message: String) {
        DispatchQueue.main.async {
            let alert = UIAlertController(title: "Payment", message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            self.present(alert, animated: true)
        }
    }
}
```

## Advanced Usage with Receipt Handling

```swift
import JuicelineGeideaSDK

class AdvancedPaymentManager {
    private let sdk = JuicelineGeideaSDK.shared
    private let paymentProcessor = GeideaPaymentProcessor.shared
    
    func processPaymentWithReceipt(amount: Decimal, deviceId: String) async throws {
        // Process payment
        let result = try await sdk.processQuickPayment(amount: amount, deviceId: deviceId)
        
        if result.status == .success {
            // Create transaction for receipt handling
            let transaction = Transaction(
                id: result.transactionId,
                amount: amount,
                timestamp: result.timestamp,
                paymentResult: result
            )
            
            // Handle receipt
            try await paymentProcessor.handleReceipt(transaction)
            print("Receipt processed for transaction: \(transaction.id)")
        }
    }
}
```

## Error Handling Best Practices

```swift
import JuicelineGeideaSDK

class PaymentErrorHandler {
    
    func handlePaymentError(_ error: Error) {
        switch error {
        case GeideaDeviceError.bluetoothUnavailable:
            // Show Bluetooth settings prompt
            showBluetoothAlert()
            
        case GeideaDeviceError.deviceNotFound:
            // Rescan for devices
            rescanForDevices()
            
        case GeideaDeviceError.connectionFailed:
            // Retry connection
            retryConnection()
            
        case GeideaDeviceError.paymentFailed(let reason):
            // Show specific payment error
            showPaymentError(reason)
            
        case GeideaDeviceError.deviceBusy:
            // Wait and retry
            waitAndRetry()
            
        default:
            // Generic error handling
            showGenericError(error.localizedDescription)
        }
    }
    
    private func showBluetoothAlert() {
        // Implementation for Bluetooth alert
    }
    
    private func rescanForDevices() {
        // Implementation for device rescanning
    }
    
    private func retryConnection() {
        // Implementation for connection retry
    }
    
    private func showPaymentError(_ reason: String) {
        // Implementation for payment error display
    }
    
    private func waitAndRetry() {
        // Implementation for retry logic
    }
    
    private func showGenericError(_ message: String) {
        // Implementation for generic error display
    }
}
```