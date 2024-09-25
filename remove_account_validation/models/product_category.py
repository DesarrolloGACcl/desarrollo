# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.constrains('property_stock_valuation_account_id', 'property_stock_account_output_categ_id', 'property_stock_account_input_categ_id')
    def _check_valuation_accouts(self):
        # Prevent to set the valuation account as the input or output account.
        for category in self:
            valuation_account = category.property_stock_valuation_account_id
            input_and_output_accounts = category.property_stock_account_input_categ_id | category.property_stock_account_output_categ_id
        #REMOVE NATIVE VALIDATION

    
