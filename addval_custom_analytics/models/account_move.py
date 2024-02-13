from collections import defaultdict
from odoo import api, fields, models, _, Command
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    is_html_empty,
    sql
)

class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]
                sign = move.direction_sign
                if move.id:
                    # The invoice is stored so we can add the early payment discount lines directly to reduce the
                    # tax amount without touching the untaxed amount.
                    base_line_values_list += [
                        {
                            **line._convert_to_tax_base_line_dict(),
                            'handle_price_include': False,
                            'quantity': 1.0,
                            'price_unit': sign * line.amount_currency,
                        }
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'epd')
                    ]

                kwargs = {
                    'base_lines': base_line_values_list,
                    'currency': move.currency_id or move.journal_id.currency_id or move.company_id.currency_id,
                }

                if move.id:
                    kwargs['tax_lines'] = [
                        line._convert_to_tax_line_dict()
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'tax')
                    ]
                else:
                    # In case the invoice isn't yet stored, the early payment discount lines are not there. Then,
                    # we need to simulate them.
                    epd_aggregated_values = {}
                    for base_line in base_lines:
                        if not base_line.epd_needed:
                            continue
                        for grouping_dict, values in base_line.epd_needed.items():
                            epd_values = epd_aggregated_values.setdefault(grouping_dict, {'price_subtotal': 0.0})
                            epd_values['price_subtotal'] += values['price_subtotal']

                    for grouping_dict, values in epd_aggregated_values.items():
                        taxes = None
                        if grouping_dict.get('tax_ids'):
                            taxes = self.env['account.tax'].browse(grouping_dict['tax_ids'][0][2])

                        kwargs['base_lines'].append(self.env['account.tax']._convert_to_tax_base_line_dict(
                            None,
                            partner=move.partner_id,
                            currency=move.currency_id,
                            taxes=taxes,
                            price_unit=values['price_subtotal'],
                            quantity=1.0,
                            account=self.env['account.account'].browse(grouping_dict['account_id']),
                            analytic_distribution=values.get('analytic_distribution'),
                            analytic_distribution_area=values.get('analytic_distribution_area'),
                            analytic_distribution_activity=values.get('analytic_distribution_activity'),
                            analytic_distribution_task=values.get('analytic_distribution_task'),
                            price_subtotal=values['price_subtotal'],
                            is_refund=move.move_type in ('out_refund', 'in_refund'),
                            handle_price_include=False,
                        ))
                move.tax_totals = self.env['account.tax']._prepare_tax_totals(**kwargs)
                if move.invoice_cash_rounding_id:
                    rounding_amount = move.invoice_cash_rounding_id.compute_difference(move.currency_id, move.tax_totals['amount_total'])
                    totals = move.tax_totals
                    totals['display_rounding'] = True
                    if rounding_amount:
                        if move.invoice_cash_rounding_id.strategy == 'add_invoice_line':
                            totals['rounding_amount'] = rounding_amount
                            totals['formatted_rounding_amount'] = formatLang(self.env, totals['rounding_amount'], currency_obj=move.currency_id)
                            totals['amount_total_rounded'] = totals['amount_total'] + rounding_amount
                            totals['formatted_amount_total_rounded'] = formatLang(self.env, totals['amount_total_rounded'], currency_obj=move.currency_id)
                        elif move.invoice_cash_rounding_id.strategy == 'biggest_tax':
                            if totals['subtotals_order']:
                                max_tax_group = max((
                                    tax_group
                                    for tax_groups in totals['groups_by_subtotal'].values()
                                    for tax_group in tax_groups
                                ), key=lambda tax_group: tax_group['tax_group_amount'])
                                max_tax_group['tax_group_amount'] += rounding_amount
                                max_tax_group['formatted_tax_group_amount'] = formatLang(self.env, max_tax_group['tax_group_amount'], currency_obj=move.currency_id)
                                totals['amount_total'] += rounding_amount
                                totals['formatted_amount_total'] = formatLang(self.env, totals['amount_total'], currency_obj=move.currency_id)
            else:
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.tax_totals = None

    def _get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line(self):
        """ Helper to get the values to create the counterpart journal items on the register payment wizard and the
        bank reconciliation widget in case of an early payment discount. When the early payment discount computation
        is included, we need to compute the base amounts / tax amounts for each receivable / payable but we need to
        take care about the rounding issues. For others computations, we need to balance the discount you get.

        :return: A list of values to create the counterpart journal items split in 3 categories:
            * term_lines:   The journal items containing the discount amounts for each receivable line when the
                            discount computation is excluded / mixed.
            * tax_lines:    The journal items acting as tax lines when the discount computation is included.
            * base_lines:   The journal items acting as base for tax lines when the discount computation is included.
        """
        self.ensure_one()

        def grouping_key_generator(base_line, tax_values):
            return self.env['account.tax']._get_generation_dict_from_base_line(base_line, tax_values)

        def inverse_tax_rep(tax_rep):
            tax = tax_rep.tax_id
            index = list(tax.invoice_repartition_line_ids).index(tax_rep)
            return tax.refund_repartition_line_ids[index]

        # Get the current tax amounts in the current invoice.
        tax_amounts = {
            inverse_tax_rep(line.tax_repartition_line_id).id: {
                'amount_currency': line.amount_currency,
                'balance': line.balance,
            }
            for line in self.line_ids.filtered(lambda x: x.display_type == 'tax')
        }

        product_lines = self.line_ids.filtered(lambda x: x.display_type == 'product')
        base_lines = [
            {
                **x._convert_to_tax_base_line_dict(),
                'is_refund': True,
            }
            for x in product_lines
        ]
        for base_line in base_lines:
            base_line['taxes'] = base_line['taxes'].filtered(lambda t: t.amount_type != 'fixed')

        if self.is_inbound(include_receipts=True):
            cash_discount_account = self.company_id.account_journal_early_pay_discount_loss_account_id
        else:
            cash_discount_account = self.company_id.account_journal_early_pay_discount_gain_account_id

        res = {
            'term_lines': defaultdict(lambda: {}),
            'tax_lines': defaultdict(lambda: {}),
            'base_lines': defaultdict(lambda: {}),
        }

        early_pay_discount_computation = self.company_id.early_pay_discount_computation

        base_per_percentage = {}
        tax_computation_per_percentage = {}
        for aml in self.line_ids.filtered(lambda x: x.display_type == 'payment_term'):
            if not aml.discount_percentage:
                continue

            term_amount_currency = aml.amount_currency - aml.discount_amount_currency
            term_balance = aml.balance - aml.discount_balance

            if early_pay_discount_computation == 'included' and product_lines.tax_ids:

                # Compute the amounts for each percentage.
                if aml.discount_percentage not in tax_computation_per_percentage:

                    # Compute the base amounts.
                    base_per_percentage[aml.discount_percentage] = resulting_delta_base_details = {}
                    to_process = []
                    for base_line in base_lines:
                        invoice_line = base_line['record']
                        to_update_vals, tax_values_list = self.env['account.tax']._compute_taxes_for_single_line(
                            base_line,
                            early_pay_discount_computation=early_pay_discount_computation,
                            early_pay_discount_percentage=aml.discount_percentage,
                        )
                        to_process.append((base_line, to_update_vals, tax_values_list))

                        grouping_dict = {
                            'tax_ids': [Command.set(base_line['taxes'].ids)],
                            'tax_tag_ids': to_update_vals['tax_tag_ids'],
                            'partner_id': base_line['partner'].id,
                            'currency_id': base_line['currency'].id,
                            'account_id': cash_discount_account.id,
                            'analytic_distribution': base_line['analytic_distribution'],
                            'analytic_distribution_area': base_line['analytic_distribution_area'],
                            'analytic_distribution_activity': base_line['analytic_distribution_activity'],
                            'analytic_distribution_task': base_line['analytic_distribution_task'],
                        }
                        base_detail = resulting_delta_base_details.setdefault(frozendict(grouping_dict), {
                            'balance': 0.0,
                            'amount_currency': 0.0,
                        })

                        amount_currency = self.currency_id\
                            .round(self.direction_sign * to_update_vals['price_subtotal'] - invoice_line.amount_currency)
                        balance = self.company_currency_id\
                            .round(amount_currency / base_line['rate'])

                        base_detail['balance'] += balance
                        base_detail['amount_currency'] += amount_currency

                    # Compute the tax amounts.
                    tax_details_with_epd = self.env['account.tax']._aggregate_taxes(
                        to_process,
                        grouping_key_generator=grouping_key_generator,
                    )

                    tax_computation_per_percentage[aml.discount_percentage] = resulting_delta_tax_details = {}
                    for tax_detail in tax_details_with_epd['tax_details'].values():
                        tax_amount_without_epd = tax_amounts.get(tax_detail['tax_repartition_line_id'])
                        if not tax_amount_without_epd:
                            continue

                        tax_amount_currency = self.currency_id\
                            .round(self.direction_sign * tax_detail['tax_amount_currency'] - tax_amount_without_epd['amount_currency'])
                        tax_amount = self.company_currency_id\
                            .round(self.direction_sign * tax_detail['tax_amount'] - tax_amount_without_epd['balance'])

                        if self.currency_id.is_zero(tax_amount_currency) and self.company_currency_id.is_zero(tax_amount):
                            continue

                        resulting_delta_tax_details[tax_detail['tax_repartition_line_id']] = {
                            **tax_detail,
                            'amount_currency': tax_amount_currency,
                            'balance': tax_amount,
                        }

                # Multiply each amount by the percentage paid by the current payment term line.
                percentage_paid = abs(aml.amount_residual_currency / self.amount_total)
                for tax_detail in tax_computation_per_percentage[aml.discount_percentage].values():
                    tax_rep = self.env['account.tax.repartition.line'].browse(tax_detail['tax_repartition_line_id'])
                    tax = tax_rep.tax_id

                    grouping_dict = {
                        'account_id': tax_detail['account_id'],
                        'partner_id': tax_detail['partner_id'],
                        'currency_id': tax_detail['currency_id'],
                        'analytic_distribution': tax_detail['analytic_distribution'],
                        'analytic_distribution_area': tax_detail['analytic_distribution_area'],
                        'analytic_distribution_activity': tax_detail['analytic_distribution_activity'],
                        'analytic_distribution_task': tax_detail['analytic_distribution_task'],
                        'tax_repartition_line_id': tax_rep.id,
                        'tax_ids': tax_detail['tax_ids'],
                        'tax_tag_ids': tax_detail['tax_tag_ids'],
                        'group_tax_id': tax_detail['tax_id'] if tax_detail['tax_id'] != tax.id else None,
                    }

                    res['tax_lines'][aml][frozendict(grouping_dict)] = {
                        'name': _("Early Payment Discount (%s)", tax.name),
                        'amount_currency': aml.currency_id.round(tax_detail['amount_currency'] * percentage_paid),
                        'balance': aml.company_currency_id.round(tax_detail['balance'] * percentage_paid),
                        'tax_tag_invert': True,
                    }

                for grouping_dict, base_detail in base_per_percentage[aml.discount_percentage].items():
                    res['base_lines'][aml][grouping_dict] = {
                        'name': _("Early Payment Discount"),
                        'amount_currency': aml.currency_id.round(base_detail['amount_currency'] * percentage_paid),
                        'balance': aml.company_currency_id.round(base_detail['balance'] * percentage_paid),
                    }

                # Fix the rounding issue if any.
                delta_amount_currency = term_amount_currency \
                                        - sum(x['amount_currency'] for x in res['base_lines'][aml].values()) \
                                        - sum(x['amount_currency'] for x in res['tax_lines'][aml].values())
                delta_balance = term_balance \
                                - sum(x['balance'] for x in res['base_lines'][aml].values()) \
                                - sum(x['balance'] for x in res['tax_lines'][aml].values())

                last_tax_line = (list(res['tax_lines'][aml].values()) or list(res['base_lines'][aml].values()))[-1]
                last_tax_line['amount_currency'] += delta_amount_currency
                last_tax_line['balance'] += delta_balance

            else:
                grouping_dict = {'account_id': cash_discount_account.id}

                res['term_lines'][aml][frozendict(grouping_dict)] = {
                    'name': _("Early Payment Discount"),
                    'partner_id': aml.partner_id.id,
                    'currency_id': aml.currency_id.id,
                    'amount_currency': term_amount_currency,
                    'balance': term_balance,
                }

        return res