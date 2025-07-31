#!/usr/bin/env python3
"""
Validation script for Geidea Payment Integration Module.
Checks if all the issues mentioned in the problem statement are addressed.
"""

import os
import re
import ast

def check_security_fixes():
    """Check if tracking=False is used for sensitive API fields."""
    print("🔒 Checking Security Fixes...")
    
    model_files = [
        'payment_geidea_18/models/payment_provider.py',
        'payment_geidea_18/models/payment_transaction.py',
        'payment_geidea_18/models/geidea_payment_acquirer.py'
    ]
    
    issues_found = []
    tracking_false_count = 0
    
    for file_path in model_files:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for tracking=False in sensitive fields
        tracking_false_matches = re.findall(r'tracking=False', content)
        tracking_false_count += len(tracking_false_matches)
        
        # Check for sensitive field names with tracking=False
        sensitive_patterns = [
            r'.*_key.*=.*fields\..*tracking=False',
            r'.*merchant_id.*=.*fields\..*tracking=False',
            r'.*api_.*=.*fields\..*tracking=False',
            r'.*transaction_id.*=.*fields\..*tracking=False'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                print(f"  ✓ Found secure field with tracking=False in {file_path}")
    
    if tracking_false_count >= 10:  # We have many sensitive fields
        print(f"  ✓ Security fix applied: {tracking_false_count} fields use tracking=False")
        return True
    else:
        issues_found.append("Missing tracking=False for sensitive fields")
        return False

def check_datetime_fixes():
    """Check if fields.Datetime.now() is used instead of request.env.cr.now()."""
    print("📅 Checking Datetime Handling Fixes...")
    
    python_files = [
        'payment_geidea_18/models/payment_provider.py',
        'payment_geidea_18/models/payment_transaction.py', 
        'payment_geidea_18/models/geidea_payment_acquirer.py',
        'payment_geidea_18/controllers/main.py'
    ]
    
    correct_usage_count = 0
    incorrect_usage_count = 0
    
    for file_path in python_files:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for correct usage
        correct_matches = re.findall(r'fields\.Datetime\.now\(\)', content)
        correct_usage_count += len(correct_matches)
        
        # Check for incorrect usage (excluding comments)
        lines = content.split('\n')
        for line in lines:
            # Skip comment lines
            if line.strip().startswith('#'):
                continue
            if 'request.env.cr.now()' in line:
                incorrect_usage_count += 1
    
    if correct_usage_count > 0 and incorrect_usage_count == 0:
        print(f"  ✓ Datetime fix applied: {correct_usage_count} uses of fields.Datetime.now()")
        return True
    else:
        print(f"  ✗ Found {incorrect_usage_count} uses of request.env.cr.now()")
        return False

def check_async_implementation():
    """Check if asynchronous HTTP calls are implemented."""
    print("⚡ Checking Asynchronous HTTP Implementation...")
    
    # Check for async method implementations
    transaction_file = 'payment_geidea_18/models/payment_transaction.py'
    
    with open(transaction_file, 'r') as f:
        content = f.read()
    
    async_patterns = [
        r'_geidea_make_request_async',
        r'threading\.Thread',
        r'async.*request',
        r'def.*async.*\('
    ]
    
    async_found = False
    for pattern in async_patterns:
        if re.search(pattern, content):
            async_found = True
            print(f"  ✓ Found async implementation: {pattern}")
    
    if async_found:
        print("  ✓ Asynchronous HTTP calls implemented")
        return True
    else:
        print("  ✗ No asynchronous HTTP implementation found")
        return False

def check_pos_interface_fixes():
    """Check if POS interface issues are fixed."""
    print("🖥️  Checking POS Interface Fixes...")
    
    # Check for set_geidea_transaction_id method
    transaction_file = 'payment_geidea_18/models/payment_transaction.py'
    
    with open(transaction_file, 'r') as f:
        content = f.read()
    
    if 'def set_geidea_transaction_id' in content:
        print("  ✓ set_geidea_transaction_id method implemented")
        pos_method_fix = True
    else:
        print("  ✗ set_geidea_transaction_id method missing")
        pos_method_fix = False
    
    # Check for safe model access in POS files
    pos_files = [
        'payment_geidea_18/static/src/js/pos_store.js',
        'payment_geidea_18/static/src/js/payment_screen.js'
    ]
    
    safe_access_found = False
    for file_path in pos_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for safe model access patterns
            safe_patterns = [
                r'_checkModelExists',
                r'getGeideaAcquirers',
                r'if.*models.*geidea',
                r'\.exists\(\)'
            ]
            
            for pattern in safe_patterns:
                if re.search(pattern, content):
                    safe_access_found = True
                    print(f"  ✓ Safe model access pattern found: {pattern}")
    
    if pos_method_fix and safe_access_found:
        print("  ✓ POS interface fixes implemented")
        return True
    else:
        print("  ✗ POS interface fixes incomplete")
        return False

def check_api_response_improvements():
    """Check if REST API responses are improved to JSON format."""
    print("🌐 Checking API Response Improvements...")
    
    controller_file = 'payment_geidea_18/controllers/main.py'
    
    with open(controller_file, 'r') as f:
        content = f.read()
    
    json_patterns = [
        r'_json_response',
        r'application/json',
        r'\.json\(',
        r'return.*{.*status.*}',
        r'Content-Type.*application/json'
    ]
    
    json_improvements = 0
    for pattern in json_patterns:
        matches = re.findall(pattern, content)
        json_improvements += len(matches)
        if matches:
            print(f"  ✓ JSON response improvement found: {pattern}")
    
    if json_improvements >= 3:
        print("  ✓ REST API JSON response improvements implemented")
        return True
    else:
        print("  ✗ Insufficient JSON response improvements")
        return False

def check_error_handling():
    """Check if comprehensive error handling is implemented."""
    print("🚨 Checking Error Handling Improvements...")
    
    python_files = [
        'payment_geidea_18/models/payment_transaction.py',
        'payment_geidea_18/controllers/main.py',
        'payment_geidea_18/models/geidea_payment_acquirer.py'
    ]
    
    error_handling_count = 0
    
    for file_path in python_files:
        with open(file_path, 'r') as f:
            content = f.read()
        
        error_patterns = [
            r'try:.*except',
            r'except.*Exception',
            r'_logger\.error',
            r'_logger\.exception',
            r'raise.*Error',
            r'ValidationError',
            r'UserError'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            error_handling_count += len(matches)
    
    if error_handling_count >= 10:
        print(f"  ✓ Comprehensive error handling: {error_handling_count} error handling patterns")
        return True
    else:
        print(f"  ✗ Insufficient error handling: {error_handling_count} patterns found")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Validating Geidea Payment Integration Module")
    print("=" * 60)
    
    checks = [
        ("Security Fixes (tracking=False)", check_security_fixes),
        ("Datetime Handling", check_datetime_fixes),
        ("Asynchronous HTTP Calls", check_async_implementation),
        ("POS Interface Fixes", check_pos_interface_fixes),
        ("API Response Improvements", check_api_response_improvements),
        ("Error Handling", check_error_handling),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            print()
        except Exception as e:
            print(f"  ✗ Error during {check_name}: {e}")
            results.append((check_name, False))
            print()
    
    # Summary
    print("📊 Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All required fixes have been implemented!")
        return True
    else:
        print("⚠️  Some issues still need attention.")
        return False

if __name__ == "__main__":
    main()