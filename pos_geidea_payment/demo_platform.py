#!/usr/bin/env python3
"""
Demo script to showcase Geidea platform detection and capabilities
"""

import json
import os
import platform

def get_python_platform_info():
    """Get platform information from Python"""
    return {
        'system': platform.system(),
        'platform': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'architecture': platform.architecture(),
        'python_version': platform.python_version(),
    }

def simulate_javascript_platform_detection():
    """Simulate JavaScript platform detection logic"""
    system = platform.system().lower()
    
    # Simulate browser platform detection
    if system == 'windows':
        js_platform = 'windows'
        capabilities = {
            'usb': True,
            'bluetooth': True,
            'serial': True,
            'network': True
        }
        recommended = ['usb', 'serial', 'network', 'bluetooth']
    elif system == 'darwin':
        js_platform = 'ios'  # Assuming iPad for demo
        capabilities = {
            'usb': False,
            'bluetooth': True,
            'serial': False,
            'network': True
        }
        recommended = ['bluetooth', 'network']
    elif system == 'linux':
        js_platform = 'android'  # Assuming Android for demo
        capabilities = {
            'usb': True,  # Via OTG
            'bluetooth': True,
            'serial': False,
            'network': True
        }
        recommended = ['usb', 'bluetooth', 'network']
    else:
        js_platform = 'unknown'
        capabilities = {
            'usb': False,
            'bluetooth': False,
            'serial': False,
            'network': True
        }
        recommended = ['network']
    
    return {
        'detected_platform': js_platform,
        'capabilities': capabilities,
        'recommended_connections': recommended
    }

def get_connection_instructions():
    """Get platform-specific connection instructions"""
    system = platform.system().lower()
    
    instructions = {
        'usb': {
            'windows': 'Connect the terminal via USB cable. Install drivers if prompted.',
            'darwin': 'USB connections are not supported on iOS devices.',
            'linux': 'Connect the terminal via USB OTG cable. Enable USB debugging if required.',
            'default': 'Connect the terminal via USB cable.'
        },
        'bluetooth': {
            'windows': 'Enable Bluetooth and pair the terminal in Windows Settings.',
            'darwin': 'Ensure Bluetooth is enabled. Pair the terminal in iOS Settings first.',
            'linux': 'Enable Bluetooth and pair the terminal in Android Settings.',
            'default': 'Enable Bluetooth and pair the terminal in system settings.'
        },
        'network': {
            'windows': 'Ensure both devices are on the same network.',
            'darwin': 'Ensure both devices are on the same WiFi network.',
            'linux': 'Ensure both devices are on the same WiFi network.',
            'default': 'Ensure both devices are on the same network.'
        },
        'serial': {
            'windows': 'Connect via COM port. Check Device Manager for port number.',
            'darwin': 'Serial connections are not supported on iOS devices.',
            'linux': 'Serial connections require USB OTG and special apps.',
            'default': 'Serial connections may not be supported on this platform.'
        }
    }
    
    platform_instructions = {}
    for conn_type, platform_map in instructions.items():
        platform_instructions[conn_type] = platform_map.get(system, platform_map['default'])
    
    return platform_instructions

def demo_terminal_configs():
    """Generate demo terminal configurations for the current platform"""
    js_info = simulate_javascript_platform_detection()
    platform_name = js_info['detected_platform']
    
    configs = []
    
    # Network terminal (always supported)
    configs.append({
        'name': f'Geidea Terminal Network ({platform_name.title()})',
        'terminal_id': 'GDA_NET_001',
        'connection_type': 'network',
        'platform': platform_name,
        'ip_address': '192.168.1.100',
        'port': 8080,
        'supported': True
    })
    
    # Add platform-specific configurations
    if js_info['capabilities']['bluetooth']:
        configs.append({
            'name': f'Geidea Terminal Bluetooth ({platform_name.title()})',
            'terminal_id': 'GDA_BT_001',
            'connection_type': 'bluetooth',
            'platform': platform_name,
            'bluetooth_address': '00:11:22:33:44:55',
            'supported': True
        })
    
    if js_info['capabilities']['usb']:
        configs.append({
            'name': f'Geidea Terminal USB ({platform_name.title()})',
            'terminal_id': 'GDA_USB_001',
            'connection_type': 'usb',
            'platform': platform_name,
            'usb_vendor_id': '0x1234',
            'usb_product_id': '0x5678',
            'supported': True
        })
    
    if js_info['capabilities']['serial']:
        configs.append({
            'name': f'Geidea Terminal Serial ({platform_name.title()})',
            'terminal_id': 'GDA_SER_001',
            'connection_type': 'serial',
            'platform': platform_name,
            'serial_port': 'COM1' if platform_name == 'windows' else '/dev/ttyUSB0',
            'supported': True
        })
    
    return configs

def main():
    """Main demo function"""
    print("=" * 70)
    print("GEIDEA PAYMENT INTEGRATION - PLATFORM DETECTION DEMO")
    print("=" * 70)
    
    # Python platform info
    print("\n📍 PYTHON PLATFORM INFORMATION")
    print("-" * 40)
    py_info = get_python_platform_info()
    for key, value in py_info.items():
        print(f"{key:15}: {value}")
    
    # JavaScript simulation
    print("\n🌐 JAVASCRIPT PLATFORM DETECTION (Simulated)")
    print("-" * 40)
    js_info = simulate_javascript_platform_detection()
    print(f"Platform        : {js_info['detected_platform']}")
    print(f"Capabilities    : {json.dumps(js_info['capabilities'], indent=18)}")
    print(f"Recommended     : {', '.join(js_info['recommended_connections'])}")
    
    # Connection instructions
    print("\n📋 CONNECTION INSTRUCTIONS")
    print("-" * 40)
    instructions = get_connection_instructions()
    for conn_type, instruction in instructions.items():
        print(f"{conn_type.upper():10}: {instruction}")
    
    # Demo terminal configurations
    print("\n⚙️  DEMO TERMINAL CONFIGURATIONS")
    print("-" * 40)
    configs = demo_terminal_configs()
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. {config['name']}")
        print(f"   Terminal ID  : {config['terminal_id']}")
        print(f"   Connection   : {config['connection_type']}")
        print(f"   Platform     : {config['platform']}")
        print(f"   Supported    : {'✅ Yes' if config['supported'] else '❌ No'}")
        
        # Show connection-specific details
        if config['connection_type'] == 'network':
            print(f"   Address      : {config['ip_address']}:{config['port']}")
        elif config['connection_type'] == 'bluetooth':
            print(f"   BT Address   : {config['bluetooth_address']}")
        elif config['connection_type'] == 'usb':
            print(f"   USB VID:PID  : {config['usb_vendor_id']}:{config['usb_product_id']}")
        elif config['connection_type'] == 'serial':
            print(f"   Serial Port  : {config['serial_port']}")
    
    print("\n" + "=" * 70)
    print("🎉 PLATFORM DETECTION DEMO COMPLETE")
    print("\nThis demonstrates how the Geidea module detects platform capabilities")
    print("and provides appropriate terminal configurations for each platform.")
    print("=" * 70)

if __name__ == "__main__":
    main()