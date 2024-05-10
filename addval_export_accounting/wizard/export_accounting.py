import base64
from io import BytesIO
from odoo import models, fields, api
import xlsxwriter
import json

class ExportAccounting(models.TransientModel):
    _name = 'export.accounting'
    _description = 'Exportar movimientos contables'

    year_id = fields.Many2one('res.account.year', string='Año', required=True)
    month = fields.Selection([
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
        ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
        ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
    ], string='Mes', required=True)


    def action_export(self):
        # Retrieve account.move.line records
        if self.month == '1' or self.month == '3' or self.month == '5' or self.month == '7' or self.month == '8' or self.month == '10' or self.month == '12': 
            domain = [
                ('date', '>=', f'{self.year_id.name}-{str(self.month).zfill(2)}-01'),
                ('date', '<=', f'{self.year_id.name}-{str(self.month).zfill(2)}-31'),
                ('move_id.state', '=', 'posted')
            ]

        elif self.month == '4' or self.month == '6' or self.month == '9' or self.month == '11':

            domain = [
                ('date', '>=', f'{self.year_id.name}-{str(self.month).zfill(2)}-01'),
                ('date', '<=', f'{self.year_id.name}-{str(self.month).zfill(2)}-30'),
                ('move_id.state', '=', 'posted')
            ]

        elif (self.month == '2' and self.year_id.name == '2024') or (self.month == '2' and self.year_id.name == '2028'):
            domain = [
                ('date', '>=', f'{self.year_id.name}-{str(self.month).zfill(2)}-01'),
                ('date', '<=', f'{self.year_id.name}-{str(self.month).zfill(2)}-29'),
                ('move_id.state', '=', 'posted')
            ]

        elif self.month == '2':

            domain = [
                ('date', '>=', f'{self.year_id.name}-{str(self.month).zfill(2)}-01'),
                ('date', '<=', f'{self.year_id.name}-{str(self.month).zfill(2)}-28'),
                ('move_id.state', '=', 'posted')
            ]
        

        account_move_lines = self.env['account.move.line'].search(domain)

        # Create an Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Add Excel file headers (based on your needs)
        headers = ['Fecha', 'Tipo', 'Documento', 'Empresa','Código Proyecto','Proyecto', 'Código Área', 'Área', 
                   'Código Actividad', 'Actividad', 'Código Tarea', 'Tarea', 
                   'Detalle (Etiqueta)', 'Debe', 'Haber', 'Código Cuenta Contable', 'Nombre Cuenta',
                   'Raíz de cuenta', 'Saldo']
        worksheet.write_row(0, 0, headers)

        row = 1
        for line in account_move_lines:
            # Example data writing, adjust according to your data structure
            worksheet.write(row, 0, str(line.date))

            invoice_or_move = self.env["account.move"].search(
                [("id", "=", line.move_id.id)], limit=1
            )

            if invoice_or_move.move_type == 'in_invoice' and invoice_or_move.l10n_latam_document_type_id.code == '71':
                tipo = 'H'
            elif (invoice_or_move.move_type == 'in_invoice' or invoice_or_move.move_type == 'in_refund') and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'C'
            elif (invoice_or_move.move_type == 'out_invoice' or invoice_or_move.move_type == 'out_refund') and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'V'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'outbound':
                tipo = 'E'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'inbound':
                tipo = 'I'
            else:
                tipo = 'T'
            
            worksheet.write(row, 1, tipo)
            worksheet.write(row, 2, line.move_id.name)
            worksheet.write(row, 3, line.partner_id.name)

            if line.analytic_distribution:
                distributions = line.analytic_distribution
                                 
                formatted_project_analytic_info = ""
                project_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                    if analytic_account:
                        formatted_project_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        project_codes += f"{analytic_account.code};"
            else:
                formatted_project_analytic_info = 'No se especificó'
                project_codes = 'No se especificó'

            worksheet.write(row, 4, project_codes)
            worksheet.write(row, 5, formatted_project_analytic_info)

            if line.analytic_distribution_area:
                distributions = line.analytic_distribution_area
                
                formatted_area_analytic_info = ""
                area_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_area_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        area_codes += f"{analytic_account.code};"
            else:
                formatted_area_analytic_info = 'No se especificó'
                area_codes = 'No se especificó'

            worksheet.write(row, 6, area_codes)
            worksheet.write(row, 7, formatted_area_analytic_info)

            if line.analytic_distribution_activity:
                distributions = line.analytic_distribution_activity
                
                formatted_activity_analytic_info = ""
                activity_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_activity_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        activity_codes += f"{analytic_account.code};"
            else:
                formatted_activity_analytic_info = 'No se especificó'
                activity_codes = 'No se especificó'

            worksheet.write(row, 8, activity_codes)
            worksheet.write(row, 9, formatted_activity_analytic_info)

            if line.analytic_distribution_task:
                distributions = line.analytic_distribution_task
                
                formatted_task_analytic_info = ""
                task_codes = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_task_analytic_info += f"{analytic_account.name}: {percentage}%; "
                        task_codes += f"{analytic_account.code};"
            else:
                formatted_task_analytic_info = 'No se especificó'
                task_codes = 'No se especificó'

            worksheet.write(row, 10, task_codes)
            worksheet.write(row, 11, formatted_task_analytic_info)

            worksheet.write(row, 12, line.name)
            worksheet.write(row, 13, line.debit)
            worksheet.write(row, 14, line.credit)
            worksheet.write(row, 15, line.account_id.code)
            worksheet.write(row, 16, line.account_id.name)
            worksheet.write(row, 17, line.account_root_id.name)

            worksheet.write(row, 18, line.balance)

            row += 1

        workbook.close()
        output.seek(0)
        
        # Convert the Excel file to base64 and return as an Odoo action for download
        file_data = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'AccountMoveLines.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'AccountMoveLines.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }