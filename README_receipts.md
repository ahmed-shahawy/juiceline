# وحدة تحديث تواريخ الاستلام وإنشاء قيود اليومية
# Receipt Date Update and Journal Entry Creation Module

## نظرة عامة / Overview

تحتوي هذه الوحدة على الكود المطلوب لتحديث تاريخ ووقت الاستلام (`date_received`) ليكون مساويًا للتاريخ المجدول (`scheduled_date`)، ثم إنشاء قيد يومية بناءً على التاريخ المجدول.

This module contains the required code to update receipt date_received to equal scheduled_date, then create journal entries based on the scheduled date.

## الملفات / Files

- `update_receipt_and_create_journal_entry.py` - الوحدة الأساسية / Main module
- `test_update_receipt_and_create_journal_entry.py` - اختبارات شاملة / Comprehensive tests
- `README_receipts.md` - هذا الملف / This file

## الوظائف الأساسية / Core Functionality

### الفئات / Classes

#### `Receipt`
تمثل إيصال استلام مع الحقول المطلوبة:
Represents a receipt with required fields:

- `receipt_id`: معرف الإيصال / Receipt ID
- `scheduled_date`: التاريخ المجدول / Scheduled date
- `amount`: المبلغ / Amount
- `date_received`: تاريخ الاستلام / Date received
- `description`: الوصف / Description

#### `JournalEntry`
تمثل قيد في دفتر اليومية:
Represents a journal entry:

- `entry_id`: معرف القيد / Entry ID
- `entry_date`: تاريخ القيد / Entry date
- `amount`: المبلغ / Amount
- `description`: الوصف / Description
- `receipt_id`: معرف الإيصال المرتبط / Related receipt ID
- `created_at`: وقت الإنشاء / Creation timestamp

### الدوال الأساسية / Core Functions

#### `update_receipt_and_create_journal_entry(receipts: List[Receipt]) -> List[JournalEntry]`

الدالة الرئيسية التي تنفذ المتطلبات:
Main function that implements the requirements:

1. **تحديث تاريخ الاستلام / Update Receipt Date**:
   ```python
   receipt.date_received = receipt.scheduled_date
   ```

2. **إنشاء قيد يومية / Create Journal Entry**:
   ```python
   journal_entry = create_journal_entry(
       entry_date=receipt.scheduled_date,
       amount=receipt.amount,
       description="استلام مجدول",  # Scheduled receipt
       receipt_id=receipt.receipt_id
   )
   ```

#### `create_journal_entry(entry_date, amount, description, receipt_id) -> JournalEntry`
دالة إنشاء قيد يومية جديد / Function to create a new journal entry

#### دوال مساعدة / Utility Functions
- `get_all_journal_entries()` - الحصول على جميع القيود / Get all entries
- `clear_journal_entries()` - مسح القيود (للاختبار) / Clear entries (for testing)

## كيفية الاستخدام / Usage

### مثال أساسي / Basic Example

```python
from update_receipt_and_create_journal_entry import Receipt, update_receipt_and_create_journal_entry
from datetime import date

# إنشاء قائمة الإيصالات / Create receipts list
receipts = [
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
    )
]

# تطبيق العملية المطلوبة / Apply the required operation
created_entries = update_receipt_and_create_journal_entry(receipts)

# عرض النتائج / Display results
for receipt in receipts:
    print(f"Receipt {receipt.receipt_id}: date_received = {receipt.date_received}")

for entry in created_entries:
    print(f"Journal Entry: {entry}")
```

### تشغيل المثال / Running Example

```bash
# تشغيل المثال الأساسي / Run basic example
python update_receipt_and_create_journal_entry.py

# تشغيل الاختبارات / Run tests
python test_update_receipt_and_create_journal_entry.py
```

## المتطلبات / Requirements

- Python 3.6+
- لا توجد مكتبات خارجية مطلوبة / No external libraries required

## التحقق من صحة البيانات / Data Validation

الوحدة تتضمن التحقق من صحة البيانات:
The module includes data validation:

