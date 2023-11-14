# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('account_id', 'partner_id', 'product_id')
    def _compute_analytic_distribution(self):
        for line in self:
            if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
                distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.partner_id.id,
                    "partner_category_id": line.partner_id.category_id.ids,
                    "account_prefix": line.account_id.code,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution = distribution or line.analytic_distribution
                
    @api.depends('account_id', 'partner_id', 'product_id')
    def _compute_analytic_distribution_area(self):
        for line in self:
            if not line.display_type:
                area_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "account_prefix": line.account_id.code,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_area = area_distribution or line.analytic_distribution_area

    @api.depends('account_id', 'partner_id', 'product_id')
    def _compute_analytic_distribution_activity(self):
        for line in self:
            if not line.display_type:
                activity_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "account_prefix": line.account_id.code,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution_activity = activity_distribution or line.analytic_distribution_activity