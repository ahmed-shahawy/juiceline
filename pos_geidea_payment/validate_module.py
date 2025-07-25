#!/usr/bin/env python3
"""
Geidea Payment Integration Module Validation Script

This script validates the module structure and basic functionality.
"""

import os
import sys
import json
import importlib.util
from pathlib import Path

def validate_module_structure():
    """Validate the basic module structure"""
    print("=== Validating Module Structure ===")
    
    base_path = Path(__file__).parent
    required_files = [
        '__manifest__.py',
        '__init__.py',
        'models/__init__.py',
        'models/geidea_terminal.py',
        'models/pos_config.py',
        'models/pos_payment_method.py',
        'models/pos_session.py',
        'controllers/__init__.py',
        'controllers/geidea_controller.py',
        'security/ir.model.access.csv',
        'views/geidea_terminal_views.xml',
        'views/pos_config_views.xml',
        'data/payment_method_data.xml',
        'README.md',
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def validate_manifest():
    """Validate the manifest file"""
    print("\n=== Validating Manifest ===")
    
    base_path = Path(__file__).parent
    manifest_path = base_path / '__manifest__.py'
    
    try:
        # Read and evaluate the manifest file
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # The manifest is a dictionary, so we need to evaluate it
        manifest_dict = eval(content.strip())
        
        # Check required fields
        required_fields = ['name', 'version', 'depends', 'data', 'assets']
        
        missing_fields = [field for field in required_fields 
                         if field not in manifest_dict]
        
        if missing_fields:
            print(f"❌ Missing manifest fields: {missing_fields}")
            return False
        
        # Validate dependencies
        if 'point_of_sale' not in manifest_dict.get('depends', []):
            print("❌ Missing 'point_of_sale' dependency")
            return False
            
        print("✅ Manifest validation passed")
        print(f"   Name: {manifest_dict.get('name')}")
        print(f"   Version: {manifest_dict.get('version')}")
        print(f"   Dependencies: {manifest_dict.get('depends')}")
        return True
        
    except Exception as e:
        print(f"❌ Manifest validation failed: {e}")
        return False

def validate_python_syntax():
    """Validate Python file syntax"""
    print("\n=== Validating Python Syntax ===")
    
    base_path = Path(__file__).parent
    python_files = []
    
    # Find all Python files
    for pattern in ['**/*.py']:
        python_files.extend(base_path.glob(pattern))
    
    syntax_errors = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            syntax_errors.append((py_file, str(e)))
    
    if syntax_errors:
        print("❌ Python syntax errors found:")
        for file_path, error in syntax_errors:
            print(f"   {file_path}: {error}")
        return False
    else:
        print(f"✅ All {len(python_files)} Python files have valid syntax")
        return True

def validate_xml_structure():
    """Basic XML structure validation"""
    print("\n=== Validating XML Files ===")
    
    base_path = Path(__file__).parent
    xml_files = list(base_path.glob('**/*.xml'))
    
    try:
        import xml.etree.ElementTree as ET
        
        xml_errors = []
        for xml_file in xml_files:
            try:
                ET.parse(xml_file)
            except ET.ParseError as e:
                xml_errors.append((xml_file, str(e)))
        
        if xml_errors:
            print("❌ XML parsing errors found:")
            for file_path, error in xml_errors:
                print(f"   {file_path}: {error}")
            return False
        else:
            print(f"✅ All {len(xml_files)} XML files are well-formed")
            return True
            
    except ImportError:
        print("⚠️  XML validation skipped (xml.etree.ElementTree not available)")
        return True

def validate_javascript_files():
    """Basic JavaScript file validation"""
    print("\n=== Validating JavaScript Files ===")
    
    base_path = Path(__file__).parent
    js_files = list(base_path.glob('**/*.js'))
    
    # Basic validation - check for common syntax issues
    issues = []
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for basic issues
                if 'import' in content and not content.strip().startswith('/** @odoo-module */'):
                    issues.append((js_file, "Missing @odoo-module directive"))
                
                # Check for unclosed brackets (basic check)
                open_brackets = content.count('{') - content.count('}')
                if open_brackets != 0:
                    issues.append((js_file, f"Mismatched brackets: {open_brackets}"))
                    
        except Exception as e:
            issues.append((js_file, f"Error reading file: {e}"))
    
    if issues:
        print("⚠️  JavaScript issues found:")
        for file_path, issue in issues:
            print(f"   {file_path}: {issue}")
        return False
    else:
        print(f"✅ All {len(js_files)} JavaScript files passed basic validation")
        return True

def generate_validation_report():
    """Generate a comprehensive validation report"""
    print("\n" + "="*60)
    print("GEIDEA PAYMENT INTEGRATION - VALIDATION REPORT")
    print("="*60)
    
    validations = [
        ("Module Structure", validate_module_structure),
        ("Manifest File", validate_manifest),
        ("Python Syntax", validate_python_syntax),
        ("XML Structure", validate_xml_structure),
        ("JavaScript Files", validate_javascript_files),
    ]
    
    results = {}
    all_passed = True
    
    for name, validation_func in validations:
        try:
            results[name] = validation_func()
            if not results[name]:
                all_passed = False
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {e}")
            results[name] = False
            all_passed = False
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20} {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("The Geidea Payment Integration module appears to be correctly structured.")
    else:
        print("⚠️  SOME VALIDATIONS FAILED")
        print("Please review the issues above before deploying the module.")
    
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = generate_validation_report()
    sys.exit(0 if success else 1)