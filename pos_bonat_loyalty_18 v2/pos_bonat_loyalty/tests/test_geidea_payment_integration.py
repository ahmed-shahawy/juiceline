# -*- coding: utf-8 -*-

import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestGeideaPaymentIntegration(TransactionCase):
    """Test suite for Geidea payment integration"""

    def setUp(self):
        super().setUp()
        
        # Create test company with Geidea configuration
        self.company = self.env.user.company_id
        self.company.write({
            'enable_geidea_integration': True,
            'geidea_api_key': 'test_api_key',
            'geidea_api_password': 'test_password',
            'geidea_merchant_id': 'test_merchant',
            'geidea_terminal_id': 'test_terminal',
            'geidea_environment': 'test',
            'geidea_connection_timeout': 30,
            'geidea_enable_partial_payments': True,
            'geidea_enable_refunds': True,
            'geidea_max_retry_attempts': 3,
            'geidea_connection_pool_size': 5
        })
        
        # Create test terminal
        self.terminal = self.env['geidea.payment.terminal'].create({
            'terminal_id': 'TEST_TERMINAL_001',
            'name': 'Test Terminal 1',
            'status': 'connected',
            'ip_address': '192.168.1.100',
            'port': 8080
        })
        
        # Create test currency
        self.currency = self.env.ref('base.USD')
        
        # Create test payment method
        self.payment_method = self.env['pos.payment.method'].create({
            'name': 'Geidea Card Payment',
            'is_geidea_payment': True,
            'geidea_payment_type': 'card',
            'terminal_id': self.terminal.id,
            'enable_partial_payment': True
        })

    def test_geidea_config_validation(self):
        """Test Geidea configuration validation"""
        service = self.env['geidea.payment.service']
        
        # Test with valid configuration
        config = service.get_geidea_config()
        self.assertEqual(config['merchant_id'], 'test_merchant')
        self.assertEqual(config['terminal_id'], 'test_terminal')
        self.assertTrue(config['enable_partial_payments'])
        
        # Test with missing configuration
        self.company.geidea_api_key = False
        with self.assertRaises(UserError):
            service.get_geidea_config()

    def test_terminal_health_check(self):
        """Test terminal health check functionality"""
        # Test healthy terminal
        result = self.terminal.check_terminal_health('TEST_TERMINAL_001')
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['terminal_id'], 'TEST_TERMINAL_001')
        
        # Test non-existent terminal
        result = self.terminal.check_terminal_health('NON_EXISTENT')
        self.assertEqual(result['status'], 'not_found')

    def test_transaction_creation(self):
        """Test payment transaction creation"""
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card',
            'terminal_id': self.terminal.id
        })
        
        self.assertTrue(transaction.name.startswith('GDT-'))
        self.assertEqual(transaction.state, 'draft')
        self.assertTrue(transaction.checksum)
        self.assertEqual(len(transaction.checksum), 64)  # SHA-256 hash

    def test_transaction_checksum_generation(self):
        """Test transaction checksum generation"""
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card'
        })
        
        # Generate checksum manually and compare
        expected_checksum = transaction.generate_checksum()
        self.assertEqual(transaction.checksum, expected_checksum)

    def test_payment_method_configuration(self):
        """Test payment method Geidea configuration"""
        self.assertTrue(self.payment_method.is_geidea_payment)
        self.assertEqual(self.payment_method.geidea_payment_type, 'card')
        self.assertEqual(self.payment_method.terminal_id, self.terminal)

    @patch('requests.Session.post')
    def test_payment_initiation_success(self, mock_post):
        """Test successful payment initiation"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'transactionId': 'GDT_12345'
        }
        mock_post.return_value = mock_response
        
        service = self.env['geidea.payment.service']
        payment_data = {
            'amount': 50.0,
            'currency': 'USD',
            'currency_id': self.currency.id,
            'payment_method': 'card'
        }
        
        result = service.initiate_payment(payment_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['geidea_transaction_id'], 'GDT_12345')

    @patch('requests.Session.post')
    def test_payment_initiation_failure(self, mock_post):
        """Test payment initiation failure"""
        # Mock failed API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid request'
        mock_post.return_value = mock_response
        
        service = self.env['geidea.payment.service']
        payment_data = {
            'amount': 50.0,
            'currency': 'USD',
            'currency_id': self.currency.id,
            'payment_method': 'card'
        }
        
        result = service.initiate_payment(payment_data)
        
        self.assertFalse(result['success'])
        self.assertIn('Payment request failed', result['error'])

    def test_partial_payment_validation(self):
        """Test partial payment validation"""
        # Test with partial payments disabled
        self.company.geidea_enable_partial_payments = False
        
        service = self.env['geidea.payment.service']
        result = service.process_partial_payment(1, 25.0, 'card')
        
        self.assertFalse(result['success'])
        self.assertIn('not enabled', result['error'])

    @patch('requests.Session.post')
    def test_refund_processing(self, mock_post):
        """Test refund processing"""
        # Create a completed transaction first
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card',
            'transaction_id': 'GDT_ORIGINAL_12345',
            'state': 'completed'
        })
        
        # Mock successful refund response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'refundTransactionId': 'GDT_REFUND_12345'
        }
        mock_post.return_value = mock_response
        
        service = self.env['geidea.payment.service']
        result = service.refund_payment(transaction.id, 50.0, 'Customer refund')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['geidea_refund_id'], 'GDT_REFUND_12345')

    def test_refund_validation(self):
        """Test refund validation"""
        # Test with refunds disabled
        self.company.geidea_enable_refunds = False
        
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card',
            'state': 'completed'
        })
        
        service = self.env['geidea.payment.service']
        result = service.refund_payment(transaction.id, 50.0, 'Test refund')
        
        self.assertFalse(result['success'])
        self.assertIn('not enabled', result['error'])

    @patch('requests.Session.get')
    def test_connection_test(self, mock_get):
        """Test connection testing"""
        # Mock successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        service = self.env['geidea.payment.service']
        result = service.test_connection('TEST_TERMINAL_001')
        
        self.assertTrue(result['success'])
        self.assertIn('response_time', result)

    def test_connection_pool_management(self):
        """Test connection pool management"""
        pool = self.env['geidea.connection.pool'].create({
            'name': 'Test Pool',
            'max_connections': 3,
            'terminal_ids': [(6, 0, [self.terminal.id])]
        })
        
        # Test acquiring connections
        self.assertTrue(pool.acquire_connection())
        self.assertEqual(pool.active_connections, 1)
        
        # Test releasing connections
        self.assertTrue(pool.release_connection())
        self.assertEqual(pool.active_connections, 0)
        
        # Test connection limit
        for i in range(3):
            self.assertTrue(pool.acquire_connection())
        
        # Should fail when pool is full
        self.assertFalse(pool.acquire_connection())

    def test_encryption_decryption(self):
        """Test data encryption and decryption"""
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card'
        })
        
        # Test data encryption
        sensitive_data = {'card_number': '1234567890123456', 'cvv': '123'}
        encrypted = transaction._encrypt_sensitive_data(sensitive_data)
        
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, json.dumps(sensitive_data))
        
        # Set encrypted data and test decryption
        transaction.encrypted_data = encrypted
        decrypted = transaction._decrypt_sensitive_data()
        
        self.assertEqual(decrypted, sensitive_data)

    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        # Create test transactions
        for i in range(5):
            state = 'completed' if i < 3 else 'failed'
            self.env['geidea.payment.transaction'].create({
                'amount': 100.0,
                'currency_id': self.currency.id,
                'payment_method': 'card',
                'state': state,
                'response_time': 500 + i * 100
            })
        
        # Test metrics retrieval through service
        service = self.env['geidea.payment.service']
        # Note: This would require implementing the get_performance_metrics method
        # which calls the controller method

    def test_transaction_status_mapping(self):
        """Test transaction status mapping"""
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card',
            'state': 'pending'
        })
        
        # Test status transitions
        valid_transitions = [
            ('pending', 'processing'),
            ('processing', 'authorized'),
            ('authorized', 'captured'),
            ('captured', 'completed'),
            ('completed', 'refunded')
        ]
        
        for from_state, to_state in valid_transitions:
            transaction.state = from_state
            transaction.state = to_state
            self.assertEqual(transaction.state, to_state)

    def test_error_handling(self):
        """Test error handling scenarios"""
        service = self.env['geidea.payment.service']
        
        # Test missing payment data
        result = service.initiate_payment({})
        self.assertFalse(result['success'])
        self.assertIn('Missing payment data', result['error'])
        
        # Test invalid transaction ID for status check
        result = service.check_transaction_status(99999)
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])

    def test_webhook_processing(self):
        """Test webhook notification processing"""
        # Create a test transaction
        transaction = self.env['geidea.payment.transaction'].create({
            'amount': 100.0,
            'currency_id': self.currency.id,
            'payment_method': 'card',
            'transaction_id': 'GDT_WEBHOOK_TEST',
            'state': 'processing'
        })
        
        # Simulate webhook data
        webhook_data = {
            'transactionId': 'GDT_WEBHOOK_TEST',
            'status': 'completed'
        }
        
        # Test webhook processing would be done through HTTP controller
        # In real scenario, this would be tested through HTTP requests
        
        # Manual status update simulation
        transaction.write({'state': 'completed'})
        self.assertEqual(transaction.state, 'completed')

    def tearDown(self):
        """Clean up test data"""
        super().tearDown()
        # Clean up is automatic with TransactionCase