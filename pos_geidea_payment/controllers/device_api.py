from odoo import http, _
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class GeideaDeviceController(http.Controller):
    
    @http.route('/geidea/device/discover', type='json', auth='user')
    def discover_devices(self, **post):
        """Discover available Geidea devices"""
        try:
            data = json.loads(request.httprequest.data) if request.httprequest.data else {}
            platform = data.get('platform')
            
            device_model = request.env['geidea.device'].sudo()
            discovered_devices = device_model.discover_devices(platform)
            
            return {
                'success': True,
                'devices': discovered_devices,
                'platform': platform or device_model._detect_platform()
            }
        except Exception as e:
            _logger.error("Device discovery error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/connect', type='json', auth='user')
    def connect_device(self, **post):
        """Connect to a specific device"""
        try:
            data = json.loads(request.httprequest.data)
            device_id = data.get('device_id')
            
            if not device_id:
                return {'success': False, 'error': _('Device ID is required')}
            
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id)
            ], limit=1)
            
            if not device:
                return {'success': False, 'error': _('Device not found')}
            
            success = device.action_connect()
            
            return {
                'success': success,
                'device_state': device.state,
                'message': _('Device connected successfully') if success else _('Failed to connect')
            }
        except Exception as e:
            _logger.error("Device connection error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/disconnect', type='json', auth='user')
    def disconnect_device(self, **post):
        """Disconnect from a specific device"""
        try:
            data = json.loads(request.httprequest.data)
            device_id = data.get('device_id')
            
            if not device_id:
                return {'success': False, 'error': _('Device ID is required')}
            
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id)
            ], limit=1)
            
            if not device:
                return {'success': False, 'error': _('Device not found')}
            
            success = device.action_disconnect()
            
            return {
                'success': success,
                'device_state': device.state,
                'message': _('Device disconnected') if success else _('Failed to disconnect')
            }
        except Exception as e:
            _logger.error("Device disconnection error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/status', type='json', auth='user')
    def get_device_status(self, **post):
        """Get status of all connected devices"""
        try:
            devices = request.env['geidea.device'].sudo().search([
                ('is_active', '=', True)
            ])
            
            device_status = []
            for device in devices:
                device_status.append({
                    'device_id': device.device_id,
                    'name': device.name,
                    'state': device.state,
                    'platform': device.platform,
                    'connection_type': device.connection_type,
                    'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                    'success_rate': device.success_rate,
                    'transaction_count': device.transaction_count
                })
            
            return {
                'success': True,
                'devices': device_status,
                'total_devices': len(device_status)
            }
        except Exception as e:
            _logger.error("Device status error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/test', type='json', auth='user')
    def test_device(self, **post):
        """Test device functionality"""
        try:
            data = json.loads(request.httprequest.data)
            device_id = data.get('device_id')
            
            if not device_id:
                return {'success': False, 'error': _('Device ID is required')}
            
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id)
            ], limit=1)
            
            if not device:
                return {'success': False, 'error': _('Device not found')}
            
            test_result = device._run_device_test()
            
            return {
                'success': True,
                'test_result': test_result,
                'device_state': device.state
            }
        except Exception as e:
            _logger.error("Device test error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/heartbeat', type='json', auth='user')
    def device_heartbeat(self, **post):
        """Update device heartbeat"""
        try:
            data = json.loads(request.httprequest.data)
            device_id = data.get('device_id')
            
            if not device_id:
                return {'success': False, 'error': _('Device ID is required')}
            
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id)
            ], limit=1)
            
            if not device:
                return {'success': False, 'error': _('Device not found')}
            
            device.update_heartbeat()
            
            return {
                'success': True,
                'last_heartbeat': device.last_heartbeat.isoformat() if device.last_heartbeat else None,
                'device_state': device.state
            }
        except Exception as e:
            _logger.error("Device heartbeat error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/configure', type='json', auth='user')
    def configure_device(self, **post):
        """Configure device connection parameters"""
        try:
            data = json.loads(request.httprequest.data)
            device_id = data.get('device_id')
            config = data.get('config', {})
            
            if not device_id:
                return {'success': False, 'error': _('Device ID is required')}
            
            device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', device_id)
            ], limit=1)
            
            if not device:
                return {'success': False, 'error': _('Device not found')}
            
            device.set_connection_config(config)
            
            return {
                'success': True,
                'message': _('Device configuration updated'),
                'config': device._get_connection_config()
            }
        except Exception as e:
            _logger.error("Device configuration error: %s", str(e))
            return {'success': False, 'error': str(e)}
    
    @http.route('/geidea/device/register', type='json', auth='user')
    def register_device(self, **post):
        """Register a new device"""
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['device_id', 'name', 'platform', 'connection_type']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return {
                    'success': False, 
                    'error': _('Missing required fields: %s') % ', '.join(missing_fields)
                }
            
            # Check if device already exists
            existing_device = request.env['geidea.device'].sudo().search([
                ('device_id', '=', data['device_id'])
            ], limit=1)
            
            if existing_device:
                return {'success': False, 'error': _('Device already registered')}
            
            # Create new device
            device_vals = {
                'name': data['name'],
                'device_id': data['device_id'],
                'platform': data['platform'],
                'connection_type': data['connection_type'],
                'device_type': data.get('device_type', 'pos_terminal'),
                'manufacturer': data.get('manufacturer'),
                'model': data.get('model'),
                'device_serial': data.get('serial_number'),
                'connection_config': json.dumps(data.get('config', {})),
            }
            
            device = request.env['geidea.device'].sudo().create(device_vals)
            
            return {
                'success': True,
                'device_id': device.id,
                'message': _('Device registered successfully')
            }
        except Exception as e:
            _logger.error("Device registration error: %s", str(e))
            return {'success': False, 'error': str(e)}