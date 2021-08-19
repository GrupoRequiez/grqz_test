# Copyright 2018 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.tools import float_compare, float_is_zero, html_escape


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False):
        self = self.with_context(from_planned=True)
        return super(ProcurementGroup, self).run_scheduler(
            use_new_cursor, company_id)
