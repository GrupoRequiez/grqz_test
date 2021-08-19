# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import date, datetime, timedelta
import logging
import base64
import tempfile
import os
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
import io

_logger = logging.getLogger(__name__)


class ProductRelocation(models.TransientModel):
    _name = 'product.relocation'
    _description = 'Product relocation'

    responsible = fields.Char("Responsible", required=True)  #
    source = fields.Char('Source', required=True)
    location_id = fields.Many2one('stock.location', 'Location origin', default=562, required=True)
    name = fields.Char('File Name', default='locations.txt')
    data_file = fields.Binary('File')
    getted = fields.Boolean('Getted', default=False)
    product_relocation_line_ids = fields.One2many(
        'product.relocation.line', 'product_relocation_id', 'Lines')

    def confirm(self):
        if self.product_relocation_line_ids:
            stock_picking_obj = self.env['stock.picking']
            stock_move_obj = self.env['stock.move']
            stock_move_line_obj = self.env['stock.move.line']
            for line in self.product_relocation_line_ids:
                product_id = self.env['product.product'].search(
                    [('default_code', '=', line.product)], limit=1)
                location_dest_id = self.env['stock.location'].search(
                    [('name', '=', line.location_dest)], limit=1)
                quant_obj = self.env['stock.quant']
                quantity = line.quantity
                if product_id and location_dest_id:
                    quant_id = quant_obj.search([
                        ('product_id', '=', product_id.id),
                        ('location_id', '=', line.location_id.id),
                        ('quantity', '>=', quantity)], order='id desc', limit=1)
                    picking_id = stock_picking_obj.create({
                        'company_id': self.env.company.id,
                        'date': fields.Datetime.now(),
                        'picking_type_id': 551,
                        'location_id': self.location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'move_type': 'direct',
                        'origin': self.source
                    })
                    move_id = stock_move_obj.create({
                        'company_id': self.env.company.id,
                        'date': fields.Datetime.now(),
                        'location_id': self.location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'name': self.source,
                        'procure_method': 'make_to_stock',
                        'product_id': product_id.id,
                        'product_uom': product_id.uom_id.id,
                        'product_uom_qty': quantity,
                        'picking_id': picking_id.id
                    })
                    picking_id.action_confirm()
                    if quant_id and product_id.tracking == 'lot':
                        stock_move_line_obj.create({
                            'company_id': self.env.company.id,
                            'date': fields.Datetime.now(),
                            'location_id': self.location_id.id,
                            'location_dest_id': location_dest_id.id,
                            'product_id': product_id.id,
                            'product_uom_id': product_id.uom_id.id,
                            'product_uom_qty': quantity,
                            'lot_id': quant_id.lot_id.id,
                            'lot_name': quant_id.lot_id.name,
                            'origin': self.source,
                            'picking_id': picking_id.id,
                            'reference': picking_id.name,
                            'move_id': move_id.id
                        })
                        picking_id.button_validate()
                    line.write({'status': 'Transfer created successfully'})
            self.getted = True
        else:
            raise exceptions.Warning("No lines to process")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.relocation',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def read_file(self):
        # Decode data
        data = base64.b64decode(self.data_file)
        # Save file
        file_name = '/tmp/%s' % self.name
        with open(file_name, 'wb') as file:
            file.write(data)
            file.close()

        file = open(file_name, 'r')
        lines = file.readlines()
        relocation_line_obj = self.env['product.relocation.line']
        for line in lines:
            relocation = line.split(',')
            relocation_line_obj.create({
                'product_relocation_id': self.id,
                'product': relocation[2],
                'quantity': relocation[4],
                'lot': relocation[3],
                'location_id': self.location_id.id,
                'location_dest': relocation[1]
            })
        file.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.relocation',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class ProductRelocationLine(models.TransientModel):
    _name = 'product.relocation.line'
    _description = 'Product relocation lines'

    product_relocation_id = fields.Many2one(
        'product.relocation', 'Product relocation', readonly=True)
    product = fields.Char('Product', required=True)
    status = fields.Char('Status')
    quantity = fields.Float('Quantity', required=True)
    location_id = fields.Many2one('stock.location', 'Location')
    location_dest = fields.Char('Location dest', required=True)
    lot = fields.Char('Lot')
