import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DevPatient(models.Model):
    _name = 'dev.patient'
    _description = 'Patient'

    name = fields.Char(size=36)
    age = fields.Integer()
    lucky_number = fields.Integer(compute='compute_lucky_number')

    @api.depends('age')
    def compute_lucky_number(self):
        for rec in self:
            rec.lucky_number = round(rec.age * 13 / 10)

    # init comment