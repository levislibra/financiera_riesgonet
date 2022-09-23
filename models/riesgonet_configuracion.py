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
	solicitar_informe_enviar_a_revision = fields.Boolean('Solicitar informe al enviar a revision')
	vr = fields.Integer('Grupo de variables')
	nro_grupo_vid = fields.Integer('Grupo VID')
	nro_grupo_vid2 = fields.Integer('Grupo VID 2do intento')
	riesgonet_variable_1 = fields.Char('Variable 1')
	riesgonet_variable_2 = fields.Char('Variable 2')
	riesgonet_variable_3 = fields.Char('Variable 3')
	riesgonet_variable_4 = fields.Char('Variable 4')
	riesgonet_variable_5 = fields.Char('Variable 5')
	
	asignar_nombre_cliente = fields.Boolean('Asignar Nombre al cliente')
	asignar_nombre_cliente_variable = fields.Char('Variable para el Nombre', default='VI_RazonSocial')
	
	asignar_direccion_cliente = fields.Boolean('Asignar Direccion al cliente')
	asignar_calle_cliente_variable = fields.Char('Variable para la calle', default='VI_DomAF_Calle')
	asignar_nro_cliente_variable = fields.Char('Variable para el Nro', default='VI_DomAF_Nro')
	asignar_piso_cliente_variable = fields.Char('Variable para el Piso', default='VI_DomAF_Piso')
	asignar_departamento_cliente_variable = fields.Char('Variable para el Departamento', default='VI_DomAF_Dto')

	asignar_ciudad_cliente = fields.Boolean('Asignar Ciudad a direccion')
	asignar_ciudad_cliente_variable = fields.Char('Variable para la ciudad', default='VI_DomAF_Loc')

	asignar_cp_cliente = fields.Boolean('Asignar CP a direccion')
	asignar_cp_cliente_variable = fields.Char('Variable para el CP', default='VI_DomAF_CP')

	asignar_provincia_cliente = fields.Boolean('Asignar Provincia a direccion')
	asignar_provincia_cliente_variable = fields.Char('Variable para la Provincia', default='VI_DomAF_Prov')

	asignar_identificacion_cliente = fields.Boolean('Asignar identificacion al cliente')
	asignar_identificacion_cliente_variable = fields.Char('Variable para la identificacion', default='VI_Identificacion')

	asignar_genero_cliente = fields.Boolean('Asignar genero al cliente')
	asignar_genero_cliente_variable = fields.Char('Variable para genero', default='VI_Sexo')

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
