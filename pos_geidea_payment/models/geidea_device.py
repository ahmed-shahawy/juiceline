from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class GeideaDevice(models.Model):
    _name = 'geidea.device'
    _description = 'Geidea Payment Device'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Device Name', required=True, tracking=True)
    device_id = fields.Char('Device ID', required=True, tracking=True)
    device_serial = fields.Char('Serial Number', tracking=True)
    
    # Platform and Device Type
    platform = fields.Selection([
        ('windows', 'Windows'),
        ('ios', 'iOS/iPad'),
        ('android', 'Android'),
        ('web', 'Web Browser'),
        ('unknown', 'Unknown')
    ], required=True, default='unknown', tracking=True)
    
    device_type = fields.Selection([
        ('pos_terminal', 'POS Terminal'),
        ('mobile_reader', 'Mobile Card Reader'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
        ('virtual', 'Virtual Terminal')
    ], required=True, default='pos_terminal', tracking=True)
    
    # Connection Methods
    connection_type = fields.Selection([
        ('usb', 'USB'),
        ('serial', 'Serial/COM Port'),
        ('bluetooth', 'Bluetooth'),
        ('wifi', 'WiFi/Network'),
        ('lightning', 'Lightning (iOS)'),
        ('usb_otg', 'USB OTG (Android)'),
        ('websocket', 'WebSocket'),
        ('virtual', 'Virtual Connection')
    ], required=True, default='usb', tracking=True)
    
    connection_config = fields.Text(
        'Connection Configuration',
        help='JSON configuration for device connection parameters'
    )
    
    # Status and State
    state = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online'),
        ('busy', 'Busy'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance')
    ], default='offline', tracking=True)
    
    is_active = fields.Boolean('Active', default=True, tracking=True)
    last_seen = fields.Datetime('Last Seen')
    last_heartbeat = fields.Datetime('Last Heartbeat')
    
    # Device Capabilities
    supports_contactless = fields.Boolean('Supports Contactless', default=True)
    supports_chip = fields.Boolean('Supports Chip & PIN', default=True)
    supports_magnetic = fields.Boolean('Supports Magnetic Stripe', default=True)
    supports_manual = fields.Boolean('Supports Manual Entry', default=False)
    
    # Security Features
    encryption_support = fields.Boolean('Encryption Support', default=True)
    pin_verification = fields.Boolean('PIN Verification', default=True)
    signature_support = fields.Boolean('Signature Support', default=False)
    
    # Terminal Association
    terminal_id = fields.Many2one(
        'geidea.terminal',
        string='Associated Terminal',
        ondelete='cascade'
    )
    
    # Device Specifications
    manufacturer = fields.Char('Manufacturer')
    model = fields.Char('Model')
    firmware_version = fields.Char('Firmware Version')
    software_version = fields.Char('Software Version')
    
    # Performance Metrics
    transaction_count = fields.Integer(
        compute='_compute_device_stats',
        string='Transaction Count'
    )
    success_rate = fields.Float(
        compute='_compute_device_stats',
        string='Success Rate (%)'
    )
    average_response_time = fields.Float(
        compute='_compute_device_stats',
        string='Avg Response Time (s)'
    )
    uptime_percentage = fields.Float(
        compute='_compute_uptime',
        string='Uptime (%)'
    )
    
    # Maintenance
    last_maintenance = fields.Datetime('Last Maintenance')
    next_maintenance = fields.Datetime('Next Maintenance')
    maintenance_notes = fields.Text('Maintenance Notes')
    
    @api.constrains('device_id')
    def _check_device_id(self):
        for device in self:
            if self.search_count([
                ('device_id', '=', device.device_id),
                ('id', '!=', device.id)
            ]):
                raise ValidationError(_('Device ID must be unique!'))
    
    @api.depends('terminal_id.transaction_ids')
    def _compute_device_stats(self):
        for device in self:
            if device.terminal_id:
                transactions = device.terminal_id.transaction_ids.filtered(
                    lambda t: t.device_id == device.id
                )
                device.transaction_count = len(transactions)
                
                if transactions:
                    successful = transactions.filtered(lambda t: t.state == 'completed')
                    device.success_rate = (len(successful) / len(transactions)) * 100
                    
                    # Calculate average response time (mock calculation)
                    device.average_response_time = 2.5  # This would be calculated from actual data
                else:
                    device.success_rate = 0.0
                    device.average_response_time = 0.0
            else:
                device.transaction_count = 0
                device.success_rate = 0.0
                device.average_response_time = 0.0
    
    @api.depends('last_seen', 'state')
    def _compute_uptime(self):
        for device in self:
            if device.last_seen:
                # Calculate uptime based on when device was last seen
                now = fields.Datetime.now()
                last_24h = now - timedelta(hours=24)
                
                if device.last_seen >= last_24h and device.state == 'online':
                    # Simplified uptime calculation
                    device.uptime_percentage = 95.0  # This would be calculated from actual data
                else:
                    device.uptime_percentage = 0.0
            else:
                device.uptime_percentage = 0.0
    
    def action_connect(self):
        """Attempt to connect to the device"""
        self.ensure_one()
        try:
            connection_result = self._establish_connection()
            if connection_result:
                self.write({
                    'state': 'online',
                    'last_seen': fields.Datetime.now(),
                    'last_heartbeat': fields.Datetime.now()
                })
                self.message_post(body=_("Device connected successfully"))
                return True
            else:
                self.state = 'error'
                self.message_post(body=_("Failed to connect to device"))
                return False
        except Exception as e:
            self.state = 'error'
            self.message_post(body=_("Connection error: %s") % str(e))
            return False
    
    def action_disconnect(self):
        """Disconnect from the device"""
        self.ensure_one()
        try:
            self._close_connection()
            self.write({
                'state': 'offline',
                'last_seen': fields.Datetime.now()
            })
            self.message_post(body=_("Device disconnected"))
            return True
        except Exception as e:
            self.message_post(body=_("Disconnection error: %s") % str(e))
            return False
    
    def action_test_device(self):
        """Test device functionality"""
        self.ensure_one()
        try:
            test_result = self._run_device_test()
            if test_result.get('success'):
                self.message_post(body=_("Device test successful"))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Device test successful!'),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_("Device test failed: %s") % test_result.get('error'))
        except Exception as e:
            raise UserError(_("Device test failed: %s") % str(e))
    
    def update_heartbeat(self):
        """Update device heartbeat"""
        self.ensure_one()
        self.write({
            'last_heartbeat': fields.Datetime.now(),
            'last_seen': fields.Datetime.now()
        })
        if self.state == 'offline':
            self.state = 'online'
    
    def _establish_connection(self):
        """Platform-specific connection establishment"""
        connection_config = self._get_connection_config()
        
        if self.platform == 'windows':
            return self._connect_windows(connection_config)
        elif self.platform == 'ios':
            return self._connect_ios(connection_config)
        elif self.platform == 'android':
            return self._connect_android(connection_config)
        elif self.platform == 'web':
            return self._connect_web(connection_config)
        else:
            return self._connect_generic(connection_config)
    
    def _connect_windows(self, config):
        """Windows-specific connection logic"""
        if self.connection_type == 'serial':
            # Connect via COM port
            port = config.get('port', 'COM1')
            baudrate = config.get('baudrate', 9600)
            _logger.info(f"Connecting to Windows device via {port} at {baudrate}")
            return True
        elif self.connection_type == 'usb':
            # Connect via USB
            vendor_id = config.get('vendor_id')
            product_id = config.get('product_id')
            _logger.info(f"Connecting to Windows USB device {vendor_id}:{product_id}")
            return True
        elif self.connection_type == 'wifi':
            return self._connect_network(config)
        return False
    
    def _connect_ios(self, config):
        """iOS/iPad specific connection logic"""
        if self.connection_type == 'bluetooth':
            # Connect via Bluetooth
            device_uuid = config.get('device_uuid')
            _logger.info(f"Connecting to iOS device via Bluetooth: {device_uuid}")
            return True
        elif self.connection_type == 'lightning':
            # Connect via Lightning port
            _logger.info("Connecting to iOS device via Lightning")
            return True
        elif self.connection_type == 'wifi':
            return self._connect_network(config)
        return False
    
    def _connect_android(self, config):
        """Android-specific connection logic"""
        if self.connection_type == 'usb_otg':
            # Connect via USB OTG
            _logger.info("Connecting to Android device via USB OTG")
            return True
        elif self.connection_type == 'bluetooth':
            # Connect via Bluetooth
            mac_address = config.get('mac_address')
            _logger.info(f"Connecting to Android device via Bluetooth: {mac_address}")
            return True
        elif self.connection_type == 'wifi':
            return self._connect_network(config)
        return False
    
    def _connect_web(self, config):
        """Web browser connection logic"""
        if self.connection_type == 'websocket':
            # Connect via WebSocket
            ws_url = config.get('websocket_url')
            _logger.info(f"Connecting to web device via WebSocket: {ws_url}")
            return True
        return False
    
    def _connect_network(self, config):
        """Network connection logic"""
        ip_address = config.get('ip_address')
        port = config.get('port', 8080)
        _logger.info(f"Connecting to device via network: {ip_address}:{port}")
        return True
    
    def _connect_generic(self, config):
        """Generic connection fallback"""
        _logger.info("Connecting using generic connection method")
        return True
    
    def _close_connection(self):
        """Close device connection"""
        _logger.info(f"Closing connection to device {self.name}")
        return True
    
    def _run_device_test(self):
        """Run device functionality test"""
        # Simulate a device test
        return {
            'success': True,
            'response_time': 150,  # ms
            'capabilities': {
                'contactless': self.supports_contactless,
                'chip': self.supports_chip,
                'magnetic': self.supports_magnetic
            }
        }
    
    def _get_connection_config(self):
        """Parse connection configuration JSON"""
        try:
            return json.loads(self.connection_config) if self.connection_config else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_connection_config(self, config_dict):
        """Set connection configuration from dictionary"""
        self.connection_config = json.dumps(config_dict, indent=2)
    
    @api.model
    def discover_devices(self, platform=None):
        """Discover available devices on the specified platform"""
        discovered_devices = []
        
        if not platform:
            # Auto-detect platform
            platform = self._detect_platform()
        
        if platform == 'windows':
            discovered_devices.extend(self._discover_windows_devices())
        elif platform == 'ios':
            discovered_devices.extend(self._discover_ios_devices())
        elif platform == 'android':
            discovered_devices.extend(self._discover_android_devices())
        elif platform == 'web':
            discovered_devices.extend(self._discover_web_devices())
        
        return discovered_devices
    
    def _detect_platform(self):
        """Detect current platform"""
        # This would be called from frontend with actual platform detection
        return 'web'
    
    def _discover_windows_devices(self):
        """Discover Windows devices"""
        # Mock discovery - would use actual Windows APIs
        return [
            {
                'name': 'Geidea Terminal COM1',
                'device_id': 'WIN_COM1_001',
                'connection_type': 'serial',
                'config': {'port': 'COM1', 'baudrate': 9600}
            }
        ]
    
    def _discover_ios_devices(self):
        """Discover iOS devices"""
        # Mock discovery - would use actual iOS APIs
        return [
            {
                'name': 'Geidea Mobile Reader',
                'device_id': 'IOS_BT_001',
                'connection_type': 'bluetooth',
                'config': {'device_uuid': 'ABC123-DEF456'}
            }
        ]
    
    def _discover_android_devices(self):
        """Discover Android devices"""
        # Mock discovery - would use actual Android APIs
        return [
            {
                'name': 'Geidea USB Reader',
                'device_id': 'AND_USB_001',
                'connection_type': 'usb_otg',
                'config': {}
            }
        ]
    
    def _discover_web_devices(self):
        """Discover web-based devices"""
        return [
            {
                'name': 'Virtual Geidea Terminal',
                'device_id': 'WEB_VIRTUAL_001',
                'connection_type': 'websocket',
                'config': {'websocket_url': 'wss://localhost:8080'}
            }
        ]