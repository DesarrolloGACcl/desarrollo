from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    project_analytic_plan_id = fields.Many2one(
        'account.analytic.plan',
        related='company_id.project_analytic_plan_id',
        string = 'Proyecto',
        store = True,
        readonly=False,
    )

    area_analytic__plan_id = fields.Many2one(
        'account.analytic.plan',
        related='company_id.area_analytic_plan_id',
        string = 'Área',
        store = True,
        readonly=False,
    )

    activity_analytic_plan_id = fields.Many2one(
        'account.analytic.plan',
        related='company_id.activity_analytic_plan_id',
        string = 'Actividad',
        store = True,
        readonly=False,
    )

    task_analytic_plan_id = fields.Many2one(
        'account.analytic.plan',
        related='company_id.task_analytic_plan_id',
        string = 'Tarea',
        store = True,
        readonly=False,
    )