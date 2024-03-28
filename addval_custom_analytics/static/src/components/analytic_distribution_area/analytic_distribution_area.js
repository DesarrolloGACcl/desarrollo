import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { registry } from "@web/core/registry";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { evaluateExpr } from "@web/core/py_js/py";
import { getNextTabableElement, getPreviousTabableElement } from "@web/core/utils/ui";
import { usePosition } from "@web/core/position_hook";
import { getActiveHotkey } from "@web/core/hotkeys/hotkey_service";
import { shallowEqual } from "@web/core/utils/arrays";
import { sprintf } from "@web/core/utils/strings";
import { _lt } from "@web/core/l10n/translation";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TagsList } from "@web/views/fields/many2many_tags/tags_list";
import { useOpenMany2XRecord } from "@web/views/fields/relational_utils";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import { formatPercentage } from "@web/views/fields/formatters";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
 
export class AnalyticDistributionArea extends AnalyticDistribution {
    async fetchAllPlans(nextProps) {
        const argsPlan = this.fetchPlansArgs(nextProps);
        this.allPlans = await this.orm.call("account.analytic.plan", "get_area_relevant_plans", [], argsPlan);
    }
}
 
registry.category("fields").add("analytic_distribution_area", AnalyticDistributionArea);