/** @odoo-module **/

import { makeContext } from "@web/core/context";
import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { sprintf } from "@web/core/utils/strings";


export class KWX2ManyField extends X2ManyField {
    async onAdd({ context, editable } = {}) {
        const record = this.props.record;
        const domain = record.getFieldDomain(this.props.name).toList();
        context = makeContext([record.getFieldContext(this.props.name), context]);
        if (this.isMany2Many) {
            const { string } = this.props.record.activeFields[this.props.name];
            const title = sprintf(this.env._t("Add: %s"), string);
            return this.selectCreate({ domain, context, title });
        }
        if (editable) {
            if (this.list.editedRecord) {
                const proms = [];
                this.list.model.env.bus.trigger("RELATIONAL_MODEL:NEED_LOCAL_CHANGES", { proms });
                await Promise.all([...proms, this.list.editedRecord._updatePromise]);
                if (this.list.editedRecord) {
                    await this.list.editedRecord.switchMode("readonly", { checkValidity: true });
                }
            }
            if (!this.list.editedRecord) {
                let share = 0;
                this.list.records.forEach(item => {
                    share += item.data.share;
                })
                share = 100 - share;
                context.default_share = share;
                this.test = 1;
                return this.addInLine({ context, editable });
            }
            return;
        }
        return this._openRecord({ context });
    }
}
registry.category('fields').add('kw_x2many', KWX2ManyField);