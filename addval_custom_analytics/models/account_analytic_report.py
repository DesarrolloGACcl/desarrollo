from odoo import models, fields, api, osv
from psycopg2 import sql
from odoo.addons.web.controllers.utils import clean_action

class AccountReport(models.AbstractModel):
    _inherit='account.analytic.report'

    @api.model
    def _prepare_lines_for_analytic_groupby(self):
        """Prepare the analytic_temp_account_move_line

        This method should be used once before all the SQL queries using the
        table account_move_line for the analytic columns for the financial reports.
        It will create a new table with the schema of account_move_line table, but with
        the data from account_analytic_line.

        We inherit the schema of account_move_line, make the correspondence between
        account_move_line fields and account_analytic_line fields and put NULL for those
        who don't exist in account_analytic_line.
        We also drop the NOT NULL constraints for fields who are not required in account_analytic_line.
        """
        self.env.cr.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name='analytic_temp_account_move_line'")
        if self.env.cr.fetchone():
            return

        line_fields = self.env['account.move.line'].fields_get()
        self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='account_move_line'")
        stored_fields = set(f[0] for f in self.env.cr.fetchall() if f[0] in line_fields)
        changed_equivalence_dict = {
            "id": sql.Identifier("id"),
            "balance": sql.SQL("-amount"),
            "company_id": sql.Identifier("company_id"),
            "journal_id": sql.Identifier("journal_id"),
            "display_type": sql.Literal("product"),
            "parent_state": sql.Literal("posted"),
            "date": sql.Identifier("date"),
            "account_id": sql.Identifier("general_account_id"),
            "partner_id": sql.Identifier("partner_id"),
            "debit": sql.SQL("CASE WHEN (amount < 0) THEN amount else 0 END"),
            "credit": sql.SQL("CASE WHEN (amount > 0) THEN amount else 0 END"),
        }
        selected_fields = []
        for fname in stored_fields:
            if fname in changed_equivalence_dict:
                selected_fields.append(sql.SQL('{original} AS "account_move_line.{asname}"').format(
                    original=changed_equivalence_dict[fname],
                    asname=sql.SQL(fname),
                ))
            elif fname == 'analytic_distribution':
                selected_fields.append(sql.SQL('to_jsonb(account_id) AS "account_move_line.analytic_distribution"'))
            elif fname == 'analytic_distribution_area':
                selected_fields.append(sql.SQL('to_jsonb(account_id) AS "account_move_line.analytic_distribution_area"'))
            elif fname == 'analytic_distribution_activity':
                selected_fields.append(sql.SQL('to_jsonb(account_id) AS "account_move_line.analytic_distribution_activity"'))
            else:
                if line_fields[fname].get("translate"):
                    typecast = sql.SQL('jsonb')
                elif line_fields[fname].get("type") == "monetary":
                    typecast = sql.SQL('numeric')
                elif line_fields[fname].get("type") == "many2one":
                    typecast = sql.SQL('integer')
                elif line_fields[fname].get("type") == "datetime":
                    typecast = sql.SQL('date')
                elif line_fields[fname].get("type") == "selection":
                    typecast = sql.SQL('text')
                else:
                    typecast = sql.SQL(line_fields[fname].get("type"))
                selected_fields.append(sql.SQL('cast(NULL AS {typecast}) AS "account_move_line.{fname}"').format(
                    typecast=typecast,
                    fname=sql.SQL(fname),
                ))

        query = sql.SQL("""
            -- Create a temporary table, dropping not null constraints because we're not filling those columns
            CREATE TEMPORARY TABLE IF NOT EXISTS analytic_temp_account_move_line () inherits (account_move_line) ON COMMIT DROP;
            ALTER TABLE analytic_temp_account_move_line NO INHERIT account_move_line;
            ALTER TABLE analytic_temp_account_move_line ALTER COLUMN move_id DROP NOT NULL;
            ALTER TABLE analytic_temp_account_move_line ALTER COLUMN currency_id DROP NOT NULL;

            INSERT INTO analytic_temp_account_move_line ({all_fields})
            SELECT {table}
            FROM (SELECT * FROM account_analytic_line WHERE general_account_id IS NOT NULL) AS account_analytic_line
        """).format(
            all_fields=sql.SQL(', ').join(sql.Identifier(fname) for fname in stored_fields),
            table=sql.SQL(', ').join(selected_fields),
        )

        # TODO gawa need to do the auditing of the lines
        # TODO gawa try to reduce query on analytic lines

        self.env.cr.execute(query)

    def _query_get(self, options, date_scope, domain=None):

        context_self = self.with_context(account_report_analytic_groupby=options.get('analytic_groupby_option'))

        tables, where_clause, where_params =super(AccountReport, context_self)._query_get(options, date_scope, domain)
        if options.get('analytic_accounts') and not any(x in options.get('analytic_accounts_list', []) for x in options['analytic_accounts']):
            where_clause = f'{where_clause} AND "account_move_line".analytic_distribution_area ?| array[%s]'
            where_clause = f'{where_clause} AND "account_move_line".analytic_distribution_activity ?| array[%s]'
        
        return tables, where_clause, where_params
    
    def action_audit_cell(self, options, params):
        column_group_options = self._get_column_group_options(options, params['column_group_key'])

        if not column_group_options.get('analytic_groupby_option'):
            return super(AccountReport, self).action_audit_cell(options, params)
        else:
            # Start by getting the domain from the options. Note that this domain is targeting account.move.line
            report_line = self.env['account.report.line'].browse(params['report_line_id'])
            expression = report_line.expression_ids.filtered(lambda x: x.label == params['expression_label'])
            line_domain = self._get_audit_line_domain(column_group_options, expression, params)
            # The line domain is made for move lines, so we need some postprocessing to have it work with analytic lines.
            domain = []
            AccountAnalyticLine = self.env['account.analytic.line']
            for expression in line_domain:
                if len(expression) == 1:  # For operators such as '&' or '|' we can juste add them again.
                    domain.append(expression)
                    continue

                field, operator, right_term = expression
                # On analytic lines, the account.account field is named general_account_id and not account_id.
                if field.split('.')[0] == 'account_id':
                    field = field.replace('account_id', 'general_account_id')
                    expression = [(field, operator, right_term)]
                # Replace the 'analytic_distribution' by the account_id domain as we expect for analytic lines.
                elif field == 'analytic_distribution':
                    account_ids = tuple(int(account_id) for account_id in column_group_options.get('analytic_accounts_list', []))
                    expression = [('account_id', 'in', account_ids)]
                elif field == 'analytic_distribution_area':
                    account_ids = tuple(int(account_id) for account_id in column_group_options.get('analytic_accounts_list', []))
                    expression = [('account_id', 'in', account_ids)]
                elif field == 'analytic_distribution_activity':
                    account_ids = tuple(int(account_id) for account_id in column_group_options.get('analytic_accounts_list', []))
                    expression = [('account_id', 'in', account_ids)]
                # For other fields not present in on the analytic line model, map them to get the info from the move_line.
                # Or ignore these conditions if there is no move lines.
                elif field.split('.')[0] not in AccountAnalyticLine._fields:
                    expression = [(f'move_line_id.{field}', operator, right_term)]
                    if options.get('include_analytic_without_aml'):
                        expression = osv.expression.OR([
                            [('move_line_id', '=', False)],
                            expression,
                        ])
                else:
                    expression = [expression]  # just for the extend
                domain.extend(expression)

            action = clean_action(self.env.ref('analytic.account_analytic_line_action_entries')._get_action_dict(), env=self.env)
            action['domain'] = domain
            return action
        
    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        domain = super()._get_options_domain(options, date_scope)

        # Get the analytic accounts that we need to filter on from the options and add a domain for them.
        if 'analytic_accounts_list' in options:
            domain = osv.expression.AND([
                domain,
                [('analytic_distribution', 'in', options.get('analytic_accounts_list', []))],
                [('analytic_distribution_area', 'in', options.get('analytic_accounts_list', []))],
                [('analytic_distribution_activity', 'in', options.get('analytic_accounts_list', []))],
            ])

        return domain
