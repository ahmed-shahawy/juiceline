from odoo import models, api, _
import requests
import logging
import time
from functools import lru_cache

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize request tracking
        self._request_tracker = {}
        self._max_requests_per_minute = 60
        self._cleanup_interval = 300  # 5 minutes

    def _cleanup_request_tracker(self):
        """Clean up old request tracking entries"""
        current_time = time.time()
        cutoff_time = current_time - self._cleanup_interval
        
        keys_to_remove = [
            key for key, timestamp in self._request_tracker.items() 
            if timestamp < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self._request_tracker[key]

    def _check_rate_limit(self, request_type, identifier):
        """Check if request is within rate limits"""
        current_time = time.time()
        key = f"{request_type}_{identifier}"
        
        # Clean up old entries periodically
        if len(self._request_tracker) > 100:
            self._cleanup_request_tracker()
        
        # Check if request is too frequent
        if key in self._request_tracker:
            time_diff = current_time - self._request_tracker[key]
            if time_diff < 1:  # Minimum 1 second between requests
                return False
        
        self._request_tracker[key] = current_time
        return True

    def _validate_redeem_data(self, redeem_data):
        """Enhanced validation for redeem data"""
        required_fields = ["reward_code", "merchant_id", "branch_id", "date", "timestamp"]
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if not redeem_data.get(field)]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate reward code format
        reward_code = redeem_data.get("reward_code", "")
        if not reward_code or len(reward_code) < 3 or len(reward_code) > 20:
            return False, "Invalid reward code format"
        
        # Validate merchant ID
        merchant_id = redeem_data.get("merchant_id", "")
        if not merchant_id or len(merchant_id) > 50:
            return False, "Invalid merchant ID"
        
        # Validate timestamp
        try:
            timestamp = int(redeem_data.get("timestamp"))
            current_time = int(time.time())
            # Allow timestamps within 24 hours
            if abs(current_time - timestamp) > 86400:
                return False, "Invalid timestamp - request too old"
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"
        
        return True, ""

    def _make_api_request(self, url, data, headers, timeout=10, max_retries=3):
        """Enhanced API request with retry logic and better error handling"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff
                    wait_time = min(2 ** attempt, 10)
                    time.sleep(wait_time)
                    _logger.info(f"Retrying API request, attempt {attempt + 1}/{max_retries}")
                
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
                
                # Log request details for debugging (without sensitive data)
                safe_data = {k: v for k, v in data.items() if k not in ['reward_code']}
                _logger.info(f"API Request to {url}: status={response.status_code}, data_keys={list(safe_data.keys())}")
                
                if response.status_code == 200:
                    return response, None
                elif response.status_code == 429:  # Rate limited
                    _logger.warning("Rate limited by API, will retry")
                    last_error = f"Rate limited (429): {response.text}"
                    continue
                elif response.status_code >= 500:  # Server error, retry
                    _logger.warning(f"Server error {response.status_code}, will retry")
                    last_error = f"Server error ({response.status_code}): {response.text}"
                    continue
                else:  # Client error, don't retry
                    _logger.error(f"Client error {response.status_code}: {response.text}")
                    return None, f"API Error: {response.status_code} - {response.reason}"
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                _logger.warning(f"Request timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                _logger.warning(f"Connection error on attempt {attempt + 1}")
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {str(e)}"
                _logger.error(f"Request exception on attempt {attempt + 1}: {e}")
                
        return None, last_error

    @api.model
    def pos_reward_redeem(self, redeem_data):
        """
        Enhanced Bonat reward redemption with improved validation and error handling
        """
        try:
            _logger.info(f"Processing Bonat reward redemption request")
            
            # Validate input data
            is_valid, error_msg = self._validate_redeem_data(redeem_data)
            if not is_valid:
                _logger.error(f"Validation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            reward_code = redeem_data.get("reward_code")
            
            # Check rate limiting
            if not self._check_rate_limit("redeem", reward_code):
                _logger.warning(f"Rate limit exceeded for reward code redemption")
                return {"success": False, "error": "Too many requests. Please wait and try again."}
            
            # Check company configuration
            company = self.env.company
            if not company.enable_bonat_integration:
                _logger.warning("Bonat integration is not enabled")
                return {"success": False, "error": "Bonat integration is not enabled"}
            
            if not company.bonat_api_key:
                _logger.warning("Bonat API key is missing")
                return {"success": False, "error": "Bonat integration is not properly configured"}
            
            # Prepare API request
            api_url = "https://api.bonat.io/odoo_partner/redeem"
            headers = {
                "Authorization": f"Bearer {company.bonat_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Odoo-POS-Bonat/1.0"
            }
            
            bonat_redeem_data = {
                "reward_code": reward_code,
                "merchant_id": redeem_data.get("merchant_id"),
                "branch_id": redeem_data.get("branch_id"),
                "date": redeem_data.get("date"),
                "timestamp": redeem_data.get("timestamp"),
            }
            
            # Make API request with retry logic
            response, error = self._make_api_request(api_url, bonat_redeem_data, headers)
            
            if response is None:
                _logger.error(f"Failed to connect to Bonat API: {error}")
                return {"success": False, "error": f"Unable to process request: {error}"}
            
            try:
                data = response.json()
            except ValueError as e:
                _logger.error(f"Invalid JSON response from Bonat API: {e}")
                return {"success": False, "error": "Invalid response from loyalty service"}
            
            _logger.info(f"Bonat API Response: code={data.get('code')}")
            
            if data.get("code") == 0:  # Success response
                return {"success": True, "data": data.get("data")}
            else:
                error_message = data.get("errors", "Invalid reward code or code already used")
                _logger.warning(f"Bonat API returned error: {error_message}")
                return {"success": False, "error": error_message}
                
        except Exception as e:
            _logger.exception("Unexpected error in Bonat reward redemption")
            return {"success": False, "error": "An unexpected error occurred. Please try again."}

    @api.model
    def pos_order_creation_request(self, order_creation_data):
        """
        Enhanced order creation with better validation and error handling
        """
        try:
            _logger.info("Processing POS order creation request")
            
            # Validate order data
            if not order_creation_data or not isinstance(order_creation_data, dict):
                return {"success": False, "error": "Invalid order data"}
            
            order_info = order_creation_data.get("order", {})
            if not order_info:
                return {"success": False, "error": "Missing order information"}
            
            # Check company configuration
            company = self.env.company
            if not company.enable_bonat_integration or not company.bonat_api_key:
                _logger.warning("Bonat integration not properly configured")
                return {"success": False, "error": "Loyalty service not available"}
            
            # Rate limiting for order creation
            order_id = order_info.get("order_id", "unknown")
            if not self._check_rate_limit("order", str(order_id)):
                _logger.warning("Rate limit exceeded for order creation")
                return {"success": False, "error": "Too many requests. Please wait and try again."}
            
            api_url = "https://api.bonat.io/odoo_partner/order"
            headers = {
                "Authorization": f"Bearer {company.bonat_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Odoo-POS-Bonat/1.0"
            }
            
            # Make API request with retry logic
            response, error = self._make_api_request(api_url, order_creation_data, headers)
            
            if response is None:
                _logger.error(f"Failed to send order to Bonat API: {error}")
                # Don't fail the order creation if loyalty service is down
                return {"success": True, "warning": "Order created but loyalty service unavailable"}
            
            try:
                data = response.json()
            except ValueError as e:
                _logger.error(f"Invalid JSON response from Bonat API: {e}")
                return {"success": True, "warning": "Order created but loyalty service response invalid"}
            
            if data.get("code") == 0:  # Success response from Bonat
                _logger.info("Order successfully sent to Bonat loyalty service")
                return {"success": True, "data": data.get("data")}
            else:
                error_msg = data.get("errors", "Loyalty service error")
                _logger.warning(f"Bonat API error for order creation: {error_msg}")
                # Don't fail the order creation if loyalty service has issues
                return {"success": True, "warning": f"Order created but loyalty service error: {error_msg}"}
                
        except Exception as e:
            _logger.exception("Unexpected error in order creation request")
            # Don't fail the order creation for loyalty service errors
            return {"success": True, "warning": "Order created but loyalty service unavailable"}
