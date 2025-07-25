import XCTest
@testable import JuicelineGeideaSDK
@testable import JuicelineGeideaSDKTesting

final class JuicelineGeideaSDKTests: XCTestCase {
    
    var sdk: JuicelineGeideaSDK!
    
    override func setUp() {
        super.setUp()
        sdk = JuicelineGeideaSDK.shared
    }
    
    override func tearDown() {
        sdk = nil
        super.tearDown()
    }
    
    func testSDKInitialization() async throws {
        // When/Then - Should not throw
        try await sdk.initialize()
    }
    
    func testCreateDeviceInstance() {
        // Given
        let mockDevice = GeideaSDKTestingUtils.createMockDevice()
        
        // When
        let deviceInstance = sdk.createDeviceInstance(for: mockDevice)
        
        // Then
        XCTAssertNotNil(deviceInstance)
        XCTAssertEqual(deviceInstance.device.id, mockDevice.id)
        XCTAssertEqual(deviceInstance.device.name, mockDevice.name)
    }
    
    func testQuickPaymentWithExistingDevice() async throws {
        // Given
        let mockDevice = GeideaSDKTestingUtils.createMockDevice(isConnected: true)
        sdk.connectionManager.addActiveDevice(mockDevice)
        let amount: Decimal = 25.99
        
        // When
        let result = try await sdk.processQuickPayment(amount: amount, deviceId: mockDevice.id)
        
        // Then
        XCTAssertEqual(result.amount, amount)
        XCTAssertFalse(result.transactionId.isEmpty)
    }
    
    func testQuickPaymentWithNonExistentDevice() async throws {
        // Given
        let nonExistentDeviceId = "non-existent-device"
        let amount: Decimal = 10.00
        
        // When/Then
        do {
            _ = try await sdk.processQuickPayment(amount: amount, deviceId: nonExistentDeviceId)
            XCTFail("Expected GeideaDeviceError.deviceNotFound to be thrown")
        } catch GeideaDeviceError.deviceNotFound {
            // Expected error
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
    
    func testSDKSingletonInstance() {
        // Given/When
        let instance1 = JuicelineGeideaSDK.shared
        let instance2 = JuicelineGeideaSDK.shared
        
        // Then
        XCTAssertTrue(instance1 === instance2)
    }
}