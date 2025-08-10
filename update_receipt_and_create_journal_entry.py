#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
وحدة تحديث تواريخ الاستلام وإنشاء قيود اليومية
Receipt Date Update and Journal Entry Creation Module

هذا الملف يحتوي على الكود المطلوب لتحديث تاريخ ووقت الاستلام (date_received) 
ليكون مساويًا للتاريخ المجدول (scheduled_date)، ثم إنشاء قيد يومية بناءً على التاريخ المجدول.

This file contains the required code to update receipt date_received to equal 
scheduled_date, then create journal entries based on the scheduled date.

Author: Generated for Juiceline Project
Date: 2024
"""

from datetime import datetime, date
from typing import List, Union, Optional
import logging

# إعداد نظام السجلات
# Setup logging system
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Receipt:
    """
    فئة الإيصال - تمثل إيصال استلام مع التواريخ والمبالغ المطلوبة
    Receipt class - represents a receipt with required dates and amounts
    """
    
    def __init__(self, receipt_id: int, scheduled_date: Union[datetime, date], 
                 amount: float, date_received: Optional[Union[datetime, date]] = None, 
                 description: str = ""):
        """
        تهيئة الإيصال
        Initialize receipt
        
        Args:
            receipt_id: معرف الإيصال / Receipt ID
            scheduled_date: التاريخ المجدول / Scheduled date
            amount: المبلغ / Amount
            date_received: تاريخ الاستلام (اختياري) / Date received (optional)
            description: الوصف (اختياري) / Description (optional)
        """
        self.receipt_id = receipt_id
        self.scheduled_date = scheduled_date
        self.amount = amount
        self.date_received = date_received
        self.description = description
    
    def __str__(self):
        return f"Receipt(ID: {self.receipt_id}, Scheduled: {self.scheduled_date}, Amount: {self.amount})"
    
    def __repr__(self):
        return self.__str__()


class JournalEntry:
    """
    فئة قيد اليومية - تمثل قيد في دفتر اليومية
    Journal Entry class - represents an entry in the journal
    """
    
    def __init__(self, entry_id: int, entry_date: Union[datetime, date], 
                 amount: float, description: str, receipt_id: int):
        """
        تهيئة قيد اليومية
        Initialize journal entry
        
        Args:
            entry_id: معرف القيد / Entry ID
            entry_date: تاريخ القيد / Entry date
            amount: المبلغ / Amount
            description: الوصف / Description
            receipt_id: معرف الإيصال المرتبط / Related receipt ID
        """
        self.entry_id = entry_id
        self.entry_date = entry_date
        self.amount = amount
        self.description = description
        self.receipt_id = receipt_id
        self.created_at = datetime.now()
    
    def __str__(self):
        return f"JournalEntry(ID: {self.entry_id}, Date: {self.entry_date}, Amount: {self.amount}, Desc: {self.description})"
    
    def __repr__(self):
        return self.__str__()


# قائمة لحفظ قيود اليومية المنشأة
# List to store created journal entries
journal_entries: List[JournalEntry] = []
_entry_counter = 1


def create_journal_entry(entry_date: Union[datetime, date], amount: float, 
                        description: str, receipt_id: int) -> JournalEntry:
    """
    إنشاء قيد يومية جديد
    Create a new journal entry
    
    Args:
        entry_date: تاريخ القيد / Entry date
        amount: المبلغ / Amount
        description: الوصف / Description
        receipt_id: معرف الإيصال المرتبط / Related receipt ID
    
    Returns:
        JournalEntry: قيد اليومية المنشأ / Created journal entry
    """
    global _entry_counter
    
    # إنشاء قيد اليومية
    # Create journal entry
    entry = JournalEntry(
        entry_id=_entry_counter,
        entry_date=entry_date,
        amount=amount,
        description=description,
        receipt_id=receipt_id
    )
    
    # إضافة القيد إلى القائمة
    # Add entry to the list
    journal_entries.append(entry)
    
    # زيادة العداد
    # Increment counter
    _entry_counter += 1
    
    # تسجيل العملية
    # Log the operation
    logger.info(f"تم إنشاء قيد يومية - Journal entry created: {entry}")
    
    return entry


def update_receipt_and_create_journal_entry(receipts: List[Receipt]) -> List[JournalEntry]:
    """
    # تحديث تاريخ الاستلام ليكون مساوي للتاريخ المجدول وإنشاء قيد اليومية بناءً عليه
    Update receipt date to equal scheduled date and create journal entry based on it
    
    الدالة الرئيسية التي تقوم بتحديث تاريخ الاستلام لكل إيصال ليكون مساويًا للتاريخ المجدول،
    ثم تنشئ قيد يومية لكل إيصال بناءً على التاريخ المجدول والمبلغ.
    
    Main function that updates the receipt date for each receipt to equal the scheduled date,
    then creates a journal entry for each receipt based on the scheduled date and amount.
    
    Args:
        receipts: قائمة الإيصالات / List of receipts
    
    Returns:
        List[JournalEntry]: قائمة قيود اليومية المنشأة / List of created journal entries
    """
    if not receipts:
        logger.warning("قائمة الإيصالات فارغة - Empty receipts list")
        return []
    
    created_entries = []
    
    logger.info(f"بدء معالجة {len(receipts)} إيصال - Starting to process {len(receipts)} receipts")
    
    for receipt in receipts:
        try:
            # التحقق من صحة البيانات
            # Validate data
            if not receipt.scheduled_date:
                logger.error(f"التاريخ المجدول مفقود للإيصال {receipt.receipt_id} - Missing scheduled_date for receipt {receipt.receipt_id}")
                continue
            
            if receipt.amount is None or receipt.amount < 0:
                logger.error(f"المبلغ غير صحيح للإيصال {receipt.receipt_id} - Invalid amount for receipt {receipt.receipt_id}")
                continue
            
            # تحديث تاريخ الاستلام ليكون مساوي للتاريخ المجدول
            # Update date_received to equal scheduled_date
            receipt.date_received = receipt.scheduled_date
            
            logger.info(f"تم تحديث تاريخ الاستلام للإيصال {receipt.receipt_id} - Updated date_received for receipt {receipt.receipt_id}")
            
            # إنشاء قيد يومية بناءً على التاريخ المجدول
            # Create journal entry based on scheduled date
            journal_entry = create_journal_entry(
                entry_date=receipt.scheduled_date,
                amount=receipt.amount,
                description="استلام مجدول",  # Scheduled receipt
                receipt_id=receipt.receipt_id
            )
            
            created_entries.append(journal_entry)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الإيصال {receipt.receipt_id}: {str(e)} - Error processing receipt {receipt.receipt_id}: {str(e)}")
            continue
    
    logger.info(f"تم إنشاء {len(created_entries)} قيد يومية بنجاح - Successfully created {len(created_entries)} journal entries")
    
    return created_entries


def get_all_journal_entries() -> List[JournalEntry]:
    """
    الحصول على جميع قيود اليومية
    Get all journal entries
    
    Returns:
        List[JournalEntry]: قائمة جميع قيود اليومية / List of all journal entries
    """
    return journal_entries.copy()


def clear_journal_entries():
    """
    مسح جميع قيود اليومية (للاختبار)
    Clear all journal entries (for testing)
    """
    global journal_entries, _entry_counter
    journal_entries.clear()
    _entry_counter = 1
    logger.info("تم مسح جميع قيود اليومية - All journal entries cleared")


# مثال على الاستخدام
# Usage example
def main():
    """
    مثال على كيفية استخدام الوحدة
    Example of how to use the module
    """
    # إنشاء قائمة إيصالات تجريبية
    # Create sample receipts list
    sample_receipts = [
        Receipt(
            receipt_id=1,
            scheduled_date=date(2024, 1, 15),
            amount=1500.50,
            description="إيصال رقم 1"
        ),
        Receipt(
            receipt_id=2,
            scheduled_date=date(2024, 1, 16),
            amount=2200.75,
            description="إيصال رقم 2"
        ),
        Receipt(
            receipt_id=3,
            scheduled_date=date(2024, 1, 17),
            amount=980.25,
            description="إيصال رقم 3"
        )
    ]
    
    print("=== مثال على استخدام الوحدة ===")
    print("=== Module Usage Example ===")
    print()
    
    print("الإيصالات قبل التحديث:")
    print("Receipts before update:")
    for receipt in sample_receipts:
        print(f"  {receipt} - date_received: {receipt.date_received}")
    print()
    
    # تطبيق العملية المطلوبة
    # Apply the required operation
    created_entries = update_receipt_and_create_journal_entry(sample_receipts)
    
    print("الإيصالات بعد التحديث:")
    print("Receipts after update:")
    for receipt in sample_receipts:
        print(f"  {receipt} - date_received: {receipt.date_received}")
    print()
    
    print("قيود اليومية المنشأة:")
    print("Created journal entries:")
    for entry in created_entries:
        print(f"  {entry}")
    print()
    
    print(f"إجمالي قيود اليومية: {len(get_all_journal_entries())}")
    print(f"Total journal entries: {len(get_all_journal_entries())}")


if __name__ == "__main__":
    main()