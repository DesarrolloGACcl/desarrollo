# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class PruchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution_area(self):
        for line in self:
            if not line.display_type:
                area_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_area = area_distribution or line.analytic_distribution_area

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution_activity(self):
        for line in self:
            if not line.display_type:
                activity_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_activity = activity_distribution or line.analytic_distribution_activity