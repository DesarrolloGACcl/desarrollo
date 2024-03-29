/** @odoo-module **/


import { registry } from "@web/core/registry";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";

export class AnalyticDistributionArea extends AnalyticDistribution {
    async fetchAllPlans(nextProps) {
        // TODO: Optimize to execute once for all records when `force_applicability` is set}
        console.log('Entro al metodo heredado')
        
        const argsPlan = this.fetchPlansArgs(nextProps);
        if(nextProps.name == 'analytic_distribution'){
            this.allPlans = await this.orm.call("account.analytic.plan", "get_relevant_plans", [], argsPlan);
        }
        if(nextProps.name == 'analytic_distribution_area'){
            this.allPlans = await this.orm.call("account.analytic.plan", "get_area_relevant_plans", [], argsPlan);
        }
        if(nextProps.name == 'analytic_distribution_activity'){
            this.allPlans = await this.orm.call("account.analytic.plan", "get_activity_relevant_plans", [], argsPlan);
        }
        if(nextProps.name == 'analytic_distribution_task'){
            this.allPlans = await this.orm.call("account.analytic.plan", "get_task_relevant_plans", [], argsPlan);
        }

        console.log(nextProps)
        console.log(this)
        console.log('this.state.showDropdown')
        console.log(this.state.showDropdown)
        console.log('this.dropdownRef.el')
        console.log(this.dropdownRef.el)
        
        //traerse el campo que estas haciendo click, para que dependiendo del campo
        //usar la funcion que corresponda
        // o probar opcion de daniel y usar area actividad y tarea en js individuales
        // y a cada uno ponerle widget distinto
    }
}
 
registry.category("fields").add("analytic_distribution", AnalyticDistributionArea, { force: true });