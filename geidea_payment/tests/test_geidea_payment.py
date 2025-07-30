# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestGeideaPayment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.GeideaPayment = self.env['geidea.payment']
        self.PaymentMethod = self.env['pos.payment.method']
        
        # Create a test payment method
        self.payment_method = self.PaymentMethod.create({
            'name': 'Test Geidea Payment',
            'use_geidea': True,
            'geidea_merchant_id': 'TEST_MERCHANT_123',
            'geidea_terminal_id': 'TEST_TERMINAL_456',
        })

    def test_create_geidea_transaction(self):
        """Test creating a Geidea payment transaction"""
        transaction = self.GeideaPayment.create_transaction({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'reference': 'ORDER_001',
        })
        
        self.assertEqual(transaction.transaction_id, 'GDA123456789')
        self.assertEqual(transaction.amount, 150.0)
        self.assertEqual(transaction.state, 'pending')
        self.assertEqual(transaction.payment_method_id, self.payment_method)

    def test_mark_transaction_success(self):
        """Test marking transaction as successful"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'state': 'pending',
        })
        
        response_data = '{"status": "success", "auth_code": "AUTH123"}'
        transaction.mark_success(response_data)
        
        self.assertEqual(transaction.state, 'success')
        self.assertEqual(transaction.response_data, response_data)

    def test_mark_transaction_failed(self):
        """Test marking transaction as failed"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'state': 'pending',
        })
        
        error_message = 'Payment declined by bank'
        response_data = '{"status": "failed", "error_code": "DECLINED"}'
        transaction.mark_failed(error_message, response_data)
        
        self.assertEqual(transaction.state, 'failed')
        self.assertEqual(transaction.error_message, error_message)
        self.assertEqual(transaction.response_data, response_data)

    def test_cancel_transaction_pending(self):
        """Test cancelling a pending transaction"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'state': 'pending',
        })
        
        transaction.cancel_transaction()
        self.assertEqual(transaction.state, 'cancelled')

    def test_cancel_transaction_failed(self):
        """Test cancelling a failed transaction"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'state': 'failed',
        })
        
        transaction.cancel_transaction()
        self.assertEqual(transaction.state, 'cancelled')

    def test_cancel_successful_transaction_raises_error(self):
        """Test that cancelling a successful transaction raises an error"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
            'state': 'success',
        })
        
        with self.assertRaises(UserError):
            transaction.cancel_transaction()

    def test_transaction_rec_name(self):
        """Test transaction record name"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
        })
        
        self.assertEqual(transaction.display_name, 'GDA123456789')

    def test_transaction_default_currency(self):
        """Test transaction default currency"""
        transaction = self.GeideaPayment.create({
            'transaction_id': 'GDA123456789',
            'amount': 150.0,
            'payment_method_id': self.payment_method.id,
        })
        
        self.assertEqual(transaction.currency_id, self.env.company.currency_id)