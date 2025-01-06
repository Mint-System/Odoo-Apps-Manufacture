Setup products:

- Enable *Lots & Serial Numbers* (Settings > Inventory > Traceability)
- Enable *Work Orders* (Settings > Manufacturing > Operations)
- Set *Reservation Method* on the Operation Type *Manufacturing* to *Manually* (Inventory > Configuration > Warehouse Management > Operation Types > Manufacturing)
- Create a product "A" with Product Type *Storable  Product*
- Create two products "B" and "C" with Product Type *Storable  Product* and tracking *By Lots* enabled
- Create the lots 1 and 2 for each Component B and C (Inventory > Products > Lots/Serial Numbers)
- Edit the On Hand Quantity for the products Component "B" and "C".
Set "Counted Quantity" to 10 for each Lot 1 and 2.
- Create a Bill of Materials for the product "Product" with the two components "B" and "C"
- Create operation "Assemble" and assign to both components

Manufacturing order:

- Create a new production order for 10 products "A" and click confirm
- Show row *Lot/Serial Numbers* in the components list
- On the line item 1 "B" select Lot "1" with the quantity done 10 and confirm
- On the line item 2 "C" select Lot "1" with the quantity done 10, then select Lot "2" with 10 and confirm
- Open the tablet view of the workorder *Operation 1*
- Set product quantity for "A" to 5 then
- Register consumed materials, select Lot 1 for B and Lot 2 for C with 5 units each
- The list of available lots should only show the lots which were assigned in the production order
- Press button *Mark as done*
- A new backorder should be created
