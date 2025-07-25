# -*- coding: utf-8 -*-
import logging
import requests
import time
import hashlib
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from functools import lru_cache

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_bonat_integration = fields.Boolean(string="Enable Bonat Integration")
    bonat_api_key = fields.Char(string="Bonat API Key")
    bonat_merchant_name = fields.Char(string="Merchant Name", default="Name")
    bonat_merchant_id = fields.Char(string="Merchant ID", default="ABCD1234")
    
    # New fields for enhanced functionality
    bonat_cache_timeout = fields.Integer(
        string="Cache Timeout (minutes)", 
        default=5, 
        help="How long to cache API responses"
    )
    bonat_retry_attempts = fields.Integer(
        string="Retry Attempts", 
        default=3, 
        help="Number of retry attempts for failed API calls"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize cache for API responses
        self._code_response_cache = {}
        self._cache_cleanup_time = time.time()

    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        # Clean up every 10 minutes
        if current_time - self._cache_cleanup_time > 600:
            expired_keys = []
            for key, (response, timestamp, timeout) in self._code_response_cache.items():
                if current_time - timestamp > timeout:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._code_response_cache[key]
                
            self._cache_cleanup_time = current_time
            _logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _get_cache_key(self, code, merchant_id):
        """Generate a cache key for API responses"""
        combined = f"{code}_{merchant_id}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_cached_response(self, cache_key):
        """Get cached response if valid"""
        self._cleanup_cache()
        
        if cache_key in self._code_response_cache:
            response, timestamp, timeout = self._code_response_cache[cache_key]
            if time.time() - timestamp < timeout:
                _logger.info("Using cached response for code validation")
                return response
            else:
                # Remove expired entry
                del self._code_response_cache[cache_key]
        
        return None

    def _cache_response(self, cache_key, response, timeout_minutes=5):
        """Cache API response"""
        timeout_seconds = timeout_minutes * 60
        self._code_response_cache[cache_key] = (response, time.time(), timeout_seconds)
        
        # Limit cache size to prevent memory issues
        if len(self._code_response_cache) > 100:
            # Remove oldest entries
            sorted_items = sorted(
                self._code_response_cache.items(), 
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            for key, _ in sorted_items[:20]:  # Remove 20 oldest
                del self._code_response_cache[key]

    def _validate_code_format(self, code):
        """Validate the format of the reward code"""
        if not code or not isinstance(code, str):
            return False, "Code cannot be empty"
        
        code = code.strip()
        if len(code) < 3:
            return False, "Code must be at least 3 characters long"
        
        if len(code) > 50:
            return False, "Code is too long (maximum 50 characters)"
        
        # Allow alphanumeric characters and common special characters
        import re
        if not re.match(r'^[A-Za-z0-9\-_]+$', code):
            return False, "Code contains invalid characters"
        
        return True, ""

    def _validate_api_configuration(self):
        """Validate Bonat API configuration"""
        if not self.enable_bonat_integration:
            return False, _("Bonat integration is not enabled")
        
        if not self.bonat_api_key:
            return False, _("Bonat API key is missing")
        
        if not self.bonat_merchant_id:
            return False, _("Merchant ID is missing")
        
        if len(self.bonat_api_key) < 10:
            return False, _("API key appears to be invalid")
        
        return True, ""

    def _make_api_request(self, url, payload, timeout=10):
        """Make API request with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.bonat_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Odoo-POS-Bonat/1.0"
        }
        
        max_retries = max(1, self.bonat_retry_attempts or 3)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = min(2 ** attempt, 10)
                    time.sleep(wait_time)
                    _logger.info(f"Retrying API request, attempt {attempt + 1}/{max_retries}")
                
                # Log request (without sensitive data)
                safe_payload = {k: "***" if k == "reward_code" else v for k, v in payload.items()}
                _logger.info(f"Making API request to {url}: {safe_payload}")
                
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    return response, None
                elif response.status_code == 429:  # Rate limited
                    last_error = "Too many requests. Please wait and try again."
                    _logger.warning("Rate limited by Bonat API")
                    continue
                elif response.status_code >= 500:  # Server error
                    last_error = f"Loyalty service temporarily unavailable (Error {response.status_code})"
                    _logger.warning(f"Server error from Bonat API: {response.status_code}")
                    continue
                else:  # Client error
                    error_msg = f"API Error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if "errors" in error_data:
                            error_msg = error_data["errors"]
                    except:
                        error_msg = response.text
                    
                    _logger.error(f"Client error from Bonat API: {response.status_code} - {error_msg}")
                    return None, error_msg
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout. Please check your internet connection and try again."
                _logger.warning(f"Timeout on API request attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                last_error = "Unable to connect to loyalty service. Please check your internet connection."
                _logger.warning(f"Connection error on API request attempt {attempt + 1}")
            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                _logger.error(f"Request exception on attempt {attempt + 1}: {e}")
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                _logger.exception(f"Unexpected error on API request attempt {attempt + 1}")
                break  # Don't retry for unexpected errors
        
        return None, last_error

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + [
            "enable_bonat_integration", 
            "bonat_api_key", 
            "bonat_merchant_id", 
            "bonat_merchant_name",
            "bonat_cache_timeout",
            "bonat_retry_attempts"
        ]

    @api.model
    def get_bonat_code_response(self, code):
        """
        Enhanced Bonat code validation with caching and better error handling
        """
        try:
            _logger.info("Processing Bonat code validation request")
            
            # Validate input
            is_valid, error_msg = self._validate_code_format(code)
            if not is_valid:
                return {"success": False, "error": [error_msg]}
            
            # Validate configuration
            is_configured, config_error = self._validate_api_configuration()
            if not is_configured:
                return {"success": False, "error": [config_error]}
            
            # Check cache first
            cache_key = self._get_cache_key(code, self.bonat_merchant_id)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Prepare API request
            api_url = "https://api.bonat.io/odoo_partner/reward-check"
            payload = {
                "reward_code": code.strip().upper(),  # Normalize code
                "merchant_id": self.bonat_merchant_id
            }
            
            # Make API request
            response, error = self._make_api_request(api_url, payload)
            
            if response is None:
                error_msg = error or "Unable to validate code. Please try again."
                _logger.error(f"Failed to validate Bonat code: {error_msg}")
                return {"success": False, "error": [error_msg]}
            
            try:
                data = response.json()
            except ValueError as e:
                _logger.error(f"Invalid JSON response from Bonat API: {e}")
                return {"success": False, "error": ["Invalid response from loyalty service"]}
            
            _logger.info(f"Bonat API response: code={data.get('code')}")
            
            if data.get("code") == 0 and data.get("data"):
                api_data = data.get("data")
                result = {"success": True, "data": api_data}
                
                # Cache successful response
                cache_timeout = max(1, self.bonat_cache_timeout or 5)
                self._cache_response(cache_key, result, cache_timeout)
                
                return result
            else:
                error_messages = data.get("errors", ["This code has already been used or is invalid"])
                if isinstance(error_messages, str):
                    error_messages = [error_messages]
                
                result = {"success": False, "error": error_messages}
                
                # Cache failed responses for a shorter time to prevent repeated API calls
                self._cache_response(cache_key, result, 1)  # 1 minute cache for errors
                
                return result
                
        except Exception as e:
            _logger.exception("Unexpected error in Bonat code validation")
            return {"success": False, "error": ["An unexpected error occurred. Please try again."]}

    @api.constrains('bonat_api_key')
    def _check_api_key_format(self):
        """Validate API key format"""
        for record in self:
            if record.bonat_api_key and len(record.bonat_api_key) < 10:
                raise UserError(_("Bonat API key appears to be too short. Please check your configuration."))

    @api.constrains('bonat_cache_timeout')
    def _check_cache_timeout(self):
        """Validate cache timeout"""
        for record in self:
            if record.bonat_cache_timeout and (record.bonat_cache_timeout < 1 or record.bonat_cache_timeout > 60):
                raise UserError(_("Cache timeout must be between 1 and 60 minutes."))

    @api.constrains('bonat_retry_attempts')
    def _check_retry_attempts(self):
        """Validate retry attempts"""
        for record in self:
            if record.bonat_retry_attempts and (record.bonat_retry_attempts < 1 or record.bonat_retry_attempts > 10):
                raise UserError(_("Retry attempts must be between 1 and 10."))
