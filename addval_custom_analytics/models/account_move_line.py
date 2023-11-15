# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import ast
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, timedelta
from functools import lru_cache

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import frozendict, formatLang, format_date, float_compare, Query
from odoo.tools.sql import create_index
from odoo.addons.web.controllers.utils import clean_action

from odoo.addons.account.models.account_move import MAX_HASH_VERSION

import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_distribution = fields.Json(
        inverse="_inverse_analytic_distribution",
    ) 

    analytic_distribution_area = fields.Json(
        inverse="_inverse_analytic_distribution",
    ) 

    analytic_distribution_activity = fields.Json(
        inverse="_inverse_analytic_distribution",
    ) 

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'account_id', 'group_tax_id', 'analytic_distribution', 'analytic_distribution_area', 'analytic_distribution_activity')
    def _compute_tax_key(self):
        for line in self:
            if line.tax_repartition_line_id:
                line.tax_key = frozendict({
                    'tax_repartition_line_id': line.tax_repartition_line_id.id,
                    'group_tax_id': line.group_tax_id.id,
                    'account_id': line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': line.analytic_distribution,
                    'analytic_distribution_area': line.analytic_distribution_area,
                    'analytic_distribution_activity': line.analytic_distribution_activity,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                    'tax_tag_ids': [(6, 0, line.tax_tag_ids.ids)],
                    'partner_id': line.partner_id.id,
                    'move_id': line.move_id.id,
                    'display_type': 'epd' if line.name and _('(Discount)') in line.name else line.display_type,
                })
            else:
                line.tax_key = frozendict({'id': line.id})

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'analytic_distribution_area', 'analytic_distribution_activity', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit', 'quantity')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
                    'analytic_distribution_area': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution_area,
                    'analytic_distribution_activity': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution_activity,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                    'display_type': line.display_type,
                }): {
                    'name': tax['name'] + (' ' + _('(Discount)') if line.display_type == 'epd' else ''),
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }

    @api.depends('tax_ids', 'account_id', 'company_id')
    def _compute_epd_key(self):
        for line in self:
            if line.display_type == 'epd' and line.company_id.early_pay_discount_computation == 'mixed':
                line.epd_key = frozendict({
                    'account_id': line.account_id.id,
                    'analytic_distribution': line.analytic_distribution,
                    'analytic_distribution_area': line.analytic_distribution_area,
                    'analytic_distribution_activity': line.analytic_distribution_activity,
                    'tax_ids': [Command.set(line.tax_ids.ids)],
                    'tax_tag_ids': [Command.set(line.tax_tag_ids.ids)],
                    'move_id': line.move_id.id,
                })
            else:
                line.epd_key = False

    @api.depends('move_id.needed_terms', 'account_id', 'analytic_distribution', 'analytic_distribution_area', 'analytic_distribution_activity', 'tax_ids', 'tax_tag_ids', 'company_id')
    def _compute_epd_needed(self):
        for line in self:
            needed_terms = line.move_id.needed_terms
            line.epd_dirty = True
            line.epd_needed = False
            if line.display_type != 'product' or not line.tax_ids.ids or line.company_id.early_pay_discount_computation != 'mixed':
                continue

            amount_total = abs(sum(x['amount_currency'] for x in needed_terms.values()))
            percentages_to_apply = []
            names = []
            for term in needed_terms.values():
                if term.get('discount_percentage'):
                    percentages_to_apply.append({
                        'discount_percentage': term['discount_percentage'],
                        'term_percentage': abs(term['amount_currency'] / amount_total) if amount_total else 0
                    })
                    names.append(f"{term['discount_percentage']}%")

            discount_percentage_name = ', '.join(names)
            epd_needed = {}
            for percentages in percentages_to_apply:
                percentage = percentages['discount_percentage'] / 100
                line_percentage = percentages['term_percentage']
                taxes = line.tax_ids.filtered(lambda t: t.amount_type != 'fixed')
                epd_needed_vals = epd_needed.setdefault(
                    frozendict({
                        'move_id': line.move_id.id,
                        'account_id': line.account_id.id,
                        'analytic_distribution': line.analytic_distribution,
                        'analytic_distribution_area': line.analytic_distribution_area,
                        'analytic_distribution_activity': line.analytic_distribution_activity,
                        'tax_ids': [Command.set(taxes.ids)],
                        'tax_tag_ids': line.compute_all_tax[frozendict({'id': line.id})]['tax_tag_ids'],
                        'display_type': 'epd',
                    }),
                    {
                        'name': _("Early Payment Discount (%s)", discount_percentage_name),
                        'amount_currency': 0.0,
                        'balance': 0.0,
                        'price_subtotal': 0.0,
                    },
                )
                epd_needed_vals['amount_currency'] -= line.currency_id.round(line.amount_currency * percentage * line_percentage)
                epd_needed_vals['balance'] -= line.currency_id.round(line.balance * percentage * line_percentage)
                epd_needed_vals['price_subtotal'] -= line.currency_id.round(line.price_subtotal * percentage * line_percentage)
                epd_needed_vals = epd_needed.setdefault(
                    frozendict({
                        'move_id': line.move_id.id,
                        'account_id': line.account_id.id,
                        'display_type': 'epd',
                    }),
                    {
                        'name': _("Early Payment Discount (%s)", discount_percentage_name),
                        'amount_currency': 0.0,
                        'balance': 0.0,
                        'price_subtotal': 0.0,
                        'tax_ids': [Command.clear()],
                    },
                )
                epd_needed_vals['amount_currency'] += line.currency_id.round(line.amount_currency * percentage * line_percentage)
                epd_needed_vals['balance'] += line.currency_id.round(line.balance * percentage * line_percentage)
                epd_needed_vals['price_subtotal'] += line.currency_id.round(line.price_subtotal * percentage * line_percentage)
            line.epd_needed = {k: frozendict(v) for k, v in epd_needed.items()}

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

    def _prepare_analytic_lines(self):
        analytic_line_vals = super()._prepare_analytic_lines()

        if self.analytic_distribution_area:
            # distribution_on_each_plan corresponds to the proportion that is distributed to each plan to be able to
            # give the real amount when we achieve a 100% distribution
            distribution_on_each_plan = {}

            for account_id, distribution in self.analytic_distribution_area.items():
                line_values = self._prepare_analytic_distribution_line(float(distribution), account_id, distribution_on_each_plan)
                if not self.currency_id.is_zero(line_values.get('amount')):
                    analytic_line_vals.append(line_values)
        if self.analytic_distribution_activity:
            # distribution_on_each_plan corresponds to the proportion that is distributed to each plan to be able to
            # give the real amount when we achieve a 100% distribution
            distribution_on_each_plan = {}

            for account_id, distribution in self.analytic_distribution_activity.items():
                line_values = self._prepare_analytic_distribution_line(float(distribution), account_id, distribution_on_each_plan)
                if not self.currency_id.is_zero(line_values.get('amount')):
                    analytic_line_vals.append(line_values)
        return analytic_line_vals
    
    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """
        self.ensure_one()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1

        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit if is_invoice else self.amount_currency,
            quantity=self.quantity if is_invoice else 1.0,
            discount=self.discount if is_invoice else 0.0,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            analytic_distribution_area=self.analytic_distribution_area,
            analytic_distribution_activity=self.analytic_distribution_activity,
            price_subtotal=sign * self.amount_currency,
            is_refund=self.is_refund,
            rate=(abs(self.amount_currency) / abs(self.balance)) if self.balance else 1.0
        )
    
    def _convert_to_tax_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """
        self.ensure_one()
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1

        return self.env['account.tax']._convert_to_tax_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            taxes=self.tax_ids,
            tax_tags=self.tax_tag_ids,
            tax_repartition_line=self.tax_repartition_line_id,
            group_tax=self.group_tax_id,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            analytic_distribution_area=self.analytic_distribution_area,
            analytic_distribution_activity=self.analytic_distribution_activity,
            tax_amount=sign * self.amount_currency,
        )


    def _sale_determine_order(self):
   
        mapping = super()._sale_determine_order()

        for move_line in self:
            if move_line.analytic_distribution_area:
                distribution_json = move_line.analytic_distribution_area
                sale_order = self.env['sale.order'].search([('analytic_account_id', 'in', list(int(account_id) for account_id in distribution_json.keys())),
                                                            ('state', '=', 'sale')], order='create_date ASC', limit=1)
                if sale_order:
                    mapping[move_line.id] = sale_order
                else:
                    sale_order = self.env['sale.order'].search([('analytic_account_id', 'in', list(int(account_id) for account_id in distribution_json.keys()))], order='create_date ASC', limit=1)
                    mapping[move_line.id] = sale_order            
            if move_line.analytic_distribution_activity:
                distribution_json = move_line.analytic_distribution_activity
                sale_order = self.env['sale.order'].search([('analytic_account_id', 'in', list(int(account_id) for account_id in distribution_json.keys())),
                                                            ('state', '=', 'sale')], order='create_date ASC', limit=1)
                if sale_order:
                    mapping[move_line.id] = sale_order
                else:
                    sale_order = self.env['sale.order'].search([('analytic_account_id', 'in', list(int(account_id) for account_id in distribution_json.keys()))], order='create_date ASC', limit=1)
                    mapping[move_line.id] = sale_order