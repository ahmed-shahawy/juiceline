#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نهائي للتحقق من تنفيذ المتطلبات بدقة
Final test to verify exact requirement implementation
"""

import sys
import os
from datetime import date

# استيراد الوحدة
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_receipt_and_create_journal_entry import (
    Receipt, update_receipt_and_create_journal_entry, 
    get_all_journal_entries, clear_journal_entries
)

def verify_requirements():
    """
    التحقق من تنفيذ المتطلبات بدقة:
    ✓ يتم تعيين receipt.date_received = receipt.scheduled_date
    ✓ يتم استدعاء دالة create_journal_entry بحيث يكون تاريخ القيد هو التاريخ المجدول
    ✓ قيمة القيد هي المبلغ
    ✓ الوصف "استلام مجدول"
    """
    
    print("=== التحقق من تنفيذ المتطلبات بدقة ===")
    print("=== Verifying Exact Requirements Implementation ===")
    print()
    
    # مسح أي قيود سابقة
    clear_journal_entries()
    
    # إنشاء قائمة إيصالات للاختبار
    test_receipts = [
        Receipt(
            receipt_id=100,
            scheduled_date=date(2024, 2, 10),
            amount=999.99,
            date_received=None  # تأكيد أنه فارغ في البداية
        ),
        Receipt(
            receipt_id=200,
            scheduled_date=date(2024, 2, 11),
            amount=1234.56,
            date_received=None
        )
    ]
    
    print("الحالة الأولية للإيصالات:")
    print("Initial receipt state:")
    for receipt in test_receipts:
        print(f"  Receipt {receipt.receipt_id}:")
        print(f"    scheduled_date: {receipt.scheduled_date}")
        print(f"    date_received: {receipt.date_received}")
        print(f"    amount: {receipt.amount}")
    print()
    
    # تطبيق العملية المطلوبة
    print("تطبيق العملية...")
    print("Applying operation...")
    
    # # تحديث تاريخ الاستلام ليكون مساوي للتاريخ المجدول وإنشاء قيد اليومية بناءً عليه
    created_entries = update_receipt_and_create_journal_entry(test_receipts)
    
    print()
    print("=== التحقق من النتائج ===")
    print("=== Verifying Results ===")
    
    # التحقق الأول: تحديث تاريخ الاستلام
    print("1. التحقق من تحديث date_received:")
    print("1. Verifying date_received update:")
    all_dates_updated = True
    for receipt in test_receipts:
        is_equal = receipt.date_received == receipt.scheduled_date
        print(f"   Receipt {receipt.receipt_id}: date_received = {receipt.date_received}, scheduled_date = {receipt.scheduled_date} ✓" if is_equal else f"   Receipt {receipt.receipt_id}: ERROR - dates don't match!")
        if not is_equal:
            all_dates_updated = False
    
    if all_dates_updated:
        print("   ✅ جميع تواريخ الاستلام تم تحديثها بنجاح")
        print("   ✅ All date_received values updated successfully")
    else:
        print("   ❌ فشل في تحديث بعض التواريخ")
        print("   ❌ Failed to update some dates")
    
    print()
    
    # التحقق الثاني: إنشاء قيود اليومية
    print("2. التحقق من قيود اليومية:")
    print("2. Verifying journal entries:")
    
    if len(created_entries) == len(test_receipts):
        print(f"   ✅ تم إنشاء {len(created_entries)} قيد يومية (العدد صحيح)")
        print(f"   ✅ Created {len(created_entries)} journal entries (correct count)")
    else:
        print(f"   ❌ عدد القيود خاطئ: متوقع {len(test_receipts)}, فعلي {len(created_entries)}")
        print(f"   ❌ Wrong entry count: expected {len(test_receipts)}, actual {len(created_entries)}")
    
    # التحقق من تفاصيل كل قيد
    for i, (receipt, entry) in enumerate(zip(test_receipts, created_entries)):
        print(f"   قيد رقم {i+1} / Entry #{i+1}:")
        
        # التحقق من التاريخ
        date_correct = entry.entry_date == receipt.scheduled_date
        print(f"     تاريخ القيد: {entry.entry_date} {'✅' if date_correct else '❌'}")
        print(f"     Entry date: {entry.entry_date} {'✅' if date_correct else '❌'}")
        
        # التحقق من المبلغ
        amount_correct = entry.amount == receipt.amount
        print(f"     مبلغ القيد: {entry.amount} {'✅' if amount_correct else '❌'}")
        print(f"     Entry amount: {entry.amount} {'✅' if amount_correct else '❌'}")
        
        # التحقق من الوصف
        desc_correct = entry.description == "استلام مجدول"
        print(f"     وصف القيد: '{entry.description}' {'✅' if desc_correct else '❌'}")
        print(f"     Entry description: '{entry.description}' {'✅' if desc_correct else '❌'}")
        
        # التحقق من معرف الإيصال
        id_correct = entry.receipt_id == receipt.receipt_id
        print(f"     معرف الإيصال: {entry.receipt_id} {'✅' if id_correct else '❌'}")
        print(f"     Receipt ID: {entry.receipt_id} {'✅' if id_correct else '❌'}")
        
        print()
    
    # التحقق النهائي
    all_requirements_met = (
        all_dates_updated and
        len(created_entries) == len(test_receipts) and
        all(entry.entry_date == receipt.scheduled_date for entry, receipt in zip(created_entries, test_receipts)) and
        all(entry.amount == receipt.amount for entry, receipt in zip(created_entries, test_receipts)) and
        all(entry.description == "استلام مجدول" for entry in created_entries) and
        all(entry.receipt_id == receipt.receipt_id for entry, receipt in zip(created_entries, test_receipts))
    )
    
    print("=== النتيجة النهائية ===")
    print("=== Final Result ===")
    if all_requirements_met:
        print("🎉 ✅ جميع المتطلبات تم تنفيذها بنجاح!")
        print("🎉 ✅ All requirements implemented successfully!")
        print()
        print("تم التحقق من:")
        print("Verified:")
        print("✓ receipt.date_received = receipt.scheduled_date")
        print("✓ create_journal_entry called with scheduled_date")
        print("✓ journal entry amount = receipt amount")
        print("✓ journal entry description = 'استلام مجدول'")
        return True
    else:
        print("❌ بعض المتطلبات لم يتم تنفيذها بشكل صحيح")
        print("❌ Some requirements not implemented correctly")
        return False

if __name__ == "__main__":
    success = verify_requirements()
    sys.exit(0 if success else 1)