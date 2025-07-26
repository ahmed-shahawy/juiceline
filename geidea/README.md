# Geidea Payment Integration Module

## نظرة عامة | Overview

هذا الموديول يوفر تكامل مع أجهزة الدفع من Geidea لنظام نقاط البيع في Odoo.

This module provides integration with Geidea payment devices for Odoo Point of Sale system.

## الميزات | Features

### العربية
- **تكوين أجهزة Geidea**: إعداد وتكوين أجهزة الدفع من Geidea
- **معالجة المدفوعات**: معالجة آمنة للمدفوعات عبر API الخاص بـ Geidea
- **تكامل POS**: تكامل سلس مع واجهة نقاط البيع
- **مراقبة الحالة**: تتبع حالة المعاملات في الوقت الفعلي
- **إدارة البيئات**: دعم بيئات الاختبار والإنتاج
- **أمان البيانات**: حماية معلومات الدفع الحساسة

### English
- **Geidea Device Configuration**: Setup and configure Geidea payment devices
- **Payment Processing**: Secure payment processing via Geidea API
- **POS Integration**: Seamless integration with Point of Sale interface
- **Status Monitoring**: Real-time transaction status tracking
- **Environment Management**: Support for test and production environments
- **Data Security**: Protection of sensitive payment information

## التثبيت | Installation

### المتطلبات | Requirements
- Odoo 18.0+
- Point of Sale module
- Payment module
- Internet connection for API communication

### خطوات التثبيت | Installation Steps

1. **نسخ الموديول | Copy Module**
   ```bash
   cp -r geidea /path/to/odoo/addons/
   ```

2. **تفعيل وضع المطور | Enable Developer Mode**
   - Settings > General Settings > Developer Tools > Activate Developer Mode

3. **تحديث قائمة التطبيقات | Update Apps List**
   - Apps > Update Apps List

4. **تثبيت الموديول | Install Module**
   - Apps > Search "Geidea" > Install

## التكوين | Configuration

### إعداد جهاز Geidea | Geidea Acquirer Setup

1. **الانتقال إلى إعدادات Geidea | Navigate to Geidea Settings**
   ```
   Geidea Payments > Configuration > Payment Acquirers
   ```

2. **إنشاء جهاز جديد | Create New Acquirer**
   - Name: اسم وصفي للجهاز | Descriptive name for the device
   - Merchant ID: معرف التاجر من Geidea | Merchant ID from Geidea
   - Terminal ID: معرف الطرفية | Terminal ID
   - API Key: مفتاح API | API Key
   - API Secret: سر API | API Secret
   - Environment: Test أو Production | Test or Production

3. **اختبار الاتصال | Test Connection**
   - Click "Test Connection" button
   - Verify successful connection

### إعداد نقطة البيع | POS Configuration

1. **تفعيل Geidea في POS | Enable Geidea in POS**
   ```
   Point of Sale > Configuration > Point of Sale > [Your POS]
   ```

2. **تكوين الإعدادات | Configure Settings**
   - Enable "Enable Geidea Payments"
   - Select the configured Geidea Acquirer
   - Save configuration

## الاستخدام | Usage

### معالجة الدفعات في POS | Payment Processing in POS

1. **إنشاء طلب | Create Order**
   - Add products to cart
   - Click "Payment"

2. **اختيار طريقة الدفع | Select Payment Method**
   - Choose Geidea payment method
   - Enter payment amount

3. **معالجة الدفع | Process Payment**
   - Payment request sent to Geidea automatically
   - Monitor payment status in real-time
   - Complete transaction when approved

### مراقبة المعاملات | Transaction Monitoring

1. **عرض المعاملات | View Transactions**
   ```
   Geidea Payments > Transactions > Payment Transactions
   ```

2. **حالات المعاملات | Transaction States**
   - **Draft**: مسودة | Draft
   - **Pending**: في الانتظار | Pending
   - **Authorized**: مخول | Authorized
   - **Captured**: مكتمل | Captured
   - **Cancelled**: ملغي | Cancelled
   - **Error**: خطأ | Error

## API Documentation

### Controllers Available

#### Payment Operations
- `POST /geidea/payment/create` - Create payment transaction
- `POST /geidea/payment/process` - Process payment
- `POST /geidea/payment/status` - Check payment status
- `POST /geidea/payment/capture` - Capture authorized payment
- `POST /geidea/payment/cancel` - Cancel payment

#### Configuration
- `POST /geidea/acquirer/test` - Test acquirer connection
- `GET /geidea/pos/acquirers` - Get POS acquirers

#### Callbacks
- `POST /geidea/payment/callback` - Payment callback handler
- `GET /geidea/payment/return` - Payment return URL handler

### JavaScript Integration

The module provides `GeideaPaymentInterface` class for POS frontend integration:

```javascript
// Payment interface usage
const geidea = new GeideaPaymentInterface();
await geidea.send_payment_request(cid);
```

## الأمان | Security

### إعدادات الصلاحيات | Access Rights
- **User**: قراءة المعاملات | Read transactions
- **POS Manager**: إدارة كاملة | Full management
- **POS User**: إنشاء معاملات | Create transactions

### حماية البيانات | Data Protection
- API keys stored securely
- Encrypted communication with Geidea
- Audit trail for all transactions

## استكشاف الأخطاء | Troubleshooting

### مشاكل شائعة | Common Issues

1. **فشل الاتصال | Connection Failure**
   ```
   Check API credentials and network connectivity
   Verify Geidea service status
   ```

2. **انتهاء مهلة الدفع | Payment Timeout**
   ```
   Increase timeout in acquirer settings
   Check Geidea API response times
   ```

3. **خطأ في التفويض | Authorization Error**
   ```
   Verify API key and secret
   Check merchant and terminal IDs
   ```

### السجلات | Logs

Monitor logs for debugging:
```bash
grep -i geidea /var/log/odoo/odoo-server.log
```

## الدعم | Support

### التوثيق | Documentation
- Geidea API Documentation: [https://docs.geidea.net](https://docs.geidea.net)
- Odoo POS Documentation: [https://www.odoo.com/documentation](https://www.odoo.com/documentation)

### المساعدة التقنية | Technical Support
- Check module logs for error details
- Verify API credentials with Geidea
- Test in staging environment first

## الترخيص | License

This module is licensed under OPL-1 (Odoo Proprietary License).

## المساهمة | Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Submit pull request

## التحديثات | Updates

### الإصدار 18.0.1.0 | Version 18.0.1.0
- Initial release
- Basic Geidea integration
- POS frontend support
- Transaction management
- Configuration interface

## الأسئلة الشائعة | FAQ

**Q: هل يدعم الموديول العملات المتعددة؟ | Does the module support multiple currencies?**
A: نعم، يدعم العملات المختلفة حسب إعدادات Geidea | Yes, supports different currencies based on Geidea settings.

**Q: هل يمكن استخدام أكثر من جهاز Geidea؟ | Can I use multiple Geidea devices?**
A: نعم، يمكن تكوين عدة أجهزة وربطها بنقاط بيع مختلفة | Yes, multiple devices can be configured for different POS locations.

**Q: ما هي متطلبات الشبكة؟ | What are the network requirements?**
A: اتصال إنترنت مستقر للتواصل مع API الخاص بـ Geidea | Stable internet connection for Geidea API communication.