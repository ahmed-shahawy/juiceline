from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Geidea Global Settings
    geidea_global_enabled = fields.Boolean(
        'Enable Geidea Payments Globally',
        config_parameter='geidea.global_enabled',
        help='Enable Geidea payments across all POS configurations'
    )
    
    # API Configuration
    geidea_api_url_test = fields.Char(
        'Geidea Test API URL',
        config_parameter='geidea.api_url_test',
        default='https://api-test.geidea.net/v1'
    )
    geidea_api_url_production = fields.Char(
        'Geidea Production API URL',
        config_parameter='geidea.api_url_production',
        default='https://api.geidea.net/v1'
    )
    
    # Security Settings
    geidea_encryption_enabled = fields.Boolean(
        'Enable Data Encryption',
        config_parameter='geidea.encryption_enabled',
        default=True,
        help='Encrypt sensitive payment data'
    )
    geidea_ssl_verify = fields.Boolean(
        'Verify SSL Certificates',
        config_parameter='geidea.ssl_verify',
        default=True,
        help='Verify SSL certificates for API calls'
    )
    geidea_webhook_secret = fields.Char(
        'Global Webhook Secret',
        config_parameter='geidea.webhook_secret',
        help='Secret key for webhook verification'
    )
    
    # Transaction Settings
    geidea_transaction_timeout = fields.Integer(
        'Transaction Timeout (seconds)',
        config_parameter='geidea.transaction_timeout',
        default=30,
        help='Timeout for payment transactions'
    )
    geidea_retry_attempts = fields.Integer(
        'Retry Attempts',
        config_parameter='geidea.retry_attempts',
        default=3,
        help='Number of retry attempts for failed transactions'
    )
    geidea_auto_reconcile = fields.Boolean(
        'Auto Reconcile Payments',
        config_parameter='geidea.auto_reconcile',
        default=True,
        help='Automatically reconcile successful payments'
    )
    
    # Device Management
    geidea_device_discovery = fields.Boolean(
        'Enable Device Discovery',
        config_parameter='geidea.device_discovery',
        default=True,
        help='Automatically discover Geidea devices'
    )
    geidea_device_heartbeat = fields.Integer(
        'Device Heartbeat Interval (seconds)',
        config_parameter='geidea.device_heartbeat',
        default=30,
        help='Interval for device heartbeat checks'
    )
    geidea_offline_mode = fields.Boolean(
        'Enable Offline Mode',
        config_parameter='geidea.offline_mode',
        default=False,
        help='Allow offline transaction processing'
    )
    
    # Multi-Platform Support
    geidea_windows_support = fields.Boolean(
        'Windows Support',
        config_parameter='geidea.windows_support',
        default=True,
        help='Enable Windows device support'
    )
    geidea_ios_support = fields.Boolean(
        'iOS/iPad Support',
        config_parameter='geidea.ios_support',
        default=True,
        help='Enable iOS/iPad device support'
    )
    geidea_android_support = fields.Boolean(
        'Android Support',
        config_parameter='geidea.android_support',
        default=True,
        help='Enable Android device support'
    )
    
    # Logging and Monitoring
    geidea_logging_level = fields.Selection([
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical')
    ], 'Logging Level',
        config_parameter='geidea.logging_level',
        default='INFO',
        help='Set logging level for Geidea operations'
    )
    geidea_log_retention = fields.Integer(
        'Log Retention (days)',
        config_parameter='geidea.log_retention',
        default=90,
        help='Number of days to retain transaction logs'
    )
    geidea_monitoring_enabled = fields.Boolean(
        'Enable Monitoring',
        config_parameter='geidea.monitoring_enabled',
        default=True,
        help='Enable real-time transaction monitoring'
    )
    
    # Receipt and Printing
    geidea_print_receipts = fields.Boolean(
        'Print Receipts',
        config_parameter='geidea.print_receipts',
        default=True,
        help='Automatically print receipts for Geidea payments'
    )
    geidea_receipt_template = fields.Selection([
        ('standard', 'Standard'),
        ('detailed', 'Detailed'),
        ('minimal', 'Minimal'),
        ('custom', 'Custom')
    ], 'Receipt Template',
        config_parameter='geidea.receipt_template',
        default='standard',
        help='Receipt template for Geidea payments'
    )
    
    # Multi-Currency Support
    geidea_multi_currency = fields.Boolean(
        'Multi-Currency Support',
        config_parameter='geidea.multi_currency',
        default=True,
        help='Enable multi-currency payment processing'
    )
    geidea_currency_conversion = fields.Boolean(
        'Auto Currency Conversion',
        config_parameter='geidea.currency_conversion',
        default=False,
        help='Automatically convert currencies'
    )
    
    # Webhook Configuration
    geidea_webhook_enabled = fields.Boolean(
        'Enable Webhooks',
        config_parameter='geidea.webhook_enabled',
        default=True,
        help='Enable webhook notifications from Geidea'
    )
    geidea_webhook_url = fields.Char(
        'Webhook URL',
        config_parameter='geidea.webhook_url',
        help='URL for receiving Geidea webhooks'
    )
    
    # Analytics and Reporting
    geidea_analytics_enabled = fields.Boolean(
        'Enable Analytics',
        config_parameter='geidea.analytics_enabled',
        default=True,
        help='Enable payment analytics and reporting'
    )
    geidea_real_time_dashboard = fields.Boolean(
        'Real-time Dashboard',
        config_parameter='geidea.real_time_dashboard',
        default=True,
        help='Enable real-time payment dashboard'
    )
    
    # Performance Settings
    geidea_connection_pool_size = fields.Integer(
        'Connection Pool Size',
        config_parameter='geidea.connection_pool_size',
        default=10,
        help='Maximum number of concurrent API connections'
    )
    geidea_request_timeout = fields.Integer(
        'API Request Timeout (seconds)',
        config_parameter='geidea.request_timeout',
        default=30,
        help='Timeout for API requests'
    )
    
    # Testing and Development
    geidea_test_mode = fields.Boolean(
        'Global Test Mode',
        config_parameter='geidea.test_mode',
        default=False,
        help='Enable test mode for all Geidea operations'
    )
    geidea_debug_mode = fields.Boolean(
        'Debug Mode',
        config_parameter='geidea.debug_mode',
        default=False,
        help='Enable debug mode for development'
    )
    
    @api.model
    def get_values(self):
        res = super().get_values()
        
        # Add any computed values or validation
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Ensure webhook URL is set if webhooks are enabled
        if res.get('geidea_webhook_enabled') and not res.get('geidea_webhook_url'):
            base_url = ICPSudo.get_param('web.base.url', '')
            if base_url:
                res['geidea_webhook_url'] = f"{base_url}/geidea/webhook"
        
        return res
    
    def set_values(self):
        super().set_values()
        
        # Validate configuration
        self._validate_geidea_config()
        
        # Update related models if needed
        self._update_geidea_configuration()
    
    def _validate_geidea_config(self):
        """Validate Geidea configuration settings"""
        errors = []
        
        # Validate timeouts
        if self.geidea_transaction_timeout <= 0:
            errors.append(_('Transaction timeout must be greater than 0'))
        
        if self.geidea_request_timeout <= 0:
            errors.append(_('Request timeout must be greater than 0'))
        
        # Validate retry attempts
        if self.geidea_retry_attempts < 0:
            errors.append(_('Retry attempts cannot be negative'))
        
        # Validate connection pool size
        if self.geidea_connection_pool_size <= 0:
            errors.append(_('Connection pool size must be greater than 0'))
        
        # Validate log retention
        if self.geidea_log_retention <= 0:
            errors.append(_('Log retention must be greater than 0'))
        
        # Validate device heartbeat
        if self.geidea_device_heartbeat <= 0:
            errors.append(_('Device heartbeat interval must be greater than 0'))
        
        if errors:
            raise ValidationError('\n'.join(errors))
    
    def _update_geidea_configuration(self):
        """Update related Geidea configuration when settings change"""
        # Update all active terminals with new configuration
        terminals = self.env['geidea.terminal'].search([('state', '=', 'active')])
        for terminal in terminals:
            terminal._update_from_global_config()
        
        # Update all active devices
        devices = self.env['geidea.device'].search([('is_active', '=', True)])
        for device in devices:
            if self.geidea_device_heartbeat:
                # Schedule heartbeat checks if enabled
                device._schedule_heartbeat()
    
    def action_test_geidea_connection(self):
        """Test Geidea API connection with current settings"""
        try:
            # Test connection to both environments
            test_results = []
            
            # Test production API
            if self.geidea_api_url_production:
                prod_result = self._test_api_connection(self.geidea_api_url_production, 'production')
                test_results.append(prod_result)
            
            # Test sandbox API
            if self.geidea_api_url_test:
                test_result = self._test_api_connection(self.geidea_api_url_test, 'test')
                test_results.append(test_result)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('API connection test completed. Check logs for details.'),
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('API connection test failed: %s') % str(e),
                    'type': 'danger',
                }
            }
    
    def _test_api_connection(self, api_url, environment):
        """Test connection to a specific API URL"""
        import requests
        
        try:
            response = requests.get(
                f"{api_url}/health",
                timeout=self.geidea_request_timeout,
                verify=self.geidea_ssl_verify
            )
            
            if response.status_code == 200:
                return {
                    'environment': environment,
                    'status': 'success',
                    'url': api_url
                }
            else:
                return {
                    'environment': environment,
                    'status': 'failed',
                    'url': api_url,
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            return {
                'environment': environment,
                'status': 'error',
                'url': api_url,
                'error': str(e)
            }
    
    def action_reset_geidea_config(self):
        """Reset Geidea configuration to defaults"""
        defaults = {
            'geidea.api_url_test': 'https://api-test.geidea.net/v1',
            'geidea.api_url_production': 'https://api.geidea.net/v1',
            'geidea.transaction_timeout': 30,
            'geidea.retry_attempts': 3,
            'geidea.device_heartbeat': 30,
            'geidea.connection_pool_size': 10,
            'geidea.request_timeout': 30,
            'geidea.log_retention': 90,
            'geidea.logging_level': 'INFO',
            'geidea.receipt_template': 'standard',
        }
        
        ICPSudo = self.env['ir.config_parameter'].sudo()
        for key, value in defaults.items():
            ICPSudo.set_param(key, value)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Geidea configuration reset to defaults'),
                'type': 'success',
            }
        }