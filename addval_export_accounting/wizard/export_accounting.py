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
        domain = [
            ('date', '>=', f'{self.year_id.name}-{str(self.month).zfill(2)}-01'),
            ('date', '<=', f'{self.year_id.name}-{str(self.month).zfill(2)}-31'),
        ]
        account_move_lines = self.env['account.move.line'].search(domain)

        # Create an Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Add Excel file headers (based on your needs)
        headers = ['Fecha', 'Tipo', 'Documento', 'Proyecto', 'Área', 'Actividad', 'Tarea', 
                   'Detalle', 'Debe', 'Haber', 'Código Gasto', 'Nombre Cuenta']
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
            elif invoice_or_move.move_type == 'in_invoice' and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'C'
            elif invoice_or_move.move_type == 'out_invoice' and invoice_or_move.l10n_latam_document_type_id:
                tipo = 'V'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'outbound':
                tipo = 'E'
            elif invoice_or_move.l10n_latam_document_type_id is not None and invoice_or_move.payment_id.payment_type == 'inbound':
                tipo = 'I'
            else:
                tipo = 'T'
            
            worksheet.write(row, 1, tipo)
            worksheet.write(row, 2, line.move_id.name)

            if line.analytic_distribution:
                distributions = json.loads(line.analytic_distribution)
                                 
                formatted_project_analytic_info = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))
                    if analytic_account:
                        formatted_project_analytic_info += f"{analytic_account.name}: {percentage}%; "
            else:
                formatted_project_analytic_info = 'No se especificó'

            worksheet.write(row, 3, formatted_project_analytic_info)

            if line.analytic_distribution_area:
                distributions = json.loads(line.analytic_distribution_area)
                
                formatted_area_analytic_info = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_area_analytic_info += f"{analytic_account.name}: {percentage}%; "
            else:
                formatted_area_analytic_info = 'No se especificó'

            worksheet.write(row, 4, formatted_area_analytic_info)

            if line.analytic_distribution_activity:
                distributions = json.loads(line.analytic_distribution_activity)
                
                formatted_activity_analytic_info = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_activity_analytic_info += f"{analytic_account.name}: {percentage}%; "
            else:
                formatted_activity_analytic_info = 'No se especificó'

            worksheet.write(row, 5, formatted_activity_analytic_info)

            if line.analytic_distribution_task:
                distributions = json.loads(line.analytic_distribution_task)
                
                formatted_task_analytic_info = ""
                for account_id, percentage in distributions.items():
                    # Fetch the analytic account name using the ID
                    analytic_account = self.env['account.analytic.account'].browse(int(account_id))                    
                    if analytic_account:
                        formatted_task_analytic_info += f"{analytic_account.name}: {percentage}%; "
            else:
                formatted_task_analytic_info = 'No se especificó'

            worksheet.write(row, 6, formatted_task_analytic_info)

            worksheet.write(row, 7, line.name)
            worksheet.write(row, 8, line.debit)
            worksheet.write(row, 9, line.credit)
            worksheet.write(row, 10, line.account_id.code)
            worksheet.write(row, 11, line.account_id.name)
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