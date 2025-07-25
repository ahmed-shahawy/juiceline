import Foundation
#if canImport(CoreBluetooth)
import CoreBluetooth
#endif
#if canImport(Combine)
import Combine
#endif

/// Core connection manager for Geidea devices
public class GeideaConnectionManager: NSObject {
    public static let shared = GeideaConnectionManager()
    
    public private(set) var activeDevices: [String: GeideaDevice] = [:]
    public private(set) var isScanning = false
    public private(set) var availableDevices: [GeideaDevice] = []
    
    #if canImport(CoreBluetooth)
    private var centralManager: CBCentralManager?
    private var discoveredPeripherals: [CBPeripheral] = []
    #endif
    
    private let scanTimeout: TimeInterval = 30.0
    
    private override init() {
        super.init()
        setupBluetoothManager()
    }
    
    private func setupBluetoothManager() {
        #if canImport(CoreBluetooth)
        centralManager = CBCentralManager(delegate: self, queue: nil)
        #endif
    }
    
    /// Scan for available Geidea devices
    /// - Returns: Array of discovered GeideaDevice objects
    public func scanForDevices() async throws -> [GeideaDevice] {
        #if canImport(CoreBluetooth)
        guard let centralManager = centralManager else {
            throw GeideaDeviceError.bluetoothUnavailable
        }
        
        guard centralManager.state == .poweredOn else {
            throw GeideaDeviceError.bluetoothUnavailable
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            isScanning = true
            availableDevices.removeAll()
            discoveredPeripherals.removeAll()
            
            // Start scanning for Geidea devices
            centralManager.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
            
            // Set timeout
            DispatchQueue.main.asyncAfter(deadline: .now() + scanTimeout) {
                self.stopScanning()
                continuation.resume(returning: self.availableDevices)
            }
        }
        #else
        // Return mock devices for non-iOS platforms
        return [GeideaDevice(id: "mock-1", name: "Mock Geidea Device", bluetoothIdentifier: "mock-bt-1")]
        #endif
    }
    
    /// Connect to a specific Geidea device
    /// - Parameter device: The GeideaDevice to connect to
    public func connect(to device: GeideaDevice) async throws {
        #if canImport(CoreBluetooth)
        guard let centralManager = centralManager else {
            throw GeideaDeviceError.bluetoothUnavailable
        }
        
        guard centralManager.state == .poweredOn else {
            throw GeideaDeviceError.bluetoothUnavailable
        }
        
        // Find the peripheral for this device
        guard let peripheral = discoveredPeripherals.first(where: { $0.identifier.uuidString == device.bluetoothIdentifier }) else {
            throw GeideaDeviceError.deviceNotFound
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            // Store continuation for completion
            self.connectionContinuations[device.id] = continuation
            
            // Attempt connection
            centralManager.connect(peripheral, options: nil)
            
            // Set timeout
            DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) {
                if self.connectionContinuations[device.id] != nil {
                    self.connectionContinuations.removeValue(forKey: device.id)
                    continuation.resume(throwing: GeideaDeviceError.timeout)
                }
            }
        }
        #else
        // Mock connection for non-iOS platforms
        let connectedDevice = GeideaDevice(
            id: device.id,
            name: device.name,
            bluetoothIdentifier: device.bluetoothIdentifier,
            isConnected: true
        )
        activeDevices[device.id] = connectedDevice
        #endif
    }
    
    /// Disconnect from a specific device
    /// - Parameter deviceId: The ID of the device to disconnect
    public func disconnect(deviceId: String) async {
        #if canImport(CoreBluetooth)
        if let device = activeDevices[deviceId],
           let peripheral = discoveredPeripherals.first(where: { $0.identifier.uuidString == device.bluetoothIdentifier }) {
            centralManager?.cancelPeripheralConnection(peripheral)
            activeDevices.removeValue(forKey: deviceId)
        }
        #else
        activeDevices.removeValue(forKey: deviceId)
        #endif
    }
    
    /// Get currently connected devices
    public var connectedDevices: [GeideaDevice] {
        return Array(activeDevices.values.filter { $0.isConnected })
    }
    
    // MARK: - Testing Support
    
    /// Add a device to active devices (for testing purposes)
    public func addActiveDevice(_ device: GeideaDevice) {
        activeDevices[device.id] = device
    }
    
    /// Remove all active devices (for testing purposes)
    public func removeAllActiveDevices() {
        activeDevices.removeAll()
    }
    
    private func stopScanning() {
        #if canImport(CoreBluetooth)
        centralManager?.stopScan()
        #endif
        isScanning = false
    }
    
    private var connectionContinuations: [String: CheckedContinuation<Void, Error>] = [:]
}

#if canImport(CoreBluetooth)
// MARK: - CBCentralManagerDelegate
extension GeideaConnectionManager: CBCentralManagerDelegate {
    public func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn:
            print("Bluetooth is powered on and ready")
        case .poweredOff:
            print("Bluetooth is powered off")
        case .unauthorized:
            print("Bluetooth access is unauthorized")
        case .unsupported:
            print("Bluetooth is not supported on this device")
        case .resetting:
            print("Bluetooth is resetting")
        case .unknown:
            print("Bluetooth state is unknown")
        @unknown default:
            print("Unknown Bluetooth state")
        }
    }
    
    public func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi RSSI: NSNumber) {
        // Filter for Geidea devices based on device name or service UUID
        guard let name = peripheral.name,
              name.lowercased().contains("geidea") || name.lowercased().contains("payment") else {
            return
        }
        
        // Avoid duplicates
        guard !discoveredPeripherals.contains(where: { $0.identifier == peripheral.identifier }) else {
            return
        }
        
        discoveredPeripherals.append(peripheral)
        
        let device = GeideaDevice(
            id: UUID().uuidString,
            name: name,
            bluetoothIdentifier: peripheral.identifier.uuidString,
            isConnected: false
        )
        
        availableDevices.append(device)
    }
    
    public func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        // Find the device that was connected
        if let device = availableDevices.first(where: { $0.bluetoothIdentifier == peripheral.identifier.uuidString }) {
            let connectedDevice = GeideaDevice(
                id: device.id,
                name: device.name,
                bluetoothIdentifier: device.bluetoothIdentifier,
                isConnected: true
            )
            
            activeDevices[device.id] = connectedDevice
            
            // Resume the connection continuation
            if let continuation = connectionContinuations[device.id] {
                connectionContinuations.removeValue(forKey: device.id)
                continuation.resume()
            }
        }
    }
    
    public func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        // Find the device that failed to connect
        if let device = availableDevices.first(where: { $0.bluetoothIdentifier == peripheral.identifier.uuidString }) {
            if let continuation = connectionContinuations[device.id] {
                connectionContinuations.removeValue(forKey: device.id)
                continuation.resume(throwing: GeideaDeviceError.connectionFailed)
            }
        }
    }
    
    public func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        // Find and remove the device that was disconnected
        if let deviceEntry = activeDevices.first(where: { $0.value.bluetoothIdentifier == peripheral.identifier.uuidString }) {
            activeDevices.removeValue(forKey: deviceEntry.key)
        }
    }
}
#endif