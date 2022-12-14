# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    latest_bom_id = fields.Many2one('mrp.bom', compute="_compute_latest_bom_id")

    @api.depends('bom_id', 'bom_id.active')
    def _compute_latest_bom_id(self):
        self.latest_bom_id = False
        for po in self:
            if po.bom_id and not po.bom_id.active:
                po.latest_bom_id = po.bom_id._get_active_version()

    def action_update_bom(self):
        for production in self:
            if production.state != 'draft' or not production.latest_bom_id:
                continue
            (production.move_finished_ids | production.move_raw_ids).unlink()
            production.workorder_ids.unlink()
            production.write({'bom_id': production.latest_bom_id.id})
            production.env['stock.move'].create(production._get_moves_raw_values())
            production.env['stock.move'].create(production._get_moves_finished_values())
            production._create_workorder()
