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

    # move_project_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Proyecto',
    #     store = True,
    #     readonly=False,
    # )

    # move_area_analytic__plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Área',
    #     store = True,
    #     readonly=False,
    # )

    # move_activity_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Actividad',
    #     store = True,
    #     readonly=False,
    # )

    # sale_project_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Proyecto',
    #     store = True,
    #     readonly=False,
    # )

    # sale_area_analytic__plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Área',
    #     store = True,
    #     readonly=False,
    # )

    # sale_activity_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Actividad',
    #     store = True,
    #     readonly=False,
    # )

    # purchase_project_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Proyecto',
    #     store = True,
    #     readonly=False,
    # )

    # purchase_area_analytic__plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Área',
    #     store = True,
    #     readonly=False,
    # )

    # purchase_activity_analytic_plan_id = fields.Many2one(
    #     'account.analytic.plan',
    #     string = 'Actividad',
    #     store = True,
    #     readonly=False,
    # )