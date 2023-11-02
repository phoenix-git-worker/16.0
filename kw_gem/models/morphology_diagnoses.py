import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MorphologyDiagnoses(models.Model):
    _name = 'kw.gem.morphology.diagnoses'

    code = fields.Char(
        required=True, )
    name = fields.Char(
        required=True, translate=True, )
    name_ge = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the 'sample.name' model must be unique!")]

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result


class ICDTDiagnoses(models.Model):
    _name = 'kw.gem.icd.t.diagnoses'

    name = fields.Char(
        required=True, translate=True, )
    name_ge = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         "The 'Name' field in the "
         "'kw.gem.icd.t.diagnoses' model must be unique!")]

    @api.model
    def create(self, vals_list):
        result = super().create(vals_list)
        for obj in result:
            if obj.name_ge and self.env['res.lang']._lang_get('ka_GE'):
                obj.with_context(lang='ka_GE').write(
                    {'name': obj.name_ge})
        return result
