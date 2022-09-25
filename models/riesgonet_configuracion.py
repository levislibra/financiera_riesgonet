# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests

ENDPOINT_RIESGONET = 'https://ws01.riesgonet.com/rest/variables'

class FinancieraRiesgonetConfiguracion(models.Model):
	_name = 'financiera.riesgonet.configuracion'

	name = fields.Char('Nombre')
	usuario = fields.Char('Usuario')
	password = fields.Char('Password')
	
	ejecutar_cda_al_solicitar_informe = fields.Boolean('Ejecutar CDAs al solicitar informe')
	riesgonet_variable_1 = fields.Char('Variable 1')
	riesgonet_variable_2 = fields.Char('Variable 2')
	riesgonet_variable_3 = fields.Char('Variable 3')
	riesgonet_variable_4 = fields.Char('Variable 4')
	riesgonet_variable_5 = fields.Char('Variable 5')
	
	asignar_nombre = fields.Boolean('Asignar Nombre al cliente')
	asignar_direccion = fields.Boolean('Asignar Direccion al cliente')
	asignar_ciudad = fields.Boolean('Asignar Ciudad a direccion')
	asignar_cp = fields.Boolean('Asignar CP a direccion')
	asignar_provincia = fields.Boolean('Asignar Provincia a direccion')
	asignar_cuit = fields.Boolean('Asignar identificacion al cliente')
	asignar_genero = fields.Boolean('Asignar genero al cliente')

	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.riesgonet.configuracion'))
	
	@api.one
	def test_conexion(self):
		params = {
			'usuario': self.usuario,
			'token': self.token,
		}
		response = requests.get(ENDPOINT_RIESGONET, params)
		if response.status_code == 400:
			raise UserError("La cuenta esta conectada.")
		else:
			raise UserError("Error de conexion.")

class ExtendsResCompany(models.Model):
	_name = 'res.company'
	_inherit = 'res.company'

	riesgonet_configuracion_id = fields.Many2one('financiera.riesgonet.configuracion', 'Configuracion Riesgonet')
