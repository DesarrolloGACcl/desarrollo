# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

{
    'name': 'Accounting Report Excel',
    'version': '16.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Accounting',
    'live_test_url': 'https://www.youtube.com/watch?v=Sch1VcrunT0&list=PLeJtXzTubzj_wOC0fzgSAyGln4TJWKV4k&index=33',
    'summary': """Generates Excel report for Partner Ledger,General Ledger,Balance Sheet,
                Profit and Loss,Aged Partner Balance.""",
    'description': """Generates Excel reports, 
                    Accounting Reports, Odoo 14, Odoo 14 report,Odoo 14 Accounting Report,Odoo 14 Excel Report, Partner Profit and Loss,Aged Partner Balance,Ledger,General Ledger,Balance Sheet,Account Reports, Excel Report, Excel, Xlsx Report, xlsx,Accounting Excel Reports, Account Excel Reports""",
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_agedpartnerbalance.xml',
        'wizard/partner_ledger_wizard_view.xml',
        'views/partner_ledgerreport.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_financial_report_view.xml',
        'views/account_financial_report_data.xml',
    ],
    'license': 'OPL-1',
    'price': 19.99,
    'currency': 'EUR',
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'account_reports_xlsx/static/src/js/action_manager.js',
        ], }
}
