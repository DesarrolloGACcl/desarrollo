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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class AccountReportGeneralLedger(models.TransientModel):
    _name = "account.report.general.ledger.xlsx"
    _description = "General Ledger Report"

    initial_balance = fields.Boolean(string=_('Include Initial Balances'),
                                    help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.')
    sortby = fields.Selection([('sort_date', _('Date')), ('sort_journal_partner', _('Journal & Partner'))], string=_('Sort by'), required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', 'account_report_general_ledger_journal_rel', 'account_id', 'journal_id', string=_('Journals'), required=True)

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('account.action_report_general_ledger').with_context(landscape=True).report_action(records, data=data)

    display_account = fields.Selection([('all', _('All')), ('movement', _('With movements')),
                                        ('not_zero', _('With balance is not equal to 0')), ],
                                       string=_('Display Accounts'), required=True, default='movement')

    def pre_print_report(self, data):
        data['form'].update(self.read(['display_account'])[0])
        return data

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
            'data': {'model': 'account.report.general.ledger.xlsx',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'general ledger report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, options, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {}
        vals = self.search([('id', '=', options['form']['id'])])
        data['form'] = vals.read([])[0]
        data['model'] = 'ir.ui.menu'
        data['ids'] = []
        data['form']['used_context'] = {
            'date_to': vals.date_to,
            'date_from': vals.date_from,
            'strict_range': True,
            'state': vals.target_move,
            # 'active_model': 'account.account' if vals.active_account else None,
            # 'active_ids': [vals.active_account.id] if vals.active_account else None,
            # 'active_id': vals.active_account.id if vals.active_account else None,
            'journal_ids': vals.journal_ids.ids,
        }

        env_obj = vals.env['report.account.report_generalledger']
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
        # accounts = vals.active_account if vals.active_account else self.env['account.account'].search([])
        accounts = self.env['account.account'].browse(options['ids']) or self.env['account.account'].search([])
        init_balance = vals['initial_balance']
        report_obj = env_obj.with_context(data['form'].get('used_context', {}))._get_account_move_entry(
            accounts, init_balance, sortby, display_account)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'align': 'center'})
        format5 = workbook.add_format({'font_size': 10, 'align': 'right'})
        format1.set_align('center')
        format2.set_align('center')
        format3.set_align('right')
        format4.set_align('left')
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
        logged_users = self.env['res.company']._company_default_get('account.account')
        report_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sheet.merge_range('M8:N8', _("Report Date"), format3)
        sheet.merge_range('M9:N9', report_date, format4)
        sheet.merge_range(1, 0, 1, 14, logged_users.name, format4)
        sheet.merge_range(3, 0, 4, 14, _("General Ledger Report"), format1)
        sheet.merge_range('A6:B6', _("Journals :"), format6)
        row = 6
        col = 0
        i = 0
        for values in codes:
            sheet.write(row, col + i, values, format7)
            i += 1
        if data['form']['display_account'] == 'all':
            display_account = _('All accounts')
        elif data['form']['display_account'] == 'movement':
            display_account = _('With movements')
        else:
            display_account = _('With balance not equal to zero')

        if data['form']['target_move'] == 'all':
            target_moves = _('All entries')
        else:
            target_moves = _('All posted entries')

        if data['form']['sortby'] == 'sort_date':
            sortby = 'Date'
        else:
            sortby = 'Journal and partners'
        if data['form']['date_from']:
            date_start = data['form']['date_from']
        else:
            date_start = ""
        if data['form']['date_to']:
            date_end = data['form']['date_to']
        else:
            date_end = ""
        if sortby == 'Date':
            sheet.write('G8', _("Start Date"), format3)
            sheet.write('G9', date_start, format4)
            sheet.write('J8', _("End Date"), format3)
            sheet.write('J9', date_end, format4)
        sheet.merge_range('C8:D8', _("Sorted By"), format3)
        sheet.merge_range('C9:D9', sortby, format4)
        sheet.merge_range('A8:B8', _("Display Account"), format6)
        sheet.merge_range('A9:B9', display_account, format7)
        sheet.merge_range('E8:F8', _("Target Moves"), format6)
        sheet.merge_range('E9:F9', target_moves, format7)
        sheet.write('A11', "Date ", format2)
        sheet.write('B11', "JRNL", format2)
        sheet.merge_range('C11:D11', _("Partner"), format2)
        sheet.merge_range('E11:F11', _("Ref"), format2)
        sheet.merge_range('G11:H11', _("Move"), format2)
        sheet.merge_range('I11:L11', _("Entry Label"), format2)
        sheet.write('M11', _("Debit"), format2)
        sheet.write('N11', _("Credit"), format2)
        sheet.write('O11', _("Balance"), format2)
        accounts = self.env['account.account'].search([])
        row_number = 11
        col_number = 0
        for datas in accounts:
            for values in report_obj:
                if datas['name'] == values['name'] and datas['company_id'].id == values['company_id']:
                    sheet.write(row_number, col_number, datas['code'], format3)
                    sheet.merge_range(row_number, col_number + 1, row_number, col_number + 11, datas['name'], format6)
                    sheet.write(row_number, col_number + 12,
                                logged_users.currency_id.symbol + ' ' + "{:,}".format(values['debit']), format3)
                    sheet.write(row_number, col_number + 13,
                                logged_users.currency_id.symbol + ' ' + "{:,}".format(values['credit']), format3)
                    sheet.write(row_number, col_number + 14,
                                logged_users.currency_id.symbol + ' ' + "{:,}".format(values['balance']), format3)
                    row_number += 1
                    for lines in values['move_lines']:
                        sheet.write(row_number, col_number, lines['ldate'], format4)
                        sheet.write(row_number, col_number + 1, lines['lcode'], format4)
                        sheet.merge_range(row_number, col_number + 2, row_number, col_number + 3, lines['partner_name'],
                                          format4)
                        sheet.merge_range(row_number, col_number + 4, row_number, col_number + 5, lines['lref'],
                                          format4)
                        sheet.merge_range(row_number, col_number + 6, row_number, col_number + 7, lines['move_name'],
                                          format4)
                        sheet.merge_range(row_number, col_number + 8, row_number, col_number + 11, lines['lname'],
                                          format4)
                        sheet.write(row_number, col_number + 12, "{:,}".format(lines['debit']), format5)
                        sheet.write(row_number, col_number + 13, "{:,}".format(lines['credit']), format5)
                        sheet.write(row_number, col_number + 14, "{:,}".format(lines['balance']), format5)
                        row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()