from ast import literal_eval

from odoo import models, fields, api, exceptions, _


class MassStageWizard(models.TransientModel):
    _name = 'kw.gem.mass.stage.wizard'
    _description = 'Mass Stage'

    from_stage_id = fields.Many2one(
        comodel_name='generic.process.stage', readonly=True)
    to_stage_id = fields.Many2one(
        comodel_name='generic.process.stage')
    stage_ids = fields.Many2many(
        comodel_name='generic.process.stage')
    model = fields.Char()
    res_ids = fields.Char()

    @api.model
    def default_get(self, vals):
        res = super(MassStageWizard, self).default_get(vals)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        act_ids = self.env[active_model].sudo().search(
            [('id', 'in', active_ids)])
        if len(act_ids.mapped('stage_id')) != 1:
            raise exceptions.UserError(
                _('Error. Select objects with the same status!'))
        stage = act_ids.mapped('stage_id')
        res['from_stage_id'] = stage.id
        right_route_ids = stage.route_out_ids

        allowed_user_ids = right_route_ids.filtered(
            lambda x: x.allowed_user_ids)
        if allowed_user_ids:
            not_allowed_by_user = right_route_ids.filtered(
                lambda x: x.allowed_user_ids not in self.env.user)
            right_route_ids -= not_allowed_by_user

        allowed_group_ids = right_route_ids.filtered(
            lambda x: x.allowed_group_ids)
        if allowed_group_ids:
            not_allowed_by_group = right_route_ids.filtered(
                lambda x: not x.allowed_group_ids & self.env.user.groups_id)
            right_route_ids -= not_allowed_by_group
        stage_ids = right_route_ids.mapped('stage_to_id').filtered(
            lambda x: x.is_mass_change_status)

        if not stage_ids:
            raise exceptions.UserError(
                _('Error. There is no route for this status!'))

        res['stage_ids'] = stage_ids
        res['model'] = self.env.context.get('active_model')
        res['res_ids'] = self.env.context.get('active_ids')
        return res

    def confirm_assign(self):
        self.ensure_one()
        active_ids = self.env[self.model].browse(literal_eval(self.res_ids))
        for active_id in active_ids:
            active_id.sudo().write({'stage_id': self.to_stage_id.id})
            self.change_status(active_id)

    def change_status(self, active_id):
        self.ensure_one()
        if self.model == 'sale.order':
            if active_id.kw_stage != self.to_stage_id.sale_state1:
                active_id.sudo().write({
                    'kw_stage': self.to_stage_id.sale_state1})
        if self.model == 'kw.gem.sample':
            if active_id.state != self.to_stage_id.sample_state:
                active_id.sudo().write({
                    'state': self.to_stage_id.sample_state})
        if self.model == 'kw.gem.cassette':
            if active_id.state != self.to_stage_id.cassette_state:
                active_id.sudo().write({
                    'state': self.to_stage_id.cassette_state})
        if self.model == 'kw.gem.slide':
            if active_id.state != self.to_stage_id.slide_state:
                active_id.sudo().write({
                    'state': self.to_stage_id.slide_state})
