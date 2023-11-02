import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    kw_examination_type_ids = fields.Many2one(
        comodel_name='kw.gem.examination.type', string='Examination types',
        ondelete='cascade',
    )
    kw_is_research = fields.Boolean(
        string='Is research', default=True)
    kw_abbreviation = fields.Many2one(
        comodel_name='kw.gem.examination.type.code', string='Abbreviation',
        ondelete='cascade',)

    @api.onchange('kw_examination_type_ids')
    def _onchange_kw_examination_type_ids(self):
        for obj in self:
            obj.kw_abbreviation = obj.kw_examination_type_ids.code

    @api.onchange('kw_abbreviation')
    def _onchange_kw_abbreviation(self):
        for obj in self:
            obj.kw_examination_type_ids = self.env[
                'kw.gem.examination.type'].search(
                [('code', '=', obj.kw_abbreviation.id)])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('kw_examination_type_ids')
    def _onchange_kw_examination_type_ids(self):
        for obj in self:
            obj.kw_abbreviation = obj.kw_examination_type_ids.code

    @api.onchange('kw_abbreviation')
    def _onchange_kw_abbreviation(self):
        for obj in self:
            obj.kw_examination_type_ids = self.env[
                'kw.gem.examination.type'].search(
                [('code', '=', obj.kw_abbreviation.id)])


class SampleType(models.Model):
    _name = 'kw.gem.examination.type'

    name = fields.Char(
        required=True, translate=True, )
    name_ge = fields.Char()
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'examination.type' model must be unique!")]
    full_name = fields.Char(
        compute_sudo=True,
        compute="_compute_full_name")
    code = fields.Many2one(
        comodel_name='kw.gem.examination.type.code', required=True, )

    def _compute_full_name(self):
        for obj in self:
            obj.write({
                'full_name': f"{obj.with_context(lang='en_US').name} / "
                             f"{obj.with_context(lang='ka_GE').name}"})

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result


class SampleTypeCode(models.Model):
    _name = 'kw.gem.examination.type.code'

    name = fields.Char(translate=True, required=True, )
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'examination.code' model must be unique!")]
