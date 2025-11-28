Setup:

- Install module *mrp_workorder_suborder_sale_info*
- Create Product A and B and enable routes *MTO* and *Manufacture* for both.
- Create BoM for Product A with at least Product B.


Check Sale Order and MTO:

- Create new Sale Order for Product A.
- Confirm that generated production order has reference to sale order (tab *Miscellaneous*)
- Confirm that generated cheild MO has same reference.


When you confirm MO for A → Odoo automatically creates a sub-production for B

✅ You want your custom field from A’s MO to be copied to the sub-production for B
