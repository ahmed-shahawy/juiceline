import XCTest
@testable import JuicelineGeideaSDK
@testable import JuicelineGeideaSDKTesting

final class GeideaDeviceProtocolTests: XCTestCase {
    
    var mockDevice: MockGeideaDevice!
    
    override func setUp() {
        super.setUp()
        let device = GeideaSDKTestingUtils.createMockDevice()
        mockDevice = MockGeideaDevice(device: device)
    }
    
    override func tearDown() {
        mockDevice = nil
        super.tearDown()
    }
    
    func testDeviceConnection() async throws {
        // Given
        XCTAssertFalse(mockDevice.isConnected)
        
        // When
        try await mockDevice.connect()
        
        // Then
        XCTAssertTrue(mockDevice.isConnected)
    }
    
    func testDeviceDisconnection() async throws {
        // Given
        try await mockDevice.connect()
        XCTAssertTrue(mockDevice.isConnected)
        
        // When
        await mockDevice.disconnect()
        
        // Then
        XCTAssertFalse(mockDevice.isConnected)
    }
    
    func testFailedConnection() async throws {
        // Given
        mockDevice.shouldFailConnection = true
        
        // When/Then
        do {
            try await mockDevice.connect()
            XCTFail("Expected connection to fail")
        } catch GeideaDeviceError.connectionFailed {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
        
        XCTAssertFalse(mockDevice.isConnected)
    }
    
    func testPaymentProcessing() async throws {
        // Given
        try await mockDevice.connect()
        let amount: Decimal = 15.75
        
        // When
        let result = try await mockDevice.processPayment(amount)
        
        // Then
        XCTAssertEqual(result.amount, amount)
        XCTAssertEqual(result.status, .success)
        XCTAssertFalse(result.transactionId.isEmpty)
    }
    
    func testPaymentWithoutConnection() async throws {
        // Given
        let amount: Decimal = 10.00
        
        // When/Then
        do {
            _ = try await mockDevice.processPayment(amount)
            XCTFail("Expected payment to fail without connection")
        } catch GeideaDeviceError.connectionFailed {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testFailedPayment() async throws {
        // Given
        try await mockDevice.connect()
        mockDevice.shouldFailPayment = true
        let amount: Decimal = 10.00
        
        // When/Then
        do {
            _ = try await mockDevice.processPayment(amount)
            XCTFail("Expected payment to fail")
        } catch GeideaDeviceError.paymentFailed {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testDeviceProperties() {
        // Given/When/Then
        XCTAssertFalse(mockDevice.device.id.isEmpty)
        XCTAssertFalse(mockDevice.device.name.isEmpty)
        XCTAssertFalse(mockDevice.device.bluetoothIdentifier.isEmpty)
        XCTAssertEqual(mockDevice.isConnected, mockDevice.device.isConnected)
    }
}