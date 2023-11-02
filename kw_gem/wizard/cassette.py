import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CassetteWizard(models.TransientModel):
    _name = 'kw.gem.cassette.wizard'
    _description = 'Cassette Wizard'

    sample_id = fields.Many2one(
        comodel_name='kw.gem.sample', required=True, )
    sample_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        related='sample_id.examination_type_ids')
    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        string='Examination types', )

    def add_cassette(self):
        self.ensure_one()
        self.env['kw.gem.cassette'].create({
            'sample_id': self.sample_id.id,
            'examination_type_default_id': self.examination_type_ids.ids[-1],
            'examination_type_ids': self.examination_type_ids.ids, })