- **التاريخ المجدول**: يجب أن يكون صحيحًا وغير فارغ
  **Scheduled Date**: Must be valid and not None
- **المبلغ**: يجب أن يكون رقمًا موجبًا أو صفر
  **Amount**: Must be a positive number or zero
- **معرف الإيصال**: يجب أن يكون صحيحًا
  **Receipt ID**: Must be valid

في حالة وجود بيانات غير صحيحة، سيتم تسجيل خطأ وتخطي هذا الإيصال.
In case of invalid data, an error will be logged and the receipt will be skipped.

## نظام السجلات / Logging System

الوحدة تستخدم نظام السجلات المدمج في Python لتسجيل:
The module uses Python's built-in logging system to record:

- عمليات التحديث الناجحة / Successful updates
- الأخطاء والتحذيرات / Errors and warnings
- إحصائيات العمليات / Operation statistics

## الاختبارات / Testing

يتضمن المشروع مجموعة شاملة من الاختبارات:
The project includes comprehensive tests:

- اختبارات الفئات / Class tests
- اختبارات الدوال / Function tests
- اختبارات التكامل / Integration tests
- اختبارات الحالات الحدية / Edge case tests
- اختبارات التحقق من صحة البيانات / Data validation tests

### تشغيل الاختبارات / Running Tests

```bash
python test_update_receipt_and_create_journal_entry.py
```

النتيجة المتوقعة: تمرير جميع الاختبارات (16 اختبار)
Expected result: All tests pass (16 tests)

## التوافق مع Odoo / Odoo Compatibility

هذه الوحدة مصممة للعمل مع:
This module is designed to work with:

- مشاريع Odoo / Odoo projects
- أنظمة POS / POS systems
- أنظمة إدارة الإيصالات / Receipt management systems

يمكن دمجها بسهولة مع نماذج Odoo الموجودة.
Can be easily integrated with existing Odoo models.

## المساهمة / Contributing

للمساهمة في المشروع:
To contribute to the project:

1. التأكد من تمرير جميع الاختبارات / Ensure all tests pass
2. إضافة اختبارات للميزات الجديدة / Add tests for new features
3. اتباع معايير الترميز / Follow coding standards
4. توثيق التغييرات / Document changes

## الترخيص / License

هذا المشروع مطور لمشروع Juiceline
This project is developed for the Juiceline project

---

## مثال مفصل / Detailed Example

```python
#!/usr/bin/env python3
from update_receipt_and_create_journal_entry import *
from datetime import date

def detailed_example():
    """مثال مفصل على الاستخدام / Detailed usage example"""
    
    # إنشاء إيصالات تجريبية / Create sample receipts
    receipts = [
        Receipt(1, date(2024, 1, 15), 1000.00, description="فاتورة أ"),
        Receipt(2, date(2024, 1, 16), 1500.50, description="فاتورة ب"),
        Receipt(3, date(2024, 1, 17), 750.25, description="فاتورة ج"),
    ]
    
    print("=== حالة الإيصالات قبل التحديث ===")
    for receipt in receipts:
        print(f"إيصال {receipt.receipt_id}: "
              f"مجدول={receipt.scheduled_date}, "
              f"مستلم={receipt.date_received}, "
              f"مبلغ={receipt.amount}")
    
    # تطبيق التحديث / Apply update
    entries = update_receipt_and_create_journal_entry(receipts)
    
    print("\n=== حالة الإيصالات بعد التحديث ===")
    for receipt in receipts:
        print(f"إيصال {receipt.receipt_id}: "
              f"مجدول={receipt.scheduled_date}, "
              f"مستلم={receipt.date_received}, "
              f"مبلغ={receipt.amount}")
    
    print("\n=== قيود اليومية المنشأة ===")
    for entry in entries:
        print(f"قيد {entry.entry_id}: "
              f"تاريخ={entry.entry_date}, "
              f"مبلغ={entry.amount}, "
              f"وصف={entry.description}")

if __name__ == "__main__":
    detailed_example()
```

هذا المثال يوضح الاستخدام الكامل للوحدة مع عرض مفصل للنتائج.
This example demonstrates complete module usage with detailed results display.