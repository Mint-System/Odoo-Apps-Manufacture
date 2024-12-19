Setup products:

- Enable *Lots & Serial Numbers* (Settings > Inventory > Traceability)
- Enable *Work Orders* (Settings > Manufacturing > Operations)
- Set *Reservation Method* on the Operation Type *Manufacturing* to *Manually* (Inventory > Configuration > Warehouse Management > Operation Types > Manufacturing)
- Create a product ("Product") with Product Type *Storable  Product*
- Create two products ("Component 1" and "Component2") with Product Type *Storable  Product* and*By Lots* enabled (> product tab *Inventory* > Tracking)
- Create the lots 1A, 1B and 1C for Component 1 and 2A, 2B and 2C for Component 2 (Inventory > Products > Lots/Serial Numbers)
- Edit the On Hand Quantity for the products Component 1 and 2. Set "Counted Quantity" to 10 for each Lot A, B and C
- Create a Bill of Materials for the product "Product" with the two components ("Component 1" and "Component 2")
- Create operation in the Bill of Materials

Manufacturing order:

- Create a new production order for 30 products ("Product") and click confirm
- Show row *Lot/Serial Numbers* in the components list
- On the line item 1 ("Component 1") select Lot "1B" with the quantity done 10 and Lot "1C" with the quantity done 20, confirm
- On the line item 2 ("Component 2") select Lot "2A" with the quantity done 10 and the Lot "2C" with the quantity done 20, confirm
- Check availability
- Open the tablet view of the workorder *Operation 1*
- Set product quantity (qty_producing) to 20
- *Mark as done* operation 1
- Open the tablet view of the workorder *Operation 2*
- Register consumed materials
- The list of available lots should only show the lots which were assigned in the production order
- Push button *Mark as done and close MO*
- A backorder 2 is created and the assigned lots (from workorder 1) has been copied
