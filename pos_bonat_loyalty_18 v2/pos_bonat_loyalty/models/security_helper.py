# -*- coding: utf-8 -*-
import base64
import hashlib
from cryptography.fernet import Fernet
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class BonatSecurityHelper(models.AbstractModel):
    _name = 'bonat.security.helper'
    _description = 'Security Helper for Bonat Integration'

    @api.model
    def _generate_key_from_master(self, master_key):
        """Generate encryption key from master key."""
        key = hashlib.sha256(master_key.encode()).digest()
        return base64.urlsafe_b64encode(key)

    @api.model
    def encrypt_api_key(self, api_key, master_key=None):
        """Encrypt API key for secure storage."""
        if not api_key:
            return False
        
        try:
            if not master_key:
                # Use database uuid as master key for consistency
                master_key = self.env['ir.config_parameter'].sudo().get_param('database.uuid', 'default_key')
            
            key = self._generate_key_from_master(master_key)
            fernet = Fernet(key)
            encrypted = fernet.encrypt(api_key.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            _logger.error(f"Failed to encrypt API key: {e}")
            return api_key  # Return original if encryption fails

    @api.model
    def decrypt_api_key(self, encrypted_api_key, master_key=None):
        """Decrypt API key for use."""
        if not encrypted_api_key:
            return False
        
        try:
            if not master_key:
                # Use database uuid as master key for consistency
                master_key = self.env['ir.config_parameter'].sudo().get_param('database.uuid', 'default_key')
            
            key = self._generate_key_from_master(master_key)
            fernet = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_api_key.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            _logger.warning(f"Failed to decrypt API key, using as-is: {e}")
            return encrypted_api_key  # Return as-is if decryption fails

    @api.model
    def sanitize_log_data(self, data):
        """Sanitize data for logging by removing sensitive information."""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['api_key', 'reward_code', 'password', 'token', 'authorization']
            
            for key, value in data.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    sanitized[key] = '***REDACTED***'
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self.sanitize_log_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self.sanitize_log_data(item) for item in data]
        else:
            return data

    @api.model
    def validate_api_key_strength(self, api_key):
        """Validate API key strength."""
        if not api_key:
            return False, "API key cannot be empty"
        
        if len(api_key) < 20:
            return False, "API key is too short (minimum 20 characters)"
        
        if len(api_key) > 200:
            return False, "API key is too long (maximum 200 characters)"
        
        # Check for basic entropy
        unique_chars = len(set(api_key))
        if unique_chars < 10:
            return False, "API key has insufficient character diversity"
        
        return True, "API key validation passed"

    @api.model
    def hash_sensitive_data(self, data):
        """Create a hash of sensitive data for comparison without storing the actual data."""
        if not data:
            return False
        
        return hashlib.sha256(data.encode()).hexdigest()