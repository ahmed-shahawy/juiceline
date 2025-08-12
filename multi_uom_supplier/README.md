# Multi UOM Supplier Module

## Overview

The Multi UOM Supplier module extends Odoo's purchasing functionality to support different units of measure (UOM) for the same product from different suppliers. This solves the common business problem where suppliers sell the same product using different units of measure.

## Problem Solved

In standard Odoo, each product can only have one purchase UOM. This creates issues when:
- Supplier A sells Product X in "Units" 
- Supplier B sells the same Product X in "Dozens"
- Supplier C sells Product X in "Cases"

Without this module, you would need to create separate products or manually convert quantities, leading to confusion and errors.

## Features

### Core Functionality
- **Supplier-Specific UOM**: Assign different UOMs to each supplier for the same product
- **Automatic Conversion**: Seamless conversion between supplier UOM and product purchase UOM
- **Purchase Order Integration**: Purchase orders automatically use the correct supplier UOM
- **Price Management**: Prices are maintained in the supplier's UOM for accuracy

### Key Benefits
- ✅ Eliminate manual UOM conversions
- ✅ Reduce purchase order errors
- ✅ Maintain accurate supplier pricing
- ✅ Streamline procurement processes
- ✅ Support complex multi-supplier scenarios

## Technical Implementation

### Models Extended

#### product.supplierinfo
- **supplier_uom_id**: Many2one field linking to uom.uom for supplier-specific UOM
- **supplier_uom_factor**: Computed field showing conversion factor to product UOM
- **Validation**: Ensures supplier UOM belongs to same category as product UOM
- **Methods**: Price and quantity conversion utilities

#### purchase.order.line
- **supplier_uom_id**: Computed field showing the supplier's UOM
- **Onchange Logic**: Automatically updates UOM when product/supplier changes
- **Integration**: Seamless integration with purchase workflow

### Views Enhanced

#### Product Management
- Supplier information forms now include UOM selection
- Tree views show supplier UOM for quick reference
- Domain restrictions ensure compatible UOM categories

#### Purchase Orders
- Purchase order lines display supplier UOM information
- Automatic UOM selection based on supplier configuration

## Installation

1. Copy the `multi_uom_supplier` folder to your Odoo addons directory
2. Update your Odoo app list
3. Install the "Multi UOM Supplier" module
4. Configure supplier UOMs in Product → Purchase → Vendor Bills

## Configuration

### Setting Up Supplier UOMs

1. **Navigate to Product**: Go to Inventory → Products → Products
2. **Edit Product**: Select a product that you purchase from multiple suppliers
3. **Access Purchase Tab**: Click on the "Purchase" tab
4. **Configure Suppliers**: In the vendor list:
   - Select a supplier
   - Set the price in their UOM
   - Choose the "Supplier UOM" field
   - Ensure it's compatible with the product's purchase UOM category

### Example Configuration

**Product**: Office Paper  
**Default Purchase UOM**: Ream (500 sheets)

**Supplier A**: 
- Price: $5.00 per Ream
- Supplier UOM: Ream (default)

**Supplier B**: 
- Price: $48.00 per Case  
- Supplier UOM: Case (10 Reams)

**Supplier C**:
- Price: $0.01 per Sheet
- Supplier UOM: Sheet

## Usage Workflow

### Creating Purchase Orders

1. **Create Purchase Order**: Go to Purchase → Purchase → Purchase Orders
2. **Select Supplier**: Choose your supplier
3. **Add Product**: Select the product
4. **Automatic UOM**: The system automatically:
   - Uses the supplier's configured UOM
   - Converts quantities as needed
   - Maintains correct pricing

### Quantity Conversion Examples

**Scenario**: Ordering 5 Reams from Supplier B (who sells in Cases)
- **You Request**: 5 Reams
- **System Converts**: 0.5 Cases (5 ÷ 10)
- **PO Shows**: 0.5 Cases at $48.00 each
- **Total Cost**: $24.00

## Demo Data

The module includes demo data showcasing:
- A demo product configured for UOM testing
- Two suppliers with different UOMs (Units vs Dozens)
- Sample pricing for each supplier

## Technical Notes

### UOM Category Validation
- Supplier UOMs must belong to the same category as the product's purchase UOM
- The system prevents incompatible UOM assignments (e.g., mixing Weight and Length categories)

### Conversion Logic
- Uses Odoo's native UOM conversion system
- Maintains precision and rounding rules
- Handles complex conversion factors automatically

### Performance Considerations
- Conversion factors are computed fields for efficiency
- Database queries are optimized for supplier lookups
- Minimal impact on existing purchase workflows

## Compatibility

- **Odoo Version**: 18.0+
- **Dependencies**: base, product, purchase, uom
- **Conflicts**: None known
- **Integration**: Compatible with standard Odoo purchase modules

## Troubleshooting

### Common Issues

**Issue**: UOM not appearing in supplier list
**Solution**: Ensure the UOM belongs to the same category as the product's purchase UOM

**Issue**: Incorrect quantity conversion
**Solution**: Verify the UOM conversion factors in Inventory → Configuration → Units of Measure

**Issue**: Price calculations seem wrong
**Solution**: Remember that prices are stored in the supplier's UOM, not the product UOM

## Support

For issues, enhancements, or questions:
- GitHub: https://github.com/ahmed-shahawy/juiceline
- Module Author: Ahmed Shahawy

## License

LGPL-3 - See LICENSE file for details

## Changelog

### Version 18.0.1.0.0
- Initial release
- Core supplier UOM functionality
- Purchase order integration
- UI enhancements
- Demo data included