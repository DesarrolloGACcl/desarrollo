# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
import re
import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportFinancial(models.AbstractModel):
    _name = 'report.account.report_financial'

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit
        and credit for the provided accounts
        """
        mapping = {
            'balance':
                "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0)"
                " as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0)
                                   for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = (
                self.env['account.move.line']._query_get())
            tables = tables.replace(
                '"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = ("SELECT account_id as id, " +
                       ', '.join(mapping.values()) +
                       " FROM " + tables +
                       " WHERE account_id IN %s " +
                       filters +
                       " GROUP BY account_id")
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        """returns a dictionary with key=the ID of a record and
         value=the credit, debit and balance amount
        computed for this record. If the record is of type :
        'accounts' : it's the sum of the linked accounts
        'account_type' : it's the sum of leaf accounts with
         such an account_type
        'account_report' : it's the amount of the related report
        'sum' : it's the sum of the children of this record
         (aka a 'view' record)"""
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(
                    report.account_ids
                )
                for value in \
                        res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts
                #  with such an account type
                accounts = self.env['account.account'].search([
                    ('account_type', '=', report.account_type_ids)
                ])
                if report.name == "Expenses":
                    accounts = self.env['account.account'].search([
                        ('account_type', 'in', ["expense","expense_depreciation","expense_direct_cost"])
                    ])
                if report.name == "Liability":
                    accounts = self.env['account.account'].search([
                        ('account_type', 'in', ["liability_payable","equity","liability_current","liability_non_current"])
                    ])
                if report.name == "Assets":
                    accounts = self.env['account.account'].search([
                        ('account_type', 'in', ["asset_receivable","asset_cash","asset_current","asset_non_current","asset_prepayments","asset_fixed"])
                    ])

                res[report.id]['account'] = self._compute_account_balance(
                    accounts)

                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([
            ('id', '=', data['account_report_id'][0])
        ])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(
            data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in \
                            comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            r_name = str(report.name)
            # r_name = r_name.replace(" ", "-") + "-"
            r_name = re.sub('[^0-9a-zA-Z]+', '', r_name)
            if report.parent_id:
                p_name = str(report.parent_id.name)
                p_name = re.sub('[^0-9a-zA-Z]+', '', p_name) + str(
                    report.parent_id.id)
                # p_name = p_name.replace(" ", "-") +
                #  "-" + str(report.parent_id.id)
            else:
                p_name = False
            vals = {
                'r_id': report.id,
                'id': r_name + str(report.id),
                'sequence': report.sequence,
                'parent': p_name,
                'name': report.name,
                'balance': res[report.id]['balance'] * int(report.sign),
                'type': 'report',
                'level': bool(
                    report.style_overwrite) and report.style_overwrite or
                         report.level,
                'account_type': report.type or False,
                # used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * int(
                    report.sign)

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is
                # used to display the details of the
                #  financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value \
                        in res[report.id]['account'].items():
                    # if there are accounts to display,
                    #  we add them to the lines with a level equals
                    #  to their level in
                    # the COA + 1 (to avoid having them with a too low level
                    #  that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    # new_r_name = str(report.name)
                    # new_r_name = new_r_name.replace(" ", "-") + "-"
                    vals = {
                        'account': account.id,
                        'a_id': account.code + re.sub('[^0-9a-zA-Z]+', 'acnt',
                                                      account.name) + str(
                            account.id),
                        'name': account.code + '-' + account.name,
                        'balance': value['balance'] * int(report.sign) or 0.0,
                        'type': 'account',
                        'parent': r_name + str(report.id),
                        'level': (
                                report.display_detail == 'detail_with_hierarchy' and
                                4),
                        'account_type': account.account_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or \
                                not account.company_id.currency_id.is_zero(
                                    vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(
                            vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * int(
                            report.sign)
                        if not account.company_id.currency_id.is_zero(
                                vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
        return lines

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(data.get('form'))
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_account_lines': report_lines,
        }
