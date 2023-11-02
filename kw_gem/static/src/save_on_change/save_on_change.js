/** @odoo-module **/
//
import { FloatField } from "@web/views/fields/float/float_field";
import { onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class KWSaveOnChange extends FloatField {
    setup(){
        super.setup();
        this.test = 1;

    }
    parse(value) {
        this.env.bus.trigger("kw_save_form");
        return this.props.inputType === "number" ? Number(value) : parseFloat(value);
    }

}

registry.category('fields').add('kw_save_onchange', KWSaveOnChange);