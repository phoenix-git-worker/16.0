from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    kw_header_to_template = fields.Text(
        string='Header to template', translate=True)
