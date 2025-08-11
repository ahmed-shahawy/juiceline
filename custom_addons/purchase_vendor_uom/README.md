# Purchase Vendor UoM (Odoo 18)

Vendor-specific Purchase Unit of Measure per supplier, auto-applied on Purchase Orders.

## Features
- New field on product.supplierinfo: Vendor Purchase UoM.
- Validation: must match the category of the product's base UoM.
- Purchase Order line defaults to the vendor's UoM for the selected vendor and product.

## Install
1. Copy this module to your addons path (e.g., custom_addons/purchase_vendor_uom).
2. Update Apps list and install "Purchase Vendor UoM".

## Use
- Product > Purchase tab > Vendors: set "Vendor Purchase UoM" per vendor.
- Create a Purchase Order for that vendor; when adding the product, the line UoM will use the vendor's UoM if defined.

## Notes
- Does not change the product-level Purchase Unit; it only applies per vendor.
- Respects Odoo UoM conversions and categories.