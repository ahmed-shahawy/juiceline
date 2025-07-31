# -*- coding: utf-8 -*-

import json
import logging
import threading
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Payment transaction model for Geidea integration."""
    
    _inherit = 'payment.transaction'

    # Geidea-specific transaction fields
    # Note: tracking=False to prevent sensitive data logging (Security fix #1)
    geidea_transaction_id = fields.Char(
        string='Geidea Transaction ID',
        help='Transaction ID returned by Geidea',
        readonly=True,
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_payment_id = fields.Char(
        string='Geidea Payment ID',
        help='Payment ID returned by Geidea',
        readonly=True,
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_order_id = fields.Char(
        string='Geidea Order ID',
        help='Order ID sent to Geidea',
        readonly=True,
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_response_code = fields.Char(
        string='Geidea Response Code',
        help='Response code from Geidea gateway',
        readonly=True,
    )
    geidea_response_message = fields.Text(
        string='Geidea Response Message',
        help='Response message from Geidea gateway',
        readonly=True,
    )
    geidea_card_brand = fields.Char(
        string='Card Brand',
        help='Card brand used for payment (VISA, MasterCard, etc.)',
        readonly=True,
    )
    geidea_card_last_four = fields.Char(
        string='Card Last Four Digits',
        help='Last four digits of the card used',
        readonly=True,
        tracking=False,  # Security fix: prevent logging sensitive data
    )
    geidea_processed_at = fields.Datetime(
        string='Processed At',
        help='Timestamp when the transaction was processed by Geidea',
        readonly=True,
    )

    def _get_specific_rendering_values(self, processing_values):
        """Return Geidea-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'geidea':
            return res

        # Use fields.Datetime.now() instead of request.env.cr.now() (Structure fix #2)
        current_time = fields.Datetime.now()
        
        # Generate unique order ID
        order_id = f"ODO-{self.reference}-{int(current_time.timestamp())}"
        
        rendering_values = {
            'api_url': self.provider_id._geidea_get_api_url('direct/pay'),
            'merchant_id': self.provider_id.geidea_merchant_id,
            'order_id': order_id,
            'amount': float_round(self.amount, precision_digits=2),
            'currency': self.currency_id.name,
            'customer_email': self.partner_email or '',
            'return_url': processing_values.get('return_url'),
            'callback_url': processing_values.get('callback_url'),
            'timestamp': current_time.isoformat(),
        }
        
        # Store order ID for tracking
        self.geidea_order_id = order_id
        
        return rendering_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find transaction from Geidea notification data."""
        if provider_code != 'geidea':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        # Extract transaction reference from Geidea response
        reference = notification_data.get('orderNo') or notification_data.get('reference')
        geidea_tx_id = notification_data.get('transactionId')
        
        if not reference and not geidea_tx_id:
            raise ValidationError(_('Geidea: Missing transaction reference in notification data.'))

        # Search by reference first, then by Geidea transaction ID
        domain = [('provider_code', '=', 'geidea')]
        if reference:
            domain.append(('reference', '=', reference))
        elif geidea_tx_id:
            domain.append(('geidea_transaction_id', '=', geidea_tx_id))

        tx = self.search(domain, limit=1)
        if not tx:
            raise ValidationError(_(
                'Geidea: No transaction found matching reference %s or transaction ID %s.',
                reference, geidea_tx_id
            ))

        return tx

    def _process_notification_data(self, notification_data):
        """Process Geidea notification data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'geidea':
            return

        # Extract Geidea-specific data
        self.geidea_transaction_id = notification_data.get('transactionId', '')
        self.geidea_payment_id = notification_data.get('paymentId', '')
        self.geidea_response_code = notification_data.get('responseCode', '')
        self.geidea_response_message = notification_data.get('responseMessage', '')
        
        # Extract card information if available
        card_info = notification_data.get('paymentMethod', {})
        if isinstance(card_info, dict):
            self.geidea_card_brand = card_info.get('brand', '')
            self.geidea_card_last_four = card_info.get('maskedCardNumber', '')[-4:] if card_info.get('maskedCardNumber') else ''

        # Use fields.Datetime.now() instead of request.env.cr.now() (Structure fix #2)
        self.geidea_processed_at = fields.Datetime.now()

        # Update transaction status based on Geidea response
        response_code = notification_data.get('responseCode', '')
        
        if response_code == '000':  # Success
            self._set_done()
            _logger.info('Geidea transaction %s processed successfully.', self.reference)
        elif response_code in ['001', '002', '003']:  # Pending states
            self._set_pending()
            _logger.info('Geidea transaction %s is pending.', self.reference)
        else:  # Error states
            self._set_error(
                _('Geidea payment failed: %s') % notification_data.get('responseMessage', 'Unknown error')
            )
            _logger.warning(
                'Geidea transaction %s failed with code %s: %s',
                self.reference, response_code, notification_data.get('responseMessage', 'Unknown error')
            )

    def _geidea_make_request_async(self, endpoint, data=None, method='POST', callback=None):
        """
        Make asynchronous request to Geidea API to prevent blocking (Structure fix #3).
        
        Args:
            endpoint (str): API endpoint
            data (dict): Request payload
            method (str): HTTP method
            callback (function): Callback function to handle response
        """
        def _make_request():
            try:
                session = requests.Session()
                
                # Configure retry strategy
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)

                # Prepare request
                url = self.provider_id._geidea_get_api_url(endpoint)
                headers = self._geidea_get_request_headers()
                timeout = self.provider_id.geidea_timeout or 30

                _logger.info('Making async Geidea API request to: %s', url)
                
                # Make request
                if method.upper() == 'POST':
                    response = session.post(url, json=data, headers=headers, timeout=timeout)
                elif method.upper() == 'GET':
                    response = session.get(url, params=data, headers=headers, timeout=timeout)
                else:
                    response = session.request(method, url, json=data, headers=headers, timeout=timeout)

                # Process response
                response_data = self._geidea_process_response(response)
                
                # Execute callback if provided
                if callback and callable(callback):
                    callback(response_data, None)
                    
            except Exception as error:
                _logger.error('Geidea async request failed: %s', str(error))
                if callback and callable(callback):
                    callback(None, error)

        # Execute in separate thread to prevent blocking
        thread = threading.Thread(target=_make_request)
        thread.daemon = True
        thread.start()

    def _geidea_get_request_headers(self):
        """Get headers for Geidea API requests."""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.provider_id.geidea_public_key}',
            'Merchant-Id': self.provider_id.geidea_merchant_id,
        }

    def _geidea_process_response(self, response):
        """
        Process Geidea API response with improved error handling (API Response fix #4).
        
        Args:
            response: requests.Response object
            
        Returns:
            dict: Processed response data
            
        Raises:
            UserError: For API errors
        """
        try:
            response.raise_for_status()
            response_data = response.json()
            
            _logger.info('Geidea API response: %s', response_data)
            return response_data
            
        except requests.exceptions.HTTPError as e:
            error_msg = f'Geidea API HTTP Error: {e}'
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = f'Geidea API Error: {error_data["errors"]}'
                elif 'message' in error_data:
                    error_msg = f'Geidea API Error: {error_data["message"]}'
            except (ValueError, KeyError):
                pass
            
            _logger.error(error_msg)
            raise UserError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f'Geidea API Request Error: {str(e)}'
            _logger.error(error_msg)
            raise UserError(error_msg)
            
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = f'Geidea API Response Parse Error: {str(e)}'
            _logger.error(error_msg)
            raise UserError(error_msg)

    def _geidea_refund_transaction(self, amount_to_refund=None):
        """
        Process refund through Geidea API.
        
        Args:
            amount_to_refund (float): Amount to refund, None for full refund
        """
        if not self.geidea_transaction_id:
            raise UserError(_('Cannot refund: Geidea transaction ID is missing.'))

        refund_amount = amount_to_refund or self.amount
        
        refund_data = {
            'originalTransactionId': self.geidea_transaction_id,
            'amount': float_round(refund_amount, precision_digits=2),
            'currency': self.currency_id.name,
            'reason': 'Customer refund request',
        }

        def refund_callback(response_data, error):
            if error:
                _logger.error('Geidea refund failed for transaction %s: %s', self.reference, str(error))
                return
                
            if response_data and response_data.get('responseCode') == '000':
                _logger.info('Geidea refund successful for transaction %s', self.reference)
                # Create refund transaction record
                self._create_refund_transaction(refund_amount, response_data)
            else:
                error_msg = response_data.get('responseMessage', 'Unknown refund error')
                _logger.error('Geidea refund failed for transaction %s: %s', self.reference, error_msg)

        # Make async refund request
        self._geidea_make_request_async('direct/refund', refund_data, callback=refund_callback)

    def _create_refund_transaction(self, refund_amount, response_data):
        """Create a refund transaction record."""
        refund_tx = self.create({
            'reference': f'REFUND-{self.reference}-{int(fields.Datetime.now().timestamp())}',
            'provider_id': self.provider_id.id,
            'amount': -refund_amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'operation': 'refund',
            'source_transaction_id': self.id,
            'geidea_transaction_id': response_data.get('transactionId', ''),
            'geidea_response_code': response_data.get('responseCode', ''),
            'geidea_response_message': response_data.get('responseMessage', ''),
            'state': 'done',
        })
        return refund_tx

    def set_geidea_transaction_id(self, transaction_id):
        """
        Set Geidea transaction ID (POS Interface fix #4).
        This method was referenced in POS but missing from the model.
        
        Args:
            transaction_id (str): Geidea transaction ID
        """
        if not transaction_id:
            raise ValidationError(_('Transaction ID cannot be empty.'))
            
        self.ensure_one()
        self.geidea_transaction_id = transaction_id
        _logger.info('Geidea transaction ID set for %s: %s', self.reference, transaction_id)