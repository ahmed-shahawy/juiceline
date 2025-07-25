# Juiceline Documentation

## Project Structure

```
juiceline/
├── src/                    # Source code
│   ├── geidea/            # Geidea device communication module
│   │   ├── __init__.py
│   │   └── device_interface.py
│   ├── __init__.py
│   └── utils.py           # Utility functions
├── config/                # Configuration files
│   ├── settings.py        # Application settings
│   └── development.py     # Development environment config
├── examples/              # Usage examples
│   └── basic_usage.py     # Basic usage example
├── docs/                  # Documentation
│   └── README.md          # This file
└── README.md              # Main project README
```

## Getting Started

### Installation

1. Clone the repository
2. Configure your Geidea API credentials in `config/development.py`
3. Run the basic example: `python examples/basic_usage.py`

### Configuration

Edit the configuration files in the `config/` directory:

- `settings.py`: General application settings
- `development.py`: Development environment specific settings

### Usage

The main interface is provided by the `GeideaDeviceInterface` class:

```python
from geidea.device_interface import GeideaDeviceInterface

# Initialize with device configuration
device = GeideaDeviceInterface(device_config)

# Connect to device
device.connect()

# Process payment
result = device.process_payment(100.50, "SAR")

# Disconnect
device.disconnect()
```

## API Reference

### GeideaDeviceInterface

Main class for device communication.

#### Methods

- `connect()`: Establish connection to device
- `disconnect()`: Close device connection
- `process_payment(amount, currency)`: Process a payment
- `get_device_status()`: Get device status

### Utilities

- `validate_amount(amount)`: Validate payment amount
- `format_currency(amount, currency)`: Format currency display
- `generate_transaction_id()`: Generate unique transaction ID

## Development

This project is ready for development of Geidea device communication features.

### Next Steps

1. Implement actual device communication protocols
2. Add error handling and validation
3. Implement transaction logging
4. Add unit tests
5. Create production configuration