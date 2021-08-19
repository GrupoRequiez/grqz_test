# Copyright 2018 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo import fields, models, api, exceptions, _
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    user_id = fields.Many2one(default=None, required=False)
    client_order_ref = fields.Char(required=False, copy=True)
    date_promised = fields.Datetime('Date promised', required=False)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """If the partner does not have a salesman this field should be filled
        out manually
        """
        res = super(SaleOrder, self).onchange_partner_id()
        values = {
            'user_id': self.partner_id.user_id.id
        }
        self.update(values)
        return res

    def action_confirm(self):
        if not self.user_id:
            raise exceptions.Warning(_("Vendor has not been assigned!!!!"))
        elif not self.type_id:
            raise exceptions.Warning(_("Type has not been assigned!!!!"))
        elif not self.client_order_ref:
            raise exceptions.Warning(_("Client order ref has not been assigned!!!!"))
        elif not self.date_promised:
            raise exceptions.Warning(_("Date planned has not been assigned!!!!"))
        else:
            payment_term_credits = (
                [payment
                 for payment in (self.env['account.payment.term'].search([]))
                 if payment.line_ids[-1] and payment.line_ids[-1].days >= 0])
            for order in self.filtered(lambda r: r.payment_term_id
                                       in payment_term_credits):
                if (not order.partner_id.expired_ignore
                        and order.partner_id.credit_expired):
                    raise exceptions.Warning(
                        _("AT THE MOMENT, IT'S NOT AUTHORIZE A CREDIT SALE. "
                          "THE CLIENT HAS EXPIRED BALANCE "
                          "ON PREVIOUS INVOICES!. "
                          "FOR MORE INFORMATION CHECK INVOICING!"))
                company_currency = self.env.user.company_id.currency_id
                total = order.currency_id.compute(order.amount_total,
                                                  company_currency)
                credit_used = order.partner_id.credit_used
                if not order.partner_id.credit_ignore and (
                        (credit_used + total) > order.partner_id.credit_limit):
                    raise exceptions.Warning(
                        _("THE CLIENT DOESN'T HAVE ENOUGH "
                          "CREDIT FOR THE SALE!, "
                          "FOR MORE INFORMATION CHECK INVOICING!"))
            super(SaleOrder, self).action_confirm()

    @api.onchange('expected_date')
    def onchange_partner_shipping_id(self):
        # self.date_promised = self.commitment_date
        self.date_promised = self.expected_date
        self.commitment_date = self.expected_date
        return {}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        vals['date_planned'] = self.order_id.date_promised
        return vals

    # def _action_launch_stock_rule(self, previous_product_uom_qty=False):
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     procurements = []
    #     for line in self:
    #         line = line.with_company(line.company_id)
    #         if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
    #             continue
    #         qty = line._get_qty_procurement(previous_product_uom_qty)
    #         if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
    #             continue
    #
    #         group_id = line._get_procurement_group()
    #         if not group_id:
    #             group_id = self.env['procurement.group'].create(
    #                 line._prepare_procurement_group_vals())
    #             line.order_id.procurement_group_id = group_id
    #         else:
    #             # In case the procurement group is already created and the order was
    #             # cancelled, we need to update certain values of the group.
    #             updated_vals = {}
    #             if group_id.partner_id != line.order_id.partner_shipping_id:
    #                 updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
    #             if group_id.move_type != line.order_id.picking_policy:
    #                 updated_vals.update({'move_type': line.order_id.picking_policy})
    #             if updated_vals:
    #                 group_id.write(updated_vals)
    #
    #         values = line._prepare_procurement_values(group_id=group_id)
    #         product_qty = line.product_uom_qty - qty
    #
    #         line_uom = line.product_uom
    #         quant_uom = line.product_id.uom_id
    #         product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
    #         procurements.append(self.env['procurement.group'].Procurement(
    #             line.product_id, product_qty, procurement_uom,
    #             line.order_id.partner_shipping_id.property_stock_customer,
    #             line.name, line.order_id.name, line.order_id.company_id, values))
    #     if procurements:
    #         print(">>>>>>>>>>>>>>>>>>> procurements ", procurements)
    #         self.env['procurement.group'].run(procurements)
    #     return True
