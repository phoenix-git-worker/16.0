# -*- coding: utf-8 -*-
from odoo import http


class HospitalDev(http.Controller):
    @http.route('/hospital_dev/hospital_dev', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/hospital_dev/hospital_dev/objects', auth='public')
    def list(self, **kw):
        return http.request.render('hospital_dev.listing', {
            'root': '/hospital_dev/hospital_dev',
            'objects': http.request.env['hospital_dev.hospital_dev'].search([]),
        })

    @http.route('/hospital_dev/hospital_dev/objects/<model("hospital_dev.hospital_dev"):obj>', auth='public')
    def object(self, obj, **kw):
        return http.request.render('hospital_dev.object', {
            'object': obj
        })
