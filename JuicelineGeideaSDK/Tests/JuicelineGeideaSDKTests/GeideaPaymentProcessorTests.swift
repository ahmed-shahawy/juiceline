import XCTest
@testable import JuicelineGeideaSDK
@testable import JuicelineGeideaSDKTesting

final class GeideaPaymentProcessorTests: XCTestCase {
    
    var paymentProcessor: GeideaPaymentProcessor!
    var mockDevice: GeideaDevice!
    
    override func setUp() {
        super.setUp()
        paymentProcessor = GeideaPaymentProcessor.shared
        mockDevice = GeideaSDKTestingUtils.createMockDevice(isConnected: true)
    }
    
    override func tearDown() {
        paymentProcessor = nil
        mockDevice = nil
        super.tearDown()
    }
    
    func testProcessPaymentWithValidAmount() async throws {
        // Given
        let amount: Decimal = 25.50
        
        // When
        let result = try await paymentProcessor.processPayment(amount: amount, device: mockDevice)
        
        // Then
        XCTAssertEqual(result.amount, amount)
        XCTAssertFalse(result.transactionId.isEmpty)
        XCTAssertTrue([PaymentStatus.success, PaymentStatus.failed].contains(result.status))
    }
    
    func testProcessPaymentWithInvalidAmount() async throws {
        // Given
        let invalidAmount: Decimal = -10.00
        
        // When/Then
        do {
            _ = try await paymentProcessor.processPayment(amount: invalidAmount, device: mockDevice)
            XCTFail("Expected GeideaDeviceError.invalidAmount to be thrown")
        } catch GeideaDeviceError.invalidAmount {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testProcessPaymentWithDisconnectedDevice() async throws {
        // Given
        let disconnectedDevice = GeideaSDKTestingUtils.createMockDevice(isConnected: false)
        let amount: Decimal = 10.00
        
        // When/Then
        do {
            _ = try await paymentProcessor.processPayment(amount: amount, device: disconnectedDevice)
            XCTFail("Expected GeideaDeviceError.connectionFailed to be thrown")
        } catch GeideaDeviceError.connectionFailed {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testHandleReceipt() async throws {
        // Given
        let transaction = GeideaSDKTestingUtils.createMockTransaction()
        
        // When/Then - Should not throw
        try await paymentProcessor.handleReceipt(transaction)
    }
    
    func testConcurrentPaymentProcessing() async throws {
        // Given
        let amount1: Decimal = 15.00
        let amount2: Decimal = 20.00
        let device1 = GeideaSDKTestingUtils.createMockDevice(name: "Device 1", isConnected: true)
        let device2 = GeideaSDKTestingUtils.createMockDevice(name: "Device 2", isConnected: true)
        
        // When
        async let result1 = paymentProcessor.processPayment(amount: amount1, device: device1)
        async let result2 = paymentProcessor.processPayment(amount: amount2, device: device2)
        
        let (payment1, payment2) = try await (result1, result2)
        
        // Then
        XCTAssertEqual(payment1.amount, amount1)
        XCTAssertEqual(payment2.amount, amount2)
        XCTAssertNotEqual(payment1.transactionId, payment2.transactionId)
    }
    
    func testDeviceBusyError() async throws {
        // Given
        let amount: Decimal = 10.00
        
        // When - Start first payment
        let task1 = Task {
            try await paymentProcessor.processPayment(amount: amount, device: mockDevice)
        }
        
        // Give first payment a moment to start
        try await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Try to start second payment on same device immediately
        do {
            _ = try await paymentProcessor.processPayment(amount: amount, device: mockDevice)
            XCTFail("Expected GeideaDeviceError.deviceBusy to be thrown")
        } catch GeideaDeviceError.deviceBusy {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
        
        // Wait for first payment to complete
        _ = try await task1.value
    }
}