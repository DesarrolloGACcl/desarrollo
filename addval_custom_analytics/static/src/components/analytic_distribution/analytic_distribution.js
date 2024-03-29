/** @odoo-module **/


import { registry } from "@web/core/registry";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";

export class AnalyticDistributionArea extends AnalyticDistribution {
    async fetchAllPlans(nextProps) {
        // TODO: Optimize to execute once for all records when `force_applicability` is set
        const argsPlan = this.fetchPlansArgs(nextProps);
        this.allPlans = await this.orm.call("account.analytic.plan", "get_area_relevant_plans", [], argsPlan);
    }
}
 
registry.category("fields").add("analytic_distribution", AnalyticDistributionArea, { force: true });