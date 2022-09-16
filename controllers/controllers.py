# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraRiesgoNet(http.Controller):
#     @http.route('/financiera_riesgo_net/financiera_riesgo_net/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_riesgo_net/financiera_riesgo_net/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_riesgo_net.listing', {
#             'root': '/financiera_riesgo_net/financiera_riesgo_net',
#             'objects': http.request.env['financiera_riesgo_net.financiera_riesgo_net'].search([]),
#         })

#     @http.route('/financiera_riesgo_net/financiera_riesgo_net/objects/<model("financiera_riesgo_net.financiera_riesgo_net"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_riesgo_net.object', {
#             'object': obj
#         })