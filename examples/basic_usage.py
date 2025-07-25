"""
Basic usage example of the Juiceline Geidea Device Interface
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from geidea.device_interface import GeideaDeviceInterface
from utils import setup_logging, validate_amount, format_currency


def main():
    """
    Main example function demonstrating basic usage
    """
    # Set up logging
    setup_logging("INFO")
    
    # Initialize device interface
    device_config = {
        "device_ip": "192.168.1.100",
        "port": 8080,
        "timeout": 30
    }
    
    geidea_device = GeideaDeviceInterface(device_config)
    
    # Example payment amount
    payment_amount = 100.50
    
    # Validate amount
    if not validate_amount(payment_amount):
        print("Invalid payment amount!")
        return
    
    print(f"Processing payment: {format_currency(payment_amount)}")
    
    # Connect to device
    if geidea_device.connect():
        print("Connected to Geidea device successfully!")
        
        # Process payment
        result = geidea_device.process_payment(payment_amount)
        if result:
            print(f"Payment processed successfully!")
        else:
            print("Payment processing failed!")
        
        # Get device status
        status = geidea_device.get_device_status()
        print(f"Device status: {status}")
        
        # Disconnect
        geidea_device.disconnect()
        print("Disconnected from device")
    else:
        print("Failed to connect to Geidea device!")


if __name__ == "__main__":
    main()