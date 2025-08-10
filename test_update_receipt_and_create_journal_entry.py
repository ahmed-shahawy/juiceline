#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات وحدة تحديث تواريخ الاستلام وإنشاء قيود اليومية
Tests for Receipt Date Update and Journal Entry Creation Module

ملف اختبار شامل للتأكد من صحة عمل جميع الوظائف في الوحدة
Comprehensive test file to ensure all module functions work correctly

Author: Generated for Juiceline Project
Date: 2024
"""

import unittest
import sys
import os
from datetime import datetime, date

# إضافة المسار الحالي لاستيراد الوحدة
# Add current path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_receipt_and_create_journal_entry import (
    Receipt, JournalEntry, create_journal_entry, 
    update_receipt_and_create_journal_entry, 
    get_all_journal_entries, clear_journal_entries
)


class TestReceiptClass(unittest.TestCase):
    """
    اختبارات فئة الإيصال
    Tests for Receipt class
    """
    
    def test_receipt_creation(self):
        """اختبار إنشاء إيصال جديد"""
        receipt = Receipt(
            receipt_id=1,
            scheduled_date=date(2024, 1, 15),
            amount=1000.50
        )
        
        self.assertEqual(receipt.receipt_id, 1)
        self.assertEqual(receipt.scheduled_date, date(2024, 1, 15))
        self.assertEqual(receipt.amount, 1000.50)
        self.assertIsNone(receipt.date_received)
    
    def test_receipt_with_date_received(self):
        """اختبار إنشاء إيصال مع تاريخ الاستلام"""
        receipt = Receipt(
            receipt_id=2,
            scheduled_date=date(2024, 1, 16),
            amount=500.25,
            date_received=date(2024, 1, 14)
        )
        
        self.assertEqual(receipt.date_received, date(2024, 1, 14))
    
    def test_receipt_string_representation(self):
        """اختبار تمثيل الإيصال كنص"""
        receipt = Receipt(1, date(2024, 1, 15), 1000.50)
        self.assertIn("Receipt(ID: 1", str(receipt))
        self.assertIn("1000.5", str(receipt))


class TestJournalEntryClass(unittest.TestCase):
    """
    اختبارات فئة قيد اليومية
    Tests for JournalEntry class
    """
    
    def test_journal_entry_creation(self):
        """اختبار إنشاء قيد يومية جديد"""
        entry = JournalEntry(
            entry_id=1,
            entry_date=date(2024, 1, 15),
            amount=1000.50,
            description="استلام مجدول",
            receipt_id=1
        )
        
        self.assertEqual(entry.entry_id, 1)
        self.assertEqual(entry.entry_date, date(2024, 1, 15))
        self.assertEqual(entry.amount, 1000.50)
        self.assertEqual(entry.description, "استلام مجدول")
        self.assertEqual(entry.receipt_id, 1)
        self.assertIsInstance(entry.created_at, datetime)
    
    def test_journal_entry_string_representation(self):
        """اختبار تمثيل قيد اليومية كنص"""
        entry = JournalEntry(1, date(2024, 1, 15), 1000.50, "استلام مجدول", 1)
        self.assertIn("JournalEntry(ID: 1", str(entry))
        self.assertIn("استلام مجدول", str(entry))


class TestCreateJournalEntry(unittest.TestCase):
    """
    اختبارات دالة إنشاء قيد اليومية
    Tests for create_journal_entry function
    """
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        clear_journal_entries()
    
    def test_create_single_journal_entry(self):
        """اختبار إنشاء قيد يومية واحد"""
        entry = create_journal_entry(
            entry_date=date(2024, 1, 15),
            amount=1500.75,
            description="استلام مجدول",
            receipt_id=1
        )
        
        self.assertIsInstance(entry, JournalEntry)
        self.assertEqual(entry.entry_date, date(2024, 1, 15))
        self.assertEqual(entry.amount, 1500.75)
        self.assertEqual(entry.description, "استلام مجدول")
        self.assertEqual(entry.receipt_id, 1)
        
        # التحقق من إضافة القيد إلى القائمة
        # Verify entry was added to the list
        all_entries = get_all_journal_entries()
        self.assertEqual(len(all_entries), 1)
        self.assertEqual(all_entries[0].entry_id, entry.entry_id)
    
    def test_create_multiple_journal_entries(self):
        """اختبار إنشاء عدة قيود يومية"""
        entry1 = create_journal_entry(date(2024, 1, 15), 1000, "استلام مجدول", 1)
        entry2 = create_journal_entry(date(2024, 1, 16), 2000, "استلام مجدول", 2)
        
        self.assertEqual(entry1.entry_id, 1)
        self.assertEqual(entry2.entry_id, 2)
        
        all_entries = get_all_journal_entries()
        self.assertEqual(len(all_entries), 2)


class TestUpdateReceiptAndCreateJournalEntry(unittest.TestCase):
    """
    اختبارات الدالة الرئيسية
    Tests for main function
    """
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        clear_journal_entries()
    
    def test_empty_receipts_list(self):
        """اختبار قائمة إيصالات فارغة"""
        result = update_receipt_and_create_journal_entry([])
        self.assertEqual(len(result), 0)
        self.assertEqual(len(get_all_journal_entries()), 0)
    
    def test_single_receipt_update(self):
        """اختبار تحديث إيصال واحد"""
        receipt = Receipt(
            receipt_id=1,
            scheduled_date=date(2024, 1, 15),
            amount=1500.50
        )
        
        # التحقق من أن تاريخ الاستلام فارغ في البداية
        # Verify date_received is None initially
        self.assertIsNone(receipt.date_received)
        
        # تطبيق العملية
        # Apply the operation
        created_entries = update_receipt_and_create_journal_entry([receipt])
        
        # التحقق من تحديث تاريخ الاستلام
        # Verify date_received was updated
        self.assertEqual(receipt.date_received, receipt.scheduled_date)
        self.assertEqual(receipt.date_received, date(2024, 1, 15))
        
        # التحقق من إنشاء قيد اليومية
        # Verify journal entry was created
        self.assertEqual(len(created_entries), 1)
        self.assertEqual(created_entries[0].entry_date, date(2024, 1, 15))
        self.assertEqual(created_entries[0].amount, 1500.50)
        self.assertEqual(created_entries[0].description, "استلام مجدول")
        self.assertEqual(created_entries[0].receipt_id, 1)
    
    def test_multiple_receipts_update(self):
        """اختبار تحديث عدة إيصالات"""
        receipts = [
            Receipt(1, date(2024, 1, 15), 1000.0),
            Receipt(2, date(2024, 1, 16), 2000.0),
            Receipt(3, date(2024, 1, 17), 1500.0)
        ]
        
        # التحقق من أن جميع تواريخ الاستلام فارغة
        # Verify all date_received are None
        for receipt in receipts:
            self.assertIsNone(receipt.date_received)
        
        # تطبيق العملية
        # Apply the operation
        created_entries = update_receipt_and_create_journal_entry(receipts)
        
        # التحقق من تحديث جميع التواريخ
        # Verify all dates were updated
        self.assertEqual(receipts[0].date_received, date(2024, 1, 15))
        self.assertEqual(receipts[1].date_received, date(2024, 1, 16))
        self.assertEqual(receipts[2].date_received, date(2024, 1, 17))
        
        # التحقق من إنشاء جميع قيود اليومية
        # Verify all journal entries were created
        self.assertEqual(len(created_entries), 3)
        
        # التحقق من تفاصيل كل قيد
        # Verify details of each entry
        for i, entry in enumerate(created_entries):
            self.assertEqual(entry.receipt_id, receipts[i].receipt_id)
            self.assertEqual(entry.amount, receipts[i].amount)
            self.assertEqual(entry.description, "استلام مجدول")
    
    def test_receipt_with_invalid_scheduled_date(self):
        """اختبار إيصال بتاريخ مجدول غير صحيح"""
        receipt = Receipt(1, None, 1000.0)  # تاريخ مجدول فارغ
        
        created_entries = update_receipt_and_create_journal_entry([receipt])
        
        # يجب أن لا يتم إنشاء أي قيد
        # No entry should be created
        self.assertEqual(len(created_entries), 0)
        self.assertEqual(len(get_all_journal_entries()), 0)
    
    def test_receipt_with_invalid_amount(self):
        """اختبار إيصال بمبلغ غير صحيح"""
        receipt = Receipt(1, date(2024, 1, 15), -100.0)  # مبلغ سالب
        
        created_entries = update_receipt_and_create_journal_entry([receipt])
        
        # يجب أن لا يتم إنشاء أي قيد
        # No entry should be created
        self.assertEqual(len(created_entries), 0)
        self.assertEqual(len(get_all_journal_entries()), 0)
    
    def test_mixed_valid_invalid_receipts(self):
        """اختبار خليط من الإيصالات الصحيحة وغير الصحيحة"""
        receipts = [
            Receipt(1, date(2024, 1, 15), 1000.0),  # صحيح
            Receipt(2, None, 2000.0),               # تاريخ غير صحيح
            Receipt(3, date(2024, 1, 17), -500.0), # مبلغ غير صحيح
            Receipt(4, date(2024, 1, 18), 3000.0)  # صحيح
        ]
        
        created_entries = update_receipt_and_create_journal_entry(receipts)
        
        # يجب إنشاء قيدين فقط (للإيصالات الصحيحة)
        # Should create only 2 entries (for valid receipts)
        self.assertEqual(len(created_entries), 2)
        
        # التحقق من الإيصالات الصحيحة
        # Verify valid receipts
        self.assertEqual(receipts[0].date_received, date(2024, 1, 15))
        self.assertEqual(receipts[3].date_received, date(2024, 1, 18))
        
        # التحقق من الإيصالات غير الصحيحة (لم تتغير)
        # Verify invalid receipts (unchanged)
        self.assertIsNone(receipts[1].date_received)
        self.assertIsNone(receipts[2].date_received)


class TestUtilityFunctions(unittest.TestCase):
    """
    اختبارات الدوال المساعدة
    Tests for utility functions
    """
    
    def setUp(self):
        """إعداد قبل كل اختبار"""
        clear_journal_entries()
    
    def test_get_all_journal_entries_empty(self):
        """اختبار الحصول على قيود اليومية عندما تكون القائمة فارغة"""
        entries = get_all_journal_entries()
        self.assertEqual(len(entries), 0)
        self.assertIsInstance(entries, list)
    
    def test_get_all_journal_entries_with_data(self):
        """اختبار الحصول على قيود اليومية مع وجود بيانات"""
        # إنشاء بعض القيود
        create_journal_entry(date(2024, 1, 15), 1000, "تجريبي", 1)
        create_journal_entry(date(2024, 1, 16), 2000, "تجريبي", 2)
        
        entries = get_all_journal_entries()
        self.assertEqual(len(entries), 2)
        
        # التحقق من أن النسخة المرجعة منفصلة (copy)
        # Verify returned copy is separate
        original_length = len(entries)
        entries.append("test")  # إضافة عنصر للنسخة
        
        # يجب أن تبقى القائمة الأصلية كما هي
        # Original list should remain unchanged
        self.assertEqual(len(get_all_journal_entries()), original_length)
    
    def test_clear_journal_entries(self):
        """اختبار مسح قيود اليومية"""
        # إنشاء بعض القيود
        create_journal_entry(date(2024, 1, 15), 1000, "تجريبي", 1)
        create_journal_entry(date(2024, 1, 16), 2000, "تجريبي", 2)
        
        # التحقق من وجود القيود
        self.assertEqual(len(get_all_journal_entries()), 2)
        
        # مسح القيود
        clear_journal_entries()
        
        # التحقق من مسح القيود
        self.assertEqual(len(get_all_journal_entries()), 0)


def run_tests():
    """
    تشغيل جميع الاختبارات
    Run all tests
    """
    print("=== تشغيل اختبارات الوحدة ===")
    print("=== Running Module Tests ===")
    print()
    
    # إنشاء مجموعة الاختبارات
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # إضافة جميع فئات الاختبارات
    # Add all test classes
    test_classes = [
        TestReceiptClass,
        TestJournalEntryClass,
        TestCreateJournalEntry,
        TestUpdateReceiptAndCreateJournalEntry,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # تشغيل الاختبارات
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # طباعة النتائج
    # Print results
    print()
    print("=== نتائج الاختبارات ===")
    print("=== Test Results ===")
    print(f"تم تشغيل: {result.testsRun} اختبار")
    print(f"Tests run: {result.testsRun}")
    print(f"فشل: {len(result.failures)} اختبار")
    print(f"Failures: {len(result.failures)}")
    print(f"أخطاء: {len(result.errors)} اختبار")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nالاختبارات الفاشلة:")
        print("Failed tests:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nالأخطاء:")
        print("Errors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # إرجاع حالة النجاح
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)