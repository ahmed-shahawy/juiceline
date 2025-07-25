"""
Utility functions for Geidea device communication
"""

import logging
from datetime import datetime


def setup_logging(log_level="INFO"):
    """
    Set up logging for the Juiceline application.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_amount(amount):
    """
    Validate payment amount.
    
    Args:
        amount (float): Payment amount to validate
        
    Returns:
        bool: True if amount is valid, False otherwise
    """
    if not isinstance(amount, (int, float)):
        return False
    
    return amount > 0


def format_currency(amount, currency="SAR"):
    """
    Format amount with currency.
    
    Args:
        amount (float): Amount to format
        currency (str): Currency code
        
    Returns:
        str: Formatted amount string
    """
    return f"{amount:.2f} {currency}"


def generate_transaction_id():
    """
    Generate a unique transaction ID.
    
    Returns:
        str: Unique transaction identifier
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TXN_{timestamp}"


def parse_device_response(response):
    """
    Parse response from Geidea device.
    
    Args:
        response (dict): Raw device response
        
    Returns:
        dict: Parsed response with standardized format
    """
    # TODO: Implement response parsing logic
    return response