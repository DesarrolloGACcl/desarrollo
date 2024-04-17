# report_partner_ledger.py file
from odoo import api, models, fields
from io import BytesIO
import xlwt
import base64
from datetime import date, timedelta

class PartnerAgedBalance(models.Model):
    _name = "partner.aged.balance.statement"
    partner_id = fields.Many2one('res.partner')
    period_30 = fields.Float()
    period_3060 = fields.Float()
    period_6090 = fields.Float()
    period_90120 = fields.Float()
    period_120 = fields.Float()
    balance = fields.Float(compute='_calc_total', store=True)
    company_id = fields.Many2one('res.partner')
    def _calc_total(self):
        for rec in self:
            rec.balance = rec.period_30 + rec.period_3060 + rec.period_6090 + rec.period_90120 + rec.period_30120
class VendorStatement(models.Model):
    _name = "account.move.line.statement"
    date = fields.Date()
    line_id = fields.Many2one('account.move.line')
    name = fields.Char(compute="_compute_data", store=True)
    ref = fields.Char(compute="_compute_data", store=True)
    partner_id = fields.Many2one('res.partner')
    debit = fields.Float()
    credit = fields.Float()
    balance = fields.Float()
    move_line_date = fields.Date()
    account_id = fields.Many2one('account.account')
    move_id = fields.Many2one('account.move')
    statement_date_due = fields.Date()
    analytic_account_id = fields.Many2one('account.analytic.account')
    company_id = fields.Many2one('res.partner')

    @api.depends('move_id')
    def _compute_data(self):
        for rec in self:
            rec.name = rec.move_id.name
            rec.ref = rec.move_id.ref

class PartnerLeger(models.Model):
    _inherit = 'res.partner'
    aged_balance_ids = fields.One2many('partner.aged.balance.statement', 'partner_id')
    statement_ids = fields.One2many('account.move.line.statement', 'partner_id')
    statement_state = fields.Selection(selection=[('all', 'All'),
                                                  ('draft', 'Draft'),
                                                  ('posted', 'Posted'),
                                                  ('cancel', 'Cancel')], default='all')
    xlsx_file_statement = fields.Binary(string="Statements XLSX File ")
    xlsx_filename_statements = fields.Char('Statements XLSX File Name')

    def print_partner_statements(self):
        return self.env.ref('customer_vendor_statements.partner_ledger_report').report_action(self)


    def download_xlsx_statements(self):
        # Create a workbook and add a worksheet
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Statements')

        # Define the header row
        row_num = 0
        columns = ['Date', 'Move ID', 'Account ID', 'Ref', 'Debit', 'Credit', 'Balance']
        for col_num, column_title in enumerate(columns):
            worksheet.write(row_num, col_num, column_title)

        # Write the data from the tree view to the worksheet
        for statement in self.statement_ids:
            row_num += 1
            row = [statement.date, statement.move_id.name, statement.account_id.name, statement.ref, statement.debit,
                   statement.credit, statement.balance]
            for col_num, cell_value in enumerate(row):
                worksheet.write(row_num, col_num, cell_value)

        # Save the workbook to a BytesIO object
        fp = BytesIO()
        workbook.save(fp)

        # Encode the data as base64
        xlsx_data = base64.b64encode(fp.getvalue()).decode()

        # Create the download action
        action = {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=%s&field=%s&id=%s&filename_field=%s&download=true' % (
            self._name, 'xlsx_file_statement', self.id, 'xlsx_filename_statements'),
            'target': 'new',
        }

        # Save the data as a binary field on the record
        self.write({'xlsx_file_statement': xlsx_data, 'xlsx_filename_statements': 'Statements.xlsx'})

        return action


    def get_statement(self):
        self.env['account.move.line.statement'].search([('partner_id', '=', self.id)]).unlink()
        self.env['partner.aged.balance.statement'].search([('partner_id', '=', self.id)]).unlink()
        states = []
        if self.statement_state == 'all':
            states = ['draft', 'posted','cancel']
        elif self.statement_state == 'posted':
            states = ['posted']
        elif self.statement_state == 'draft':
            states = ['draft']
        elif self.statement_state == 'cancel':
            states = ['cancel']
        move_line_ids = self.env['account.move.line'].search([
            ('partner_id', '=', self.id),
            ('account_id.user_type_id.type', 'in', ['receivable', 'payable']),
            ('company_id', '=', self.env.company.id),
            ('move_id.state', 'in', states)])
        today = date.today()
        period_30 = 0
        period_3060 = 0
        period_6090 = 0
        period_90120 = 0
        period_120 = 0
        for line in move_line_ids:
            self.env['account.move.line.statement'].create({
                'line_id': line.id,
                'date': line.move_id.date,
                'move_id': line.move_id.id,
                'account_id': line.account_id.id,
                'name': line.move_id.name,
                'ref': line.move_id.ref,
                'partner_id': line.partner_id.id,
                'statement_date_due': line.move_id.invoice_date_due,
                'credit': line.credit,
                'debit': line.debit,
                'balance': line.balance,
                'analytic_account_id': line.analytic_account_id.id,
                'company_id': line.company_id.id,

            })
            delta = today - line.date
            number_of_days = delta.days
            if number_of_days <= 30:
                period_30 += line.debit - line.credit
            elif number_of_days > 30 and number_of_days <= 60:
                period_3060 += line.debit - line.credit
            elif number_of_days > 60 and number_of_days <= 90:
                period_6090 += line.debit - line.credit
            elif number_of_days > 60 and number_of_days <= 120:
                period_90120 += line.debit - line.credit
            else:
                period_120 += line.debit - line.credit
        all_periods = period_30 + period_3060 + period_6090 + period_90120 + period_120

        self.env['partner.aged.balance.statement'].create({
            'partner_id': self.id,
            'period_30': period_30,
            'period_3060': period_3060,
            'period_6090': period_6090,
            'period_90120': period_90120,
            'period_120': period_120,
            'balance': all_periods,
            'company_id': self.env.company.id,
        })
    def email_partner_statement(self):
        self.ensure_one()
        template = self.env.ref('customer_vendor_statements.partner_ledger_statement_report')
        report = self.env['ir.actions.report']._get_report_from_name(
            'customer_vendor_statements.partner_ledger_statement_report')
        pdf = report.with_context(pricelist=self.id).render_qweb_pdf(self.id)[0]
        self.env['mail.thread'].message_post(
            body="Attached is the partner statement report",
            subject="Partner Statement Report",
            attachments=[('PartnerStatement.pdf', pdf)],
            message_type='email',
            subtype='mail.mt_comment',
            email_from=self.env.user.email,
            recipient_ids=[(6, 0, [self.id])],
        )




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    balance = fields.Float(compute='_compute_balance', store=True)

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.debit - rec.credit
