# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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

from datetime import datetime
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountingReport(models.TransientModel):
    _name = "accounting.report.xlsx"
    _description = "Accounting Report"

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    enable_filter = fields.Boolean(string=_('Enable Comparison'))
    account_report_id = fields.Many2one('account.financial.report', string=_('Account Reports'), required=True,
                                        default=_get_account_report)
    label_filter = fields.Char(string=_('Column Label'),
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    filter_cmp = fields.Selection([('filter_no', _('No Filters')), ('filter_date', _('Date'))], string=_('Filter by'),
                                  required=True, default='filter_no')
    date_from_cmp = fields.Date(string=_('Start Date'))
    date_to_cmp = fields.Date(string=_('End Date'))
    debit_credit = fields.Boolean(string=_('Display Debit/Credit Columns'),
                                  help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison.")

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = True
        return result

    def check_report(self):
        res = super(AccountingReport, self).check_report()
        data = {}
        data['form'] = \
        self.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context
        return res

    def _print_report(self, data):
        data['form'].update(self.read(
            ['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter',
             'label_filter', 'target_move'])[0])
        return self.env.ref('account.action_report_financial').report_action(self, data=data, config=False)

    company_id = fields.Many2one('res.company', string=_('Company'), readonly=True,
                                 default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string=_('Journals'), required=True,
                                   default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string=_('Start Date'))
    date_to = fields.Date(string=_('End Date'))
    target_move = fields.Selection([('posted', _('All Posted Entries')),
                                    ('all', _('All Entries')),
                                    ], string=_('Target Moves'), required=True, default='posted')

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    # def _print_report(self, data):
    #     raise NotImplementedError()

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'accounting.report.xlsx',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': self.account_report_id.name,
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, options, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {}
        obj = self.search([('id', '=', options['form']['id'])])
        data['form'] = obj.read([])[0]
        comp_dic = {}
        env_obj = obj.env['report.account.report_financial']
        data['form']['used_context'] = {}
        data['form']['used_context']['date_to'] = data['form']['date_to']
        data['form']['used_context']['date_from'] = data['form']['date_from']
        data['form']['used_context']['journal_ids'] = data['form']['journal_ids']
        data['form']['used_context']['state'] = 'posted'
        data['form']['used_context']['strict_range'] = True
        comp_dic['state'] = 'posted'
        comp_dic['journal_ids'] = data['form']['journal_ids']
        data['form']['comparison_context'] = comp_dic
        data['account_report_id'] = data['form']['account_report_id']
        accounting_data = env_obj.get_account_lines(data.get('form'))
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format1.set_font_name('Times New Roman')
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10})
        format8 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format1.set_align('center')
        format2.set_align('center')
        format3.set_align('center')
        format4.set_align('center')
        format8.set_align('left')
        sheet.set_column('E:E', 10, format4)
        sheet.set_column('H:H', 10, format4)
        sheet.set_column('I:I', 10, format4)
        sheet.set_column('J:J', 10, format4)
        currency = self.env.user.company_id.currency_id.symbol
        format7.set_num_format('0.00 ' + currency)
        format6.set_num_format('0.00 ' + currency)
        report_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('A1:B1', _("Report Date"), format6)
        sheet.merge_range('C1:D1', report_date, format7)
        if obj.account_report_id.name:
            sheet.merge_range(3, 0, 4, 9, obj.account_report_id.name, format1)
        if obj.target_move == 'all':
            target_moves = 'All entries'
        else:
            target_moves = 'All posted entries'
        sheet.merge_range('A7:B7', _("Target Moves:"), format6)
        sheet.write('C7', target_moves, format7)
        if obj.date_from:
            sheet.write('E7', _("Date From:"), format6)
            sheet.write('F7', str(obj.date_from), format7)
        if obj.date_to:
            sheet.write('H7', _("Date to:"), format6)
            sheet.write('I7', str(obj.date_to), format7)
        row_number = 9
        col_number = 0
        if obj.debit_credit == 1:
            sheet.merge_range('A9:G9', _("Name"), format8)
            sheet.write('H9', _("Debit"), format2)
            sheet.write('I9', _("Credit"), format2)
            sheet.write('J9', _("Balance"), format2)
            for values in accounting_data:
                if not self.env.user.company_id.parent_id:
                    if values['level'] != 0:
                        pass
                else:
                    if values['level'] != 0:
                        if values['level'] == 1:
                            sheet.write(row_number, col_number, values['name'], format6)
                            sheet.write(row_number, col_number + 7, values['debit'], format6)
                            sheet.write(row_number, col_number + 8, values['credit'], format6)
                            sheet.write(row_number, col_number + 9, values['balance'], format6)
                            row_number += 1
                        elif not values['account_type'] == 'sum':
                            sheet.write(row_number, col_number, values['name'], format7)
                            sheet.write(row_number, col_number + 7, values['debit'], format7)
                            sheet.write(row_number, col_number + 8, values['credit'], format7)
                            sheet.write(row_number, col_number + 9, values['balance'], format7)
                            row_number += 1

        if not obj.enable_filter and not obj.debit_credit:
            sheet.merge_range('A9:I9', _("Name"), format8)
            sheet.write('J9', _("Balance"), format2)
            for values in accounting_data:
                if values['level'] != 0:
                    if values['level'] == 1:
                        # assets and liabilities
                        sheet.write(row_number, col_number, values['name'], format6)
                        sheet.write(row_number, col_number + 9, values['balance'], format6)
                        row_number += 1
                    elif not values['account_type'] == 'sum':
                        sheet.write(row_number, col_number + 1, values['name'], format7)
                        # sheet.write(row_number, col_number, values['name'], format7)
                        sheet.write(row_number, col_number + 9, values['balance'], format7)
                        row_number += 1
        if obj.enable_filter and not obj.debit_credit:
            sheet.merge_range('A9:H9', _("Name"), format8)
            sheet.write('I9', _("Balance"), format2)
            sheet.write('J9', data['form']['label_filter'], format2)
            for values in accounting_data:
                if values['level'] != 0:
                    if values['level'] == 1:
                        sheet.write(row_number, col_number, values['name'], format6)
                        sheet.write(row_number, col_number + 8, values['balance'], format6)
                        sheet.write(row_number, col_number + 9, values['balance_cmp'], format6)
                        row_number += 1
                    elif not values['account_type'] == 'sum':
                        sheet.write(row_number, col_number, values['name'], format7)
                        sheet.write(row_number, col_number + 8, values['balance'], format7)
                        sheet.write(row_number, col_number + 9, values['balance_cmp'], format7)
                        row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()