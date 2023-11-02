//** @odoo-module **//

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { TagsList2 } from "./kw_tag_list";
import { useService } from "@web/core/utils/hooks";


export class FieldMany2ManyTagsLink extends Many2ManyTagsField {
    setup(){
       super.setup();
    }
}
FieldMany2ManyTagsLink.components = {
    ...Many2ManyTagsField.components,
    TagsList2,
}
FieldMany2ManyTagsLink.template = "kw_gem.FieldMany2ManyTagsLink";

registry.category("fields").add("many2many_tags_link", FieldMany2ManyTagsLink);
