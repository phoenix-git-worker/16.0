import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Codes(models.Model):
    _name = 'kw.gem.codes'
    _description = 'Codes'

    name = fields.Char(
        required=True, translate=True, )


class Payroll(models.Model):
    _name = 'kw.gem.payroll'
    _description = 'Payroll'

    name = fields.Char()
    service_id = fields.Many2one(
        related='sale_order_line_id.product_id',
        string='Service', store=True)
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True, ondelete='cascade')
    patient_id = fields.Many2one(
        comodel_name='res.partner', string='Patient',
        related='sale_order_id.kw_patient_id', )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        ondelete='cascade')
    patient_id = fields.Many2one(
        comodel_name='res.partner', string='Patient',
        related='sale_order_id.kw_patient_id', )

    doctor1_id = fields.Many2one(
        comodel_name='res.users')
    doctor2_id = fields.Many2one(
        comodel_name='res.users')
    doctor_ids = fields.Many2many(
        comodel_name='res.users',
        compute_sudo=True,
        compute='_compute_users')
    code_id = fields.Many2one(
        comodel_name='kw.gem.codes')
    is_split_for_payroll = fields.Boolean(
        default=False)

    def _compute_users(self):
        for obj in self:
            doctor_group_ids = [self.env.ref(
                "kw_gem.group_kw_gem_junior_doctor").id]
            other_groups_ids = [
                self.env.ref(
                    "kw_gem.group_kw_gem_labaratory_administrator").id,
                self.env.ref(
                    "kw_gem.group_kw_gem_1_office_administrator").id, ]
            doctors = self.env['res.users'].sudo().search(
                [('groups_id', 'in', doctor_group_ids),
                 ('groups_id', 'not in', other_groups_ids)])
            obj.sudo().write({'doctor_ids': [(6, 0, doctors.ids)]})
