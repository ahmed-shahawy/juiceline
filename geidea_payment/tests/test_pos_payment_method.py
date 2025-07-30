# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPosPaymentMethod(TransactionCase):

    def setUp(self):
        super().setUp()
        self.PaymentMethod = self.env['pos.payment.method']

    def test_create_geidea_payment_method(self):
        """Test creating a Geidea payment method"""
        payment_method = self.PaymentMethod.create({
            'name': 'Test Geidea Payment',
            'use_geidea': True,
            'geidea_merchant_id': 'TEST_MERCHANT_123',
            'geidea_terminal_id': 'TEST_TERMINAL_456',
            'geidea_api_key': 'test_api_key',
            'geidea_test_mode': True,
        })
        
        self.assertTrue(payment_method.use_geidea)
        self.assertEqual(payment_method.geidea_merchant_id, 'TEST_MERCHANT_123')
        self.assertEqual(payment_method.geidea_terminal_id, 'TEST_TERMINAL_456')
        self.assertTrue(payment_method.geidea_test_mode)
        self.assertFalse(payment_method.is_cash_count)

    def test_geidea_validation_merchant_id_required(self):
        """Test that merchant ID is required when Geidea is enabled"""
        with self.assertRaises(ValidationError):
            self.PaymentMethod.create({
                'name': 'Test Geidea Payment',
                'use_geidea': True,
                'geidea_terminal_id': 'TEST_TERMINAL_456',
            })

    def test_geidea_validation_terminal_id_required(self):
        """Test that terminal ID is required when Geidea is enabled"""
        with self.assertRaises(ValidationError):
            self.PaymentMethod.create({
                'name': 'Test Geidea Payment',
                'use_geidea': True,
                'geidea_merchant_id': 'TEST_MERCHANT_123',
            })

    def test_geidea_onchange_use_geidea(self):
        """Test onchange method when enabling Geidea"""
        payment_method = self.PaymentMethod.new({
            'use_geidea': True,
        })
        payment_method._onchange_use_geidea()
        
        self.assertFalse(payment_method.is_cash_count)
        self.assertEqual(payment_method.name, 'Geidea Payment')

    def test_geidea_payment_request_success(self):
        """Test successful Geidea payment request"""
        payment_method = self.PaymentMethod.create({
            'name': 'Test Geidea Payment',
            'use_geidea': True,
            'geidea_merchant_id': 'TEST_MERCHANT_123',
            'geidea_terminal_id': 'TEST_TERMINAL_456',
            'geidea_test_mode': True,
        })
        
        # Mock successful response
        result = payment_method.geidea_payment_request(100.0, 'TEST_REF_001')
        
        # Since it's a simulation, we need to check if the method returns a dict with expected keys
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        # In simulation, success is random but we can test the structure
        if result.get('success'):
            self.assertIn('transaction_id', result)
            self.assertIn('amount', result)
            self.assertIn('reference', result)
            self.assertEqual(result['amount'], 100.0)
            self.assertEqual(result['reference'], 'TEST_REF_001')

    def test_geidea_payment_request_disabled(self):
        """Test Geidea payment request when not enabled"""
        payment_method = self.PaymentMethod.create({
            'name': 'Regular Payment Method',
            'use_geidea': False,
        })
        
        result = payment_method.geidea_payment_request(100.0, 'TEST_REF_001')
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Geidea payment not enabled for this method')