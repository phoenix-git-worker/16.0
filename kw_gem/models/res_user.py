
from odoo import models, fields, api


class User(models.Model):
    _inherit = 'res.users'

    kw_conclusion_signature_name = fields.Text(translate=True)
    kw_facsimile = fields.Binary(string='Conclusion Facsimile')
    kw_facsimile_str = fields.Char(compute='_compute_kw_facsimile_str')
    is_head_doctor = fields.Boolean(
        default=False, )
    kw_position_for_conclusion_signature = fields.Char(translate=True)

    @api.constrains('is_head_doctor')
    def _check_head_doctor(self):
        for obj in self:
            if obj.is_head_doctor:
                for user in self.env['res.users'].sudo().search(
                        [('id', '!=', obj.id)]):
                    user.is_head_doctor = False

    def _compute_kw_facsimile_str(self):
        self.kw_facsimile_str = ''
        if self.kw_facsimile:
            self.kw_facsimile_str = str(self.kw_facsimile)[2:-1]
