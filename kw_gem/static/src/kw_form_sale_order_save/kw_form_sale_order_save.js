//** @odoo-module **//

import { registry } from "@web/core/registry";
import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useBus } from '@web/core/utils/hooks';

export class KWFormStatusIndicator extends FormStatusIndicator {
    setup(){
        super.setup();
        useBus(this.env.bus, 'kw_save_form', this.save);
    }
}

export class KWFormController extends FormController {}
KWFormController.components = {
    ...FormController.components,
    FormStatusIndicator: KWFormStatusIndicator,
}
export const kwFormView = {
    ...formView,
    Controller: KWFormController,
}
registry.category("views").add("kw_form_sale_order_save", kwFormView);

