import logging

from odoo import models, fields

logger = logging.getLogger(__name__)


class CreatePartnerWizard(models.TransientModel):
    _name = "create.partner.wizard"
    _description = "Wizard that creates partner, that's it."

    names = fields.Char()
    country_id = fields.Many2one(
        comodel_name='res.country'
    )
    company_type = fields.Selection(
        selection=[('s', 'small company'), ('m', 'medium company'), ('l', 'large company')]
    )