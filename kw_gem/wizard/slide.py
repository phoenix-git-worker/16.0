import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SlideWizard(models.TransientModel):
    _name = 'kw.gem.slide.wizard'
    _description = 'Slide Wizard'

    cassette_id = fields.Many2one(
        comodel_name='kw.gem.cassette', required=True, )
    cassette_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        related='cassette_id.examination_type_ids')
    examination_id = fields.Many2one(
        comodel_name='kw.gem.examination.type', required=True,
        string='Examination types', )

    def add_slide(self):
        self.ensure_one()
        self.env['kw.gem.slide'].create({
            'cassette_id': self.cassette_id.id,
            'examination_id': self.examination_id.id, })
