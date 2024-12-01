# Part of Odoo. See LICENSE file for full copyright and licensing details.

import markupsafe
from lxml import etree

from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.models import check_method_name
from odoo.addons.web.controllers.utils import clean_action
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang


class BankRecWidget(models.Model):
    _inherit = "bank.rec.widget"

    def button_validate(self, async_action=False):
        self.ensure_one()

        if self.state != 'valid':
            self.next_action_todo = {'type': 'move_to_next'}
            return

        partners = (self.line_ids.filtered(lambda x: x.flag != 'liquidity')).partner_id
        partner_id_to_set = partners.id if len(partners) == 1 else None

        # Prepare the lines to be created.
        to_reconcile = []
        line_ids_create_command_list = []
        aml_to_exchange_diff_vals = {}
        for i, line in enumerate(self.line_ids):
            if line.flag == 'exchange_diff':
                continue

            amount_currency = line.amount_currency
            balance = line.balance
            if line.flag == 'new_aml':
                to_reconcile.append((i, line.source_aml_id.id))
                exchange_diff = self.line_ids \
                    .filtered(lambda x: x.flag == 'exchange_diff' and x.source_aml_id == line.source_aml_id)
                if exchange_diff:
                    aml_to_exchange_diff_vals[i] = {
                        'amount_residual': exchange_diff.balance,
                        'amount_residual_currency': exchange_diff.amount_currency,
                        'analytic_distribution': exchange_diff.analytic_distribution,
                    }
                    # Squash amounts of exchange diff into corresponding new_aml
                    amount_currency += exchange_diff.amount_currency
                    balance += exchange_diff.balance
            line_ids_create_command_list.append(Command.create(
                self._get_line_create_command_dict(
                    line, i, amount_currency, balance, partner_id_to_set
                )
            ))

        self.js_action_reconcile_st_line(
            self.st_line_id.id,
            {
                'command_list': line_ids_create_command_list,
                'to_reconcile': to_reconcile,
                'exchange_diff': aml_to_exchange_diff_vals,
                'partner_id': partner_id_to_set,
            },
        )
        self.next_action_todo = {'type': 'reconcile_st_line'}

        self.move_id.line_ids[0].principal_account_id = partner_id_to_set.principal_account_id.id
        self.move_id.line_ids[0].secondary_account_id = partner_id_to_set.secondary_account_id.id
        self.move_id.line_ids[0].third_account_id = partner_id_to_set.third_account_id.id