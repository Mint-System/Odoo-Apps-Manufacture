import base64
import csv
import io
import logging

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Column header keywords (lowercase, no spaces) used to auto-detect the
# CSV delimiter and to sanity-check that the header row was found.
_EXPECTED_HEADERS = ['refdes', 'partnumber', 'label', 'description', 'quantity']
_CANDIDATE_DELIMITERS = [';', ',', '\t']


class MrpBomRefdesImport(models.TransientModel):
    _name = 'mrp.bom.refdes.import'
    _description = 'Import RefDes CSV into BOM component lines'

    csv_file = fields.Binary(string='CSV File', required=True)
    csv_filename = fields.Char(string='Filename')
    data_start_line = fields.Integer(
        string='Data starts at line', default=7,
        help="1-based line number of the first data row. The line "
             "immediately above this must be the column header row "
             "(RefDes;PartNumber;Label;Description;Quantity). Rows above "
             "that (title, 'Zusammenfassung', 'Erstellt', component "
             "counts) are skipped.")
    new_bom = fields.Boolean(
        string='Create New BOM',
        help="If no BOM exists yet for the product in cell A1, create one "
             "and add each matched component as a new BOM line instead of "
             "raising an error.",
        default=False)
    result_log = fields.Text(string='Import Log', readonly=True)

    def _decode(self, raw):
        for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        raise UserError(_("Could not decode the CSV file. Please check its encoding."))

    def _norm(self, value):
        # Strip regular + non-breaking spaces that often survive copy/paste
        # or spreadsheet exports.
        return (value or '').replace('\xa0', ' ').strip()

    def _detect_delimiter(self, header_line):
        """Pick the delimiter whose split of the header line matches the
        most expected column keywords. More reliable than csv.Sniffer here
        because the file's first few lines are free text, not tabular."""
        best_delim, best_score = ';', -1
        for delim in _CANDIDATE_DELIMITERS:
            try:
                parts = next(csv.reader([header_line], delimiter=delim))
            except StopIteration:
                continue
            normalized = [p.lower().replace(' ', '') for p in parts]
            score = sum(1 for exp in _EXPECTED_HEADERS
                        if any(exp in p for p in normalized))
            if score > best_score:
                best_delim, best_score = delim, score
        return best_delim, best_score

    def _parse_qty(self, value):
        value = self._norm(value).replace(',', '.')
        try:
            qty = float(value)
            return qty if qty > 0 else 1.0
        except (TypeError, ValueError):
            return 1.0

    def action_import(self):
        self.ensure_one()
        if not self.csv_file:
            raise UserError(_("Please attach a CSV file first."))

        raw = base64.b64decode(self.csv_file)
        text = self._decode(raw)
        lines = text.splitlines()
        if not lines:
            raise UserError(_("The CSV file appears to be empty."))

        header_index = max(self.data_start_line - 2, 0)
        if header_index >= len(lines):
            raise UserError(_("The file has fewer lines than 'Data starts at line' implies."))
        header_line = lines[header_index]

        delimiter, score = self._detect_delimiter(header_line)
        if score <= 0:
            raise UserError(_(
                "Could not find the column header row (RefDes;PartNumber;"
                "Label;Description;Quantity) at line %s. Check 'Data starts "
                "at line' - it must be exactly one more than the header "
                "line number.") % (header_index + 1))

        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))

        # A1 = default_code of the product this BOM is for.
        bom_default_code = self._norm(rows[0][0]) if rows and rows[0] else ''

        if not bom_default_code:
            raise UserError(_("Cell A1 does not contain a default code."))

        bom_default_code = bom_default_code.replace("_", ".").lower()

        product = self.env['product.product'].search(
            [('default_code', '=', bom_default_code)], limit=1)
        if not product:
            template = self.env['product.template'].search(
                [('default_code', '=', bom_default_code)], limit=1)
            product = template.product_variant_id if template else self.env['product.product']
        if not product:
            raise UserError(_("No product found with default code '%s' (cell A1).") % bom_default_code)

        bom = self.env['mrp.bom'].search([
            '|',
            ('product_id', '=', product.id),
            '&', ('product_id', '=', False), ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ], limit=1)
        created_bom = False
        if not bom:
            if not self.new_bom:
                raise UserError(_("No BOM found for product '%s'. Tick 'Create "
                                   "New BOM' to have one created automatically.") % product.display_name)
            bom = self.env['mrp.bom'].create({
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'product_qty': 1.0,
                'type': 'normal',
            })
            created_bom = True

        # Preload a code -> product map once, instead of a DB search per row.
        # Keep an exact map (preferred) and a lowercase fallback map, so a
        # capitalization mismatch between the CSV and Odoo doesn't silently
        # skip the line.
        all_products = self.env['product.product'].search([('default_code', '!=', False)])
        code_map = {}
        code_map_lower = {}
        for p in all_products:
            code = self._norm(p.default_code)
            if not code:
                continue
            code_map[code] = p
            code_map_lower.setdefault(code.lower(), p)

        # Index BOM lines by product for quick lookup / to make sure we only
        # touch lines that actually belong to this BOM.
        line_by_product = {line.product_id.id: line for line in bom.bom_line_ids}

        start_index = max(self.data_start_line - 1, 0)
        data_rows = rows[start_index:]

        log_lines = [_("BOM: %s (product: %s)%s - delimiter detected: %r") % (
            bom.display_name, product.display_name,
            _(' [newly created]') if created_bom else '', delimiter)]
        matched = 0
        unmatched = []

        # Fixed columns, confirmed from the actual export format:
        # RefDes (comma list);PartNumber;Label;Description;Quantity
        for row_no, row in enumerate(data_rows, start=self.data_start_line):
            if not any((c or '').strip() for c in row):
                continue  # blank line

            if len(row) < 2:
                unmatched.append(_("Line %s: expected at least RefDes and "
                                    "PartNumber columns, got %s") % (row_no, row))
                continue

            refdes_field = self._norm(row[0])
            part_number = self._norm(row[1])

            refdes_values = [self._norm(v) for v in refdes_field.split(',')]
            refdes_str = ','.join(v for v in refdes_values if v)

            matched_product = code_map.get(part_number) or code_map_lower.get(part_number.lower())
            if not matched_product:
                unmatched.append(_("Line %s: no product with default code "
                                    "'%s'") % (row_no, part_number))
                continue

            qty = self._parse_qty(row[4]) if len(row) > 4 else 1.0

            bom_line = line_by_product.get(matched_product.id)
            if not bom_line:
                if not self.new_bom:
                    unmatched.append(_("Line %s: part '%s' matched a product but is not a "
                                        "component of BOM %s") % (row_no, matched_product.default_code,
                                                                   bom.display_name))
                    continue
                bom_line = self.env['mrp.bom.line'].create({
                    'bom_id': bom.id,
                    'product_id': matched_product.id,
                    'product_qty': qty,
                    'product_uom_id': matched_product.uom_id.id,
                })
                line_by_product[matched_product.id] = bom_line
            elif bom_line.product_qty != qty:
                bom_line.product_qty = qty

            # NOTE: this assumes ref_des lives on mrp.bom.line (one BOM can
            # have many components, each with its own RefDes list). If the
            # field currently only exists on mrp.bom, move/recreate it on the
            # BOM line model first.
            bom_line.ref_des = refdes_str
            matched += 1
            log_lines.append(_("Line %s: %s -> refdes %s, qty %s") % (
                row_no, matched_product.default_code, refdes_str, qty))

        log_lines.append(_("\n%s line(s) updated, %s line(s) skipped/unmatched.") % (matched, len(unmatched)))
        log_lines.extend(unmatched)

        self.result_log = '\n'.join(log_lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
