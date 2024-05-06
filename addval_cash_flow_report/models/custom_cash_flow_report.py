# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import get_lang


class CustomCashFlowReport(models.AbstractModel):
    _name = 'custom.cash.flow.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Reporte flujo de caja'

    
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
        # Compute the cash flow report using the direct method: https://www.investopedia.com/terms/d/direct_method.asp
        lines = []

        layout_data = self._get_layout_data()
        report_data = self._get_report_data(report, options, layout_data)

        for layout_line_id, layout_line_data in layout_data.items():
            lines.append((0, self._get_layout_line(report, options, layout_line_id, layout_line_data, report_data)))

            if layout_line_id in report_data and 'aml_groupby_account' in report_data[layout_line_id]:
                aml_data_values = report_data[layout_line_id]['aml_groupby_account'].values()
                for aml_data in sorted(aml_data_values, key=lambda x: x['account_code']):
                    lines.append((0, self._get_aml_line(report, options, aml_data)))

        return lines

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        report._init_options_journals(options, previous_options=previous_options, additional_journals_domain=[('type', 'in', ('bank', 'cash', 'general'))])

    def _get_report_data(self, report, options, layout_data):
        report_data = {}

        # Compute 'Cash and cash equivalents, beginning of period'
        for aml_data in self._get_amls_fixed():
            self._add_report_data('fixed', aml_data, layout_data, report_data)

        return report_data
    
    
    def _add_report_data(self, layout_line_id, aml_data, layout_data, report_data):
        """
        Add or update the report_data dictionnary with aml_data.

        report_data is a dictionnary where the keys are keys from _cash_flow_report_get_layout_data() (used for mapping)
        and the values can contain 2 dictionnaries:
            * (required) 'balance' where the key is the column_group_key and the value is the balance of the line
            * (optional) 'aml_groupby_account' where the key is an account_id and the values are the aml data
        """
        def _report_update_parent(layout_line_id, aml_column_group_key, aml_balance, layout_data, report_data):
            # Update the balance in report_data of the parent of the layout_line_id recursively (Stops when the line has no parent)
            if 'parent_line_id' in layout_data[layout_line_id]:
                parent_line_id = layout_data[layout_line_id]['parent_line_id']

                report_data.setdefault(parent_line_id, {'balance': {}})
                report_data[parent_line_id]['balance'].setdefault(aml_column_group_key, 0.0)
                report_data[parent_line_id]['balance'][aml_column_group_key] += aml_balance

                _report_update_parent(parent_line_id, aml_column_group_key, aml_balance, layout_data, report_data)

        aml_column_group_key = aml_data['column_group_key']
        aml_account_id = aml_data['account_id']
        aml_account_code = aml_data['account_code']
        aml_account_name = aml_data['account_name']
        aml_balance = aml_data['balance']
        aml_account_tag = aml_data.get('account_tag_id', None)

        if self.env.company.currency_id.is_zero(aml_balance):
            return

        report_data.setdefault(layout_line_id, {
            'balance': {},
            'aml_groupby_account': {},
        })

        report_data[layout_line_id]['aml_groupby_account'].setdefault(aml_account_id, {
            'parent_line_id': layout_line_id,
            'account_id': aml_account_id,
            'account_code': aml_account_code,
            'account_name': aml_account_name,
            'account_tag_id': aml_account_tag,
            'level': layout_data[layout_line_id]['level'] + 1,
            'balance': {},
        })

        report_data[layout_line_id]['balance'].setdefault(aml_column_group_key, 0.0)
        report_data[layout_line_id]['balance'][aml_column_group_key] += aml_balance

        report_data[layout_line_id]['aml_groupby_account'][aml_account_id]['balance'].setdefault(aml_column_group_key, 0.0)
        report_data[layout_line_id]['aml_groupby_account'][aml_account_id]['balance'][aml_column_group_key] += aml_balance

        _report_update_parent(layout_line_id, aml_column_group_key, aml_balance, layout_data, report_data) 
    
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
    
    def _get_layout_line(self, report, options, layout_line_id, layout_line_data, report_data):
        line_id = report._get_generic_line_id(None, None, markup=layout_line_id)
        unfold_all = self._context.get('print_mode') or options.get('unfold_all')
        unfoldable = 'aml_groupby_account' in report_data[layout_line_id] if layout_line_id in report_data else False

        column_values = []

        for column in options['columns']:
            expression_label = column['expression_label']
            column_group_key = column['column_group_key']

            value = report_data[layout_line_id].get(expression_label, 0.0).get(column_group_key, 0.0) if layout_line_id in report_data else 0.0

            column_values.append({
                'name': report.format_value(value, blank_if_zero=column['blank_if_zero'], figure_type=column['figure_type']),
                'no_format': value,
                'class': 'number',
            })

        return {
            'id': line_id,
            'name': layout_line_data['name'],
            'level': layout_line_data['level'],
            'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
            'columns': column_values,
            'unfoldable': unfoldable,
            'unfolded': line_id in options['unfolded_lines'] or unfold_all,
        }

    def _get_aml_line(self, report, options, aml_data):
        parent_line_id = report._get_generic_line_id(None, None, aml_data['parent_line_id'])
        line_id = report._get_generic_line_id('account.account', aml_data['account_id'], parent_line_id=parent_line_id)

        column_values = []

        for column in options['columns']:
            expression_label = column['expression_label']
            column_group_key = column['column_group_key']

            value = aml_data[expression_label].get(column_group_key, 0.0)

            column_values.append({
                'name': report.format_value(value, blank_if_zero=column['blank_if_zero'], figure_type=column['figure_type']),
                'no_format': value,
                'class': 'number',
            })

        return {
            'id': line_id,
            'name': f"{aml_data['account_code']} {aml_data['account_name']}",
            'caret_options': 'account.account',
            'level': aml_data['level'],
            'parent_id': parent_line_id,
            'columns': column_values,
        }
