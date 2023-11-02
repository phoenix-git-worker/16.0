import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SampleWizard(models.TransientModel):
    _name = 'kw.gem.sample.wizard'
    _description = 'Sample Wizard'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order', required=True, )
    sample_name_ids = fields.Many2many(
        context={'active_test': False},
        comodel_name='kw.gem.sample.name', required=True, )
    all_sample_type_ids = fields.Many2many(
        relation='gem_sample_wizard_all_sample_type_ids_rel',
        comodel_name='kw.gem.sample.type', required=True, )
    sample_type_ids = fields.Many2many(
        relation='gem_sample_wizard_sample_type_ids_rel',
        comodel_name='kw.gem.sample.type', required=True,
        domain="[('id', 'in', all_sample_type_ids)]")
    all_examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type',
        rel='gem_all_examination_type_ids_rel')
    examination_type_ids = fields.Many2many(
        comodel_name='kw.gem.examination.type', required=True,
        string='Examination types', relation='gem_examination_type_ids_rel',
        domain="[('id', 'in', all_examination_type_ids)]")

    doctor_ids = fields.Many2many(
        comodel_name='res.users',
        related='sale_order_id.doctor_ids',)
    doctor_id = fields.Many2one(comodel_name='res.users')

    macroscopy = fields.Text()
    cassettes_number = fields.Integer(
        string='Number of Cassettes to Create')

    def add_sample(self):
        self.ensure_one()
        data = {
            'sale_order_id': self.sale_order_id.id,
            'doctor_id': self.doctor_id.id,
            'description': self.macroscopy,
            'sample_name_ids': self.sample_name_ids.ids,
            'sample_type_ids': self.sample_type_ids.ids,
            'examination_type_default_id': self.examination_type_ids.ids[-1],
            'examination_type_ids': self.examination_type_ids.ids, }
        if self.cassettes_number:
            data.update({'number_of_cassettes': self.cassettes_number})
        sample_id = self.env['kw.gem.sample'].create(data)
        if self.macroscopy:
            sample_id.sudo().write({'state': 'described'})
        if self.cassettes_number and sample_id:
            if sample_id.state != 'described':
                sample_id.sudo().write({'state': 'described'})
            sample_id.create_cassettes()
            sample_id.sudo().write({'state': 'cassettes'})
        return sample_id
