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
        headers = ['Fecha', 'Tipo', 'Documento', 'Código Proyecto','Proyecto', 'Código Área', 'Área', 
                   'Código Actividad', 'Actividad', 'Código Tarea', 'Tarea', 
                   'Detalle (Etiqueta)', 'Debe', 'Haber', 'Código Cuenta Contable', 'Nombre Cuenta',
                   'Raíz de cuenta', 'Importe en moneda', 'Importe residual',
                   'Importe residual en moneda', 'Líneas analíticas', 'Activos relacionados',
                   'Saldo', 'Moneda de la Compañía', 'Moneda' , 'Fecha de vencimiento',
                   'Descuento (%)', 'Importe de Descuento en Divisa', 'Descuento de Balance',
                   'Fecha descuento', 'Porcentaje de descuento', 'Tipo de visualización',
                   'Fecha prevista','Nivel del seguimiento', 'Conciliación', 'Grupo de impuestos originador',
                   'Es un anticipo', 'Diario', 'Tipo de Documento', 'Conciliación #','Número',
                   'Estado', 'Empresa','Emisor del pago', 'Subtotal', 'Total', 'Precio un.', 'Precio un. orig.',
                   'Producto', 'Unidad de medida','Línea pedido de compra', 'Cantidad', 'Modelo de conciliación',
                   'Conciliado', 'Referencia','Secuencia','Extracto', 'Línea de estado de cuenta del originador',
                   'Cadena de auditoría fiscal', 'Importe base', 'Grupo de impuestos del originador',
                   'Impuestos', 'Impuesto (cuota)', 'Línea de distribución de impuestos del originador',
                   'Etiquetas', 'Invertir etiquetas', 'Última actualización en', 'Última actualización de']
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

            worksheet.write(row, 3, project_codes)
            worksheet.write(row, 4, formatted_project_analytic_info)

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

            worksheet.write(row, 5, area_codes)
            worksheet.write(row, 6, formatted_area_analytic_info)

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

            worksheet.write(row, 7, activity_codes)
            worksheet.write(row, 8, formatted_activity_analytic_info)

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

            worksheet.write(row, 9, task_codes)
            worksheet.write(row, 10, formatted_task_analytic_info)

            worksheet.write(row, 11, line.name)
            worksheet.write(row, 12, line.debit)
            worksheet.write(row, 13, line.credit)
            worksheet.write(row, 14, line.account_id.code)
            worksheet.write(row, 15, line.account_id.name)
            worksheet.write(row, 16, line.account_root_id.name)
            worksheet.write(row, 17, line.amount_currency)
            worksheet.write(row, 18, line.amount_residual)
            worksheet.write(row, 19, line.amount_residual_currency)
            worksheet.write(row, 20, str(line.analytic_line_ids))
            worksheet.write(row, 21, str(line.asset_ids))
            worksheet.write(row, 22, line.balance)
            worksheet.write(row, 23, line.company_currency_id.name)
            worksheet.write(row, 24, line.currency_id.name)
            worksheet.write(row, 25, line.date_maturity)
            worksheet.write(row, 26, line.discount)
            worksheet.write(row, 27, line.discount_amount_currency)
            worksheet.write(row, 28, line.discount_balance)
            worksheet.write(row, 29, line.discount_date)
            worksheet.write(row, 30, line.discount_percentage)
            worksheet.write(row, 31, line.display_type)
            worksheet.write(row, 32, line.expected_pay_date)
            worksheet.write(row, 33, line.followup_line_id.name)
            worksheet.write(row, 34, line.full_reconcile_id.name)
            worksheet.write(row, 35, line.group_tax_id.name)
            worksheet.write(row, 36, line.is_downpayment)
            worksheet.write(row, 37, line.journal_id.name)
            worksheet.write(row, 38, line.l10n_latam_document_type_id.name)
            worksheet.write(row, 39, line.matching_number)
            worksheet.write(row, 40, line.move_name)
            worksheet.write(row, 41, line.parent_state)
            worksheet.write(row, 42, line.partner_id.name)
            worksheet.write(row, 43, line.payment_id.name)
            worksheet.write(row, 44, line.price_subtotal)
            worksheet.write(row, 45, line.price_total)
            worksheet.write(row, 46, line.price_unit)
            worksheet.write(row, 47, line.price_unit_original)
            worksheet.write(row, 48, line.product_id.name)
            worksheet.write(row, 49, line.product_uom_id.name)
            worksheet.write(row, 50, line.purchase_line_id.name)
            worksheet.write(row, 51, line.quantity)
            worksheet.write(row, 52, line.reconcile_model_id.name)
            worksheet.write(row, 53, line.reconciled)
            worksheet.write(row, 54, line.ref)
            worksheet.write(row, 55, line.sequence)
            worksheet.write(row, 56, line.statement_id.name)
            worksheet.write(row, 57, line.statement_line_id.name)
            worksheet.write(row, 58, line.tax_audit)
            worksheet.write(row, 59, line.tax_base_amount)
            worksheet.write(row, 60, line.tax_group_id.name)
            worksheet.write(row, 61, str(line.tax_ids))
            worksheet.write(row, 62, line.tax_line_id.name)
            worksheet.write(row, 63, str(line.tax_repartition_line_id))
            worksheet.write(row, 64, str(line.tax_tag_ids))
            worksheet.write(row, 65, line.tax_tag_invert)
            worksheet.write(row, 66, line.write_date)
            worksheet.write(row, 67, str(line.write_uid))

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