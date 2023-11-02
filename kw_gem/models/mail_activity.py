from odoo import api, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def change_access_rules_laboratory_assistant(self, can_write=False):
        if self.env.user.id in self.env.ref(
                "kw_gem.group_kw_gem_laboratory_assistant").users.ids:
            self.env.ref(
                "kw_gem.access_sale_order_group_kw_gem_sale_user").sudo(
                ).write({'perm_write': can_write})

    def _filter_access_rules(self, operation):
        self.change_access_rules_laboratory_assistant(can_write=True)
        res = super()._filter_access_rules(operation)
        self.change_access_rules_laboratory_assistant(can_write=False)
        return res

    def _filter_access_rules_python(self, operation):
        self.change_access_rules_laboratory_assistant(can_write=True)
        res = super()._filter_access_rules_python(operation)
        self.change_access_rules_laboratory_assistant(can_write=False)
        return res

    @api.model
    def _search(self, args, offset=0, limit=None,
                order=None, count=False, access_rights_uid=None):
        self.change_access_rules_laboratory_assistant(can_write=True)
        res = super()._search(
            args=args, offset=0, limit=None,
            order=None, count=False, access_rights_uid=None)
        self.change_access_rules_laboratory_assistant(can_write=False)
        return res

    def _action_done(self, feedback=False, attachment_ids=None):
        self.change_access_rules_laboratory_assistant(can_write=True)
        res = super()._action_done(feedback, attachment_ids)
        self.change_access_rules_laboratory_assistant(can_write=False)
        return res

    def _filter_access_rules_remaining(
            self, valid, operation, filter_access_rules_method):
        self.change_access_rules_laboratory_assistant(can_write=True)
        res = super()._filter_access_rules_remaining(
            valid, operation, filter_access_rules_method)
        self.change_access_rules_laboratory_assistant(can_write=False)
        return res
