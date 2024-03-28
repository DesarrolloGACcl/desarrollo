import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { registry } from "@web/core/registry";

import { _lt } from "@web/core/l10n/translation";

 
export class AnalyticDistributionArea extends AnalyticDistribution {
    async fetchAllPlans(nextProps) {
        const argsPlan = this.fetchPlansArgs(nextProps);
        this.allPlans = await this.orm.call("account.analytic.plan", "get_area_relevant_plans", [], argsPlan);
    }
}
 
registry.category("fields").add("analytic_distribution", AnalyticDistributionArea);