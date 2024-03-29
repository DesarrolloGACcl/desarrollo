/** @odoo-module **/


import { registry } from "@web/core/registry";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";

export class AnalyticDistributionArea extends AnalyticDistribution {
    async fetchAllPlans(nextProps) {
        // TODO: Optimize to execute once for all records when `force_applicability` is set}
        console.log('Entro al metodo heredado')
        
        const argsPlan = this.fetchPlansArgs(nextProps);
        console.log(nextProps)
        console.log('this.state.showDropdown')
        console.log(this.state.showDropdown)
        console.log('this.dropdownRef.el')
        console.log(this.dropdownRef.el)
        
        //traerse el campo que estas haciendo click, para que dependiendo del campo
        //usar la funcion que corresponda
        // o probar opcion de daniel y usar area actividad y tarea en js individuales
        // y a cada uno ponerle widget distinto
        this.allPlans = await this.orm.call("account.analytic.plan", "get_relevant_plans", [], argsPlan);
    }
}
 
registry.category("fields").add("analytic_distribution", AnalyticDistributionArea, { force: true });