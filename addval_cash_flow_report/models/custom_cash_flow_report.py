# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
import logging
_logger = logging.getLogger(__name__)


class CustomCashFlowReport(models.AbstractModel):
    _name = 'custom.cash.flow.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Reporte flujo de caja'

    
    def _get_amls_fixed(self):
        
        amls_fixed = self.env["account.move.line"].search([("secondary_account_id", "=", 1)])

        # Initialize an empty dictionary to store the results
        account_balances = {}

        for aml in amls_fixed:

            account_id = aml.account_id.id

            # Check if the account_id is already in the dictionary
            if account_id not in account_balances:
                account_balances[account_id] = 0

            # Add or subtract based on debit or credit
            if aml.debit > 0:
                account_balances[account_id] += aml.debit
            elif aml.credit > 0:
                account_balances[account_id] -= aml.credit
        
        return account_balances
    
    def _get_layout_data(self):
        return {
            'operating_activites': {'name': _('Flujo de caja actividades operativas'), 'level': 0},
                'fixed': {'name': _('Fijo'), 'level': 2, 'parent_line_id': 'operating_activites'},
                'variable': {'name': _('Variable'), 'level': 2, 'parent_line_id': 'operating_activites'},

            'inversion_activites': {'name': _('Flujo caja actividades de inversion'), 'level': 0},
                'inversion': {'name': _('Inversión'), 'level': 2, 'parent_line_id': 'inversion_activites'},

            'financial_flow': {'name': _('Flujo de caja financiero'), 'level': 0},
                'fixed_cp': {'name': _('Fijo C/P'), 'level': 2, 'parent_line_id': 'financial_flow'},
                'fixed_lp': {'name': _('Fijo L/P'), 'level': 2, 'parent_line_id': 'financial_flow'},

            'unsorted_flow': {'name': _('Flujo sin clasificar'), 'level': 0},
                'dividend': {'name': _('Diviendo'), 'level': 2, 'parent_line_id': 'unsorted_flow'},
        }
    
