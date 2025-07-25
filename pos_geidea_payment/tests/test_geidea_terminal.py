# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import exceptions
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestGeideaTerminal(common.TransactionCase):
    """Test cases for Geidea Terminal tree view and CRUD operations."""

    def setUp(self):
        super().setUp()
        self.geidea_terminal_model = self.env['geidea.terminal']
        self.pos_config_model = self.env['pos.config']
        
        # Create a test POS config for terminal association
        self.pos_config = self.pos_config_model.create({
            'name': 'Test POS Config',
        })

    def test_01_geidea_terminal_create(self):
        """Test creating a Geidea terminal with required fields."""
        terminal_data = {
            'name': 'Test Terminal',
            'terminal_id': 'TEST001',
            'merchant_id': 'MERCHANT001',
            'api_key': 'test_api_key_123',
            'pos_config_ids': [(6, 0, [self.pos_config.id])]
        }
        
        terminal = self.geidea_terminal_model.create(terminal_data)
        
        # Verify terminal creation
        self.assertTrue(terminal.id)
        self.assertEqual(terminal.name, 'Test Terminal')
        self.assertEqual(terminal.terminal_id, 'TEST001')
        self.assertEqual(terminal.merchant_id, 'MERCHANT001')
        self.assertEqual(terminal.api_key, 'test_api_key_123')
        self.assertEqual(terminal.state, 'draft')
        self.assertTrue(terminal.encryption_key)  # Should be auto-generated
        
        # Verify POS config association
        self.assertIn(self.pos_config, terminal.pos_config_ids)

    def test_02_required_fields_validation(self):
        """Test that required fields are properly validated."""
        # Test missing name
        with self.assertRaises(exceptions.ValidationError):
            self.geidea_terminal_model.create({
                'terminal_id': 'TEST002',
                'merchant_id': 'MERCHANT002',
                'api_key': 'test_api_key_456',
            })
        
        # Test missing terminal_id
        with self.assertRaises(exceptions.ValidationError):
            self.geidea_terminal_model.create({
                'name': 'Test Terminal 2',
                'merchant_id': 'MERCHANT002',
                'api_key': 'test_api_key_456',
            })
        
        # Test missing merchant_id
        with self.assertRaises(exceptions.ValidationError):
            self.geidea_terminal_model.create({
                'name': 'Test Terminal 2',
                'terminal_id': 'TEST002',
                'api_key': 'test_api_key_456',
            })
        
        # Test missing api_key
        with self.assertRaises(exceptions.ValidationError):
            self.geidea_terminal_model.create({
                'name': 'Test Terminal 2',
                'terminal_id': 'TEST002',
                'merchant_id': 'MERCHANT002',
            })

    def test_03_unique_terminal_id_constraint(self):
        """Test that terminal_id must be unique."""
        # Create first terminal
        self.geidea_terminal_model.create({
            'name': 'Test Terminal 1',
            'terminal_id': 'UNIQUE001',
            'merchant_id': 'MERCHANT001',
            'api_key': 'test_api_key_123',
        })
        
        # Try to create second terminal with same terminal_id
        with self.assertRaises(ValidationError):
            self.geidea_terminal_model.create({
                'name': 'Test Terminal 2',
                'terminal_id': 'UNIQUE001',  # Same as first terminal
                'merchant_id': 'MERCHANT002',
                'api_key': 'test_api_key_456',
            })

    def test_04_tree_view_fields_display(self):
        """Test that all required fields are displayed in tree view."""
        # Create a terminal for testing
        terminal = self.geidea_terminal_model.create({
            'name': 'Tree View Test Terminal',
            'terminal_id': 'TREE001',
            'merchant_id': 'MERCHANT_TREE',
            'api_key': 'tree_api_key_123',
            'state': 'active',
            'last_sync': '2024-01-15 10:00:00'
        })
        
        # Get the tree view
        tree_view = self.env.ref('pos_geidea_payment.view_geidea_terminal_tree')
        self.assertTrue(tree_view)
        self.assertEqual(tree_view.model, 'geidea.terminal')
        self.assertEqual(tree_view.type, 'tree')
        
        # Verify tree view contains the required fields
        tree_arch = tree_view.arch
        self.assertIn('name', tree_arch)
        self.assertIn('terminal_id', tree_arch)
        self.assertIn('merchant_id', tree_arch)
        self.assertIn('state', tree_arch)
        self.assertIn('last_sync', tree_arch)

    def test_05_terminal_state_management(self):
        """Test terminal state transitions."""
        terminal = self.geidea_terminal_model.create({
            'name': 'State Test Terminal',
            'terminal_id': 'STATE001',
            'merchant_id': 'MERCHANT_STATE',
            'api_key': 'state_api_key_123',
        })
        
        # Initial state should be draft
        self.assertEqual(terminal.state, 'draft')
        
        # Test state changes
        terminal.state = 'active'
        self.assertEqual(terminal.state, 'active')
        
        terminal.state = 'inactive'
        self.assertEqual(terminal.state, 'inactive')
        
        terminal.state = 'error'
        self.assertEqual(terminal.state, 'error')

    def test_06_computed_fields(self):
        """Test computed fields: transaction_count and success_rate."""
        terminal = self.geidea_terminal_model.create({
            'name': 'Computed Fields Test Terminal',
            'terminal_id': 'COMP001',
            'merchant_id': 'MERCHANT_COMP',
            'api_key': 'comp_api_key_123',
        })
        
        # Initially no transactions
        self.assertEqual(terminal.transaction_count, 0)
        self.assertEqual(terminal.success_rate, 0.0)
        
        # Create test transactions
        geidea_transaction_model = self.env['geidea.transaction']
        
        # Create successful transaction
        geidea_transaction_model.create({
            'name': 'TRANS001',
            'terminal_id': terminal.id,
            'amount': 100.0,
            'currency_id': self.env.company.currency_id.id,
            'state': 'completed'
        })
        
        # Create failed transaction
        geidea_transaction_model.create({
            'name': 'TRANS002',
            'terminal_id': terminal.id,
            'amount': 50.0,
            'currency_id': self.env.company.currency_id.id,
            'state': 'failed'
        })
        
        # Refresh computed fields
        terminal._compute_transaction_count()
        terminal._compute_success_rate()
        
        # Verify computed fields
        self.assertEqual(terminal.transaction_count, 2)
        self.assertEqual(terminal.success_rate, 50.0)  # 1 out of 2 successful

    def test_07_crud_operations(self):
        """Test complete CRUD operations."""
        # CREATE
        terminal_data = {
            'name': 'CRUD Test Terminal',
            'terminal_id': 'CRUD001',
            'merchant_id': 'MERCHANT_CRUD',
            'api_key': 'crud_api_key_123',
        }
        terminal = self.geidea_terminal_model.create(terminal_data)
        self.assertTrue(terminal.id)
        
        # READ
        read_terminal = self.geidea_terminal_model.browse(terminal.id)
        self.assertEqual(read_terminal.name, 'CRUD Test Terminal')
        self.assertEqual(read_terminal.terminal_id, 'CRUD001')
        
        # UPDATE
        read_terminal.write({
            'name': 'Updated CRUD Terminal',
            'state': 'active'
        })
        self.assertEqual(read_terminal.name, 'Updated CRUD Terminal')
        self.assertEqual(read_terminal.state, 'active')
        
        # DELETE
        terminal_id = read_terminal.id
        read_terminal.unlink()
        deleted_terminal = self.geidea_terminal_model.search([('id', '=', terminal_id)])
        self.assertFalse(deleted_terminal)

    def test_08_search_and_filtering(self):
        """Test search functionality and filtering."""
        # Create test terminals with different states
        active_terminal = self.geidea_terminal_model.create({
            'name': 'Active Terminal',
            'terminal_id': 'ACTIVE001',
            'merchant_id': 'MERCHANT_ACTIVE',
            'api_key': 'active_api_key',
            'state': 'active'
        })
        
        inactive_terminal = self.geidea_terminal_model.create({
            'name': 'Inactive Terminal',
            'terminal_id': 'INACTIVE001',
            'merchant_id': 'MERCHANT_INACTIVE',
            'api_key': 'inactive_api_key',
            'state': 'inactive'
        })
        
        # Test search by state
        active_terminals = self.geidea_terminal_model.search([('state', '=', 'active')])
        self.assertIn(active_terminal, active_terminals)
        self.assertNotIn(inactive_terminal, active_terminals)
        
        # Test search by name
        name_search = self.geidea_terminal_model.search([('name', 'ilike', 'Active')])
        self.assertIn(active_terminal, name_search)
        self.assertNotIn(inactive_terminal, name_search)
        
        # Test search by terminal_id
        terminal_search = self.geidea_terminal_model.search([('terminal_id', '=', 'ACTIVE001')])
        self.assertEqual(len(terminal_search), 1)
        self.assertEqual(terminal_search, active_terminal)

    def test_09_encryption_functionality(self):
        """Test encryption/decryption of sensitive data."""
        terminal = self.geidea_terminal_model.create({
            'name': 'Encryption Test Terminal',
            'terminal_id': 'ENCRYPT001',
            'merchant_id': 'MERCHANT_ENCRYPT',
            'api_key': 'encrypt_api_key_123',
        })
        
        # Test encryption key is generated
        self.assertTrue(terminal.encryption_key)
        
        # Test encryption/decryption methods
        test_data = "sensitive_test_data"
        encrypted_data = terminal._encrypt_sensitive_data(test_data)
        self.assertNotEqual(encrypted_data, test_data)
        
        decrypted_data = terminal._decrypt_sensitive_data(encrypted_data)
        self.assertEqual(decrypted_data, test_data)

    def test_10_view_action_window(self):
        """Test that the action window is properly configured."""
        action = self.env.ref('pos_geidea_payment.action_geidea_terminal')
        self.assertTrue(action)
        self.assertEqual(action.type, 'ir.actions.act_window')
        self.assertEqual(action.res_model, 'geidea.terminal')
        self.assertEqual(action.view_mode, 'tree,form')
        self.assertTrue(action.search_view_id)