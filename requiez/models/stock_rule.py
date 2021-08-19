# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.addons.stock.models.stock_rule import ProcurementException


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_manufacture(self, procurements):
        productions_values_by_company = defaultdict(list)
        errors = []
        for procurement, rule in procurements:
            bom = rule._get_matching_bom(procurement.product_id,
                                         procurement.company_id, procurement.values)
            if not bom:
                msg = _('There is no Bill of Material of type manufacture or kit found for the product %s. Please define a Bill of Material for this product.') % (
                    procurement.product_id.display_name,)
                errors.append((procurement, msg))

            productions_values_by_company[procurement.company_id.id].append(
                rule._prepare_mo_vals(*procurement, bom))

        if errors:
            raise ProcurementException(errors)

        for company_id, productions_values in productions_values_by_company.items():
            # creck if already exists someone mrp production order with the same production
            productions_values_check = []
            for p in productions_values:
                print(">>>>>>>>>>>>>>>>>>>>> p:", p)
                current_qty = p['product_qty']
                mrp_production_ids = self.env['mrp.production'].search([
                    ('product_id', '=', p['product_id']),
                    ('origin', '=', p['origin']),
                    ('state', 'not in', ('cancel', 'done', 'draft'))], order='id')
                if mrp_production_ids:
                    mrp_qty = sum(m.product_qty for m in mrp_production_ids)
                    diff_qty = current_qty-mrp_qty
                    if diff_qty > 0:
                        p['product_qty'] = diff_qty
                        productions_values_check.append(p)
                    else:
                        break
                else:
                    productions_values_check.append(p)

            productions_values = productions_values_check
            print(">>>>>>>>>>>>>>>>>>>>> productions_values_check:", productions_values_check)

            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(
                SUPERUSER_ID).sudo().with_company(company_id).create(productions_values)
            self.env['stock.move'].sudo().create(productions._get_moves_raw_values())
            self.env['stock.move'].sudo().create(productions._get_moves_finished_values())
            productions._create_workorder()
            productions.filtered(lambda p: p.move_raw_ids).action_confirm()

            for production in productions:
                origin_production = production.move_dest_ids and production.move_dest_ids[
                    0].raw_material_production_id or False
                orderpoint = production.orderpoint_id
                if orderpoint:
                    production.message_post_with_view('mail.message_origin_link',
                                                      values={'self': production,
                                                              'origin': orderpoint},
                                                      subtype_id=self.env.ref('mail.mt_note').id)
                if origin_production:
                    production.message_post_with_view('mail.message_origin_link',
                                                      values={'self': production,
                                                              'origin': origin_production},
                                                      subtype_id=self.env.ref('mail.mt_note').id)
        return True
        # res = super(StockRule, self)._run_manufacture(procurements)
        # print res
