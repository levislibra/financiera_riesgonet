# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import time

from requests.auth import HTTPBasicAuth
from requests import Session
from zeep import Client, helpers
from zeep.transports import Transport
import collections


ENDPOINT_RIESGONET_PRODUCCION = 'http://ws.riesgonet.com/variablesrn/?wsdl'
# ENDPOINT_RIESGONET_VID = 'https://ws02.riesgonet.com/rest/validacion'

VARIABLES_RIESGONET = {
	'apellido': 'individualizacion_apellido',
	'nombre': 'individualizacion_nombre',
	'genero': 'individualizacion_genero',
	'cuit': 'individualizacion_cuit',
	'direccion': 'domicilio_calleAlturaPisoDepto',
	'lodalidad': 'domicilio_localidad',
	'provincia': 'domicilio_provincia',
	'cp': 'domicilio_cp_cpa',
}

class ExtendsResPartnerRiesgonet(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	riesgonet_contratado = fields.Boolean('Riesgo Net', compute='_compute_riesgonet_contrtado')
	riesgonet_informe_ids = fields.One2many('financiera.riesgonet.informe', 'partner_id', 'Riesgonet - Informes')
	riesgonet_variable_ids = fields.One2many('financiera.riesgonet.informe.variable', 'partner_id', 'Variables')
	riesgonet_variable_1 = fields.Char('Variable 1')
	riesgonet_variable_2 = fields.Char('Variable 2')
	riesgonet_variable_3 = fields.Char('Variable 3')
	riesgonet_variable_4 = fields.Char('Variable 4')
	riesgonet_variable_5 = fields.Char('Variable 5')
	riesgonet_capacidad_pago_mensual = fields.Float('Riesgonet - CPM', digits=(16,2))
	riesgonet_partner_tipo_id = fields.Many2one('financiera.partner.tipo', 'Riesgonet - Tipo de cliente')

	pregunta_ids = fields.Char('Preguntas')

	# Validacion por cuestionario
	# riesgonet_cuestionario_ids = fields.One2many('financiera.riesgonet.cuestionario', 'partner_id', 'Riesgonet - Cuestionarios')
	# riesgonet_cuestionario_id = fields.Many2one('financiera.riesgonet.cuestionario', 'Riesgonet - Cuestionario actual')

	@api.one
	def _compute_riesgonet_contrtado(self):
		self.riesgonet_contratado = True if self.company_id.riesgonet_configuracion_id else False

	def flatten(self, d, parent_key='', sep='_'):
		items = []
		for k, v in d.items():
			new_key = parent_key + sep + k if parent_key else k
			if isinstance(v, collections.MutableMapping):
				items.extend(self.flatten(v, new_key, sep=sep).items())
			else:
				items.append((new_key, v))
		return dict(items)

	@api.one
	def solicitar_informe_riesgonet(self):
		riesgonet_configuracion_id = self.company_id.riesgonet_configuracion_id
		session = Session()
		session.auth = HTTPBasicAuth(riesgonet_configuracion_id.usuario, riesgonet_configuracion_id.password)
		client = Client(ENDPOINT_RIESGONET_PRODUCCION, transport=Transport(session=session))
		print('client', client)
		sexo = 'M' if self.sexo == 'masculino' else 'F'
		payload = {
			'modoConsulta': '1',
			'identificacion': {
				'usuario': riesgonet_configuracion_id.usuario,
				'password': riesgonet_configuracion_id.password,
				'legajo': 'PRUEBA WEB SERVICE',
			},
			'datosConsulta': {
				'identidad': {
					'dni': self.dni,
					"versionDNI": "",
					'sexo': sexo,
					'apellido': '',
					'nombre': '',
				},
				'fechaNacimiento': '',
			},
		}
		print('payload: ', payload)
		# call post cliente with body
		response = client.service.getVariables_RN(payload)
		response_json = helpers.serialize_object(response, dict)
		print('response', response_json)
		print('response[resultado]', response_json['resultado'])
		if response_json['resultado'] == 0:
			raise ValidationError("Error en la consulta de informe Riesgonet: "+response_json['diagnostico']['detalle'])
		else:
			list_values = []
			flatten_dict = self.flatten(response_json)
			print('flatten_dict', flatten_dict)
			variables = flatten_dict.iteritems()
			print('variables', variables)
			for variable in variables:
				variable_nombre, variable_valor = variable
				variable_values = {
					'partner_id': self.id,
					'name': variable_nombre,
					'valor': variable_valor,
				}
				list_values.append((0,0, variable_values))
			nuevo_informe_id = self.env['financiera.riesgonet.informe'].create({})
			self.riesgonet_informe_ids = [nuevo_informe_id.id]
			self.riesgonet_variable_ids = [(6, 0, [])]
			nuevo_informe_id.write({'variable_ids': list_values})
			self.asignar_variables_riesgonet()
			self.enriquecer_partner_riesgonet()
			if riesgonet_configuracion_id.ejecutar_cda_al_solicitar_informe:
				nuevo_informe_id.ejecutar_cdas()


	@api.one
	def enriquecer_partner_riesgonet(self):
		# start = time.time()
		riesgonet_configuracion_id = self.company_id.riesgonet_configuracion_id
		vals = {}
		variable_apellido_id = False
		variable_nombre_id = False
		if riesgonet_configuracion_id.asignar_nombre:
			variable_apellido_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['apellido'])
			variable_nombre_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['nombre'])
			if variable_apellido_id and variable_nombre_id:
				vals['name'] = variable_apellido_id.valor + ' ' + variable_nombre_id.valor
		if riesgonet_configuracion_id.asignar_direccion:
			variable_direccion_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['direccion'])
			if variable_direccion_id:
				vals['street'] = variable_direccion_id.valor
		if riesgonet_configuracion_id.asignar_ciudad:
			variable_ciudad_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['lodalidad'])
			if variable_ciudad_id:
				vals['city'] = variable_ciudad_id.valor
		if riesgonet_configuracion_id.asignar_cp:
			variable_cp_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['cp'])
			if variable_cp_id:
				vals['zip'] = variable_cp_id.valor
		if riesgonet_configuracion_id.asignar_provincia:
			variable_provincia_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['provincia'])
			if variable_provincia_id:
				self.set_provincia(variable_provincia_id.valor)
		if riesgonet_configuracion_id.asignar_cuit:
			variable_cuit_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['cuit'])
			if variable_cuit_id:
				vals['main_id_category_id'] = 25
				vals['main_id_number'] = variable_cuit_id.valor
		if riesgonet_configuracion_id.asignar_genero:
			variable_genero_id = self.riesgonet_variable_ids.filtered(lambda x: x.name == VARIABLES_RIESGONET['genero'])
			if variable_genero_id:
				if variable_genero_id.valor == 'M':
					vals['sexo'] = 'masculino'
				elif variable_genero_id.valor == 'F':
					vals['sexo'] = 'femenino'
		self.write(vals)
		# end = time.time()
		# delta = end - start
		# print("Time difference in seconds is: ", delta)
		# ms = delta * 1000


	@api.one
	def asignar_variables_riesgonet(self):
		variable_1 = False
		variable_2 = False
		variable_3 = False
		variable_4 = False
		variable_5 = False
		riesgonet_configuracion_id = self.company_id.riesgonet_configuracion_id
		for var_id in self.riesgonet_variable_ids:
			if var_id.name == riesgonet_configuracion_id.riesgonet_variable_1:
				variable_1 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == riesgonet_configuracion_id.riesgonet_variable_2:
				variable_2 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == riesgonet_configuracion_id.riesgonet_variable_3:
				variable_3 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == riesgonet_configuracion_id.riesgonet_variable_4:
				variable_4 = var_id.name + ": " + str(var_id.valor)
			if var_id.name == riesgonet_configuracion_id.riesgonet_variable_5:
				variable_5 = var_id.name + ": " + str(var_id.valor)
		self.write({
			'riesgonet_variable_1': variable_1,
			'riesgonet_variable_2': variable_2,
			'riesgonet_variable_3': variable_3,
			'riesgonet_variable_4': variable_4,
			'riesgonet_variable_5': variable_5,
		})

	@api.one
	def set_provincia(self, provincia):
		if provincia == 'Capital Federal':
			provincia = 'Ciudad Autónoma de Buenos Aires'
		state_obj = self.pool.get('res.country.state')
		state_ids = state_obj.search(self.env.cr, self.env.uid, [
			('name', '=ilike', provincia)
		])
		if len(state_ids) > 0:
			self.state_id = state_ids[0]
			country_id = state_obj.browse(self.env.cr, self.env.uid, state_ids[0]).country_id
			self.country_id = country_id.id

	@api.one
	def ejecutar_cdas_riesgonet(self):
		if self.riesgonet_informe_ids and len(self.riesgonet_informe_ids) > 0:
			self.riesgonet_informe_ids[0].ejecutar_cdas()

	@api.one
	def button_solicitar_informe_riesgonet(self):
		self.solicitar_informe_riesgonet()

	# def obtener_cuestionario_riesgonet(self):
	# 	ret = False
	# 	riesgonet_configuracion_id = self.company_id.riesgonet_configuracion_id
	# 	grupoVid = riesgonet_configuracion_id.nro_grupo_vid
	# 	if len(self.riesgonet_cuestionario_id) > 0:
	# 		grupoVid = riesgonet_configuracion_id.nro_grupo_vid2
	# 	params = {
	# 		'usuario': riesgonet_configuracion_id.usuario,
	# 		'token': riesgonet_configuracion_id.token,
	# 		'NroGrupoVID': grupoVid,
	# 		'documento': self.main_id_number,
	# 		'format': 'json',
	# 	}
	# 	response = requests.get(ENDPOINT_RIESGONET_VID, params)
	# 	data = response.json()
	# 	if response.status_code != 200:
	# 		raise ValidationError("Error en la obtencion del cuestionario Riesgonet: "+data['Contenido']['Resultado']['Novedad'])
	# 	else:
	# 		if data['Contenido']['Resultado']['Estado'] != 200:
	# 			raise ValidationError("Riesgonet: " + data['Contenido']['Resultado']['Novedad'])
	# 		nuevo_cuestionario_id = self.env['financiera.riesgonet.cuestionario'].create({})
	# 		self.riesgonet_cuestionario_ids = [nuevo_cuestionario_id.id]
	# 		self.riesgonet_cuestionario_id = nuevo_cuestionario_id.id
	# 		nuevo_cuestionario_id.id_consulta = data['Contenido']['Datos']['IdConsulta']
	# 		desafios = data['Contenido']['Datos']['Cuestionario']['Desafios']
	# 		for desafio in desafios:
	# 			if 'Pregunta' in desafio:
	# 				pregunta = desafio['Pregunta']
	# 				pregunta_id = self.env['financiera.riesgonet.cuestionario.pregunta'].create({
	# 					'id_pregunta': pregunta['IdPregunta'],
	# 					'texto': pregunta['Texto'],
	# 				})
	# 				nuevo_cuestionario_id.pregunta_ids = [pregunta_id.id]
	# 				i = 0
	# 				for opcion in pregunta['Opciones']:
	# 					opcion_id = self.env['financiera.riesgonet.cuestionario.pregunta.opcion'].create({
	# 						'id_opcion': i,
	# 						'texto': opcion,
	# 					})
	# 					i += 1
	# 					pregunta_id.opcion_ids = [opcion_id.id]
	# 		ret = nuevo_cuestionario_id.id
	# 	return ret

	# @api.one
	# def button_obtener_cuestionario_riesgonet(self):
	# 	self.obtener_cuestionario_riesgonet()

	@api.multi
	def riesgonet_report(self):
		self.ensure_one()
		return self.env['report'].get_action(self, 'financiera_riesgonet.riesgonet_report_view')