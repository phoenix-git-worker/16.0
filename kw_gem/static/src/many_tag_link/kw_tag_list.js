//** @odoo-module **//

import { TagsList } from "@web/views/fields/many2many_tags/tags_list";
import { useService } from "@web/core/utils/hooks";


export class TagsList2 extends TagsList {
    setup(){
        super.setup();
        this.action = useService("action");
    }
    tagClick(tag){
        const model = this.props.resModel;
        const id = tag.resId;

        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: model,
            res_id: id,
            views: [[false, 'form']],
            target: 'current',
        });

    }
}
TagsList2.template = "kw_gem.TagsList2";
TagsList2.props = {
    ...TagsList.props,
    resModel:{ type: String, required: false}
}
