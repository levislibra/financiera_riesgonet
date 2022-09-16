# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import requests
import xml.etree.ElementTree as ET

ENDPOINT_RIESGONET_TEST = 'https://prepro.online.org.riesgonet.com.ar/pls/consulta817/wserv'
ENDPOINT_RIESGONET_PRODUCCION = 'https://online.org.riesgonet.com.ar/pls/consulta817/wserv'
# ENDPOINT_RIESGONET_VID = 'https://ws02.riesgonet.com/rest/validacion'

class ExtendsResPartnerRiesgonet(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

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

	def riesgonet_xml(self):
		return """
			<?xml version="1.0" encoding="ISO-8859-1"?>
			<mensaje>
				<identificador>
					<userlogon>
						<matriz>
							<![CDATA[completar_matriz]]>
						</matriz>
						<usuario>
							<![CDATA[completar_usuario]]>
						</usuario>
						<password>
							<![CDATA[completar_clave]]>
						</password>
					</userlogon>
					<formatoInforme>H</formatoInforme>
					<reenvio />
					<producto>RISC:Experto</producto>
					<lote>
						<sectorRiesgonet>completar_sector</sectorRiesgonet>
						<sucursalRiesgonet>completar_sucursal</sucursalRiesgonet>
						<cliente>completar_cliente_id</cliente>
					</lote>
				</identificador>
				<consulta>
					<integrantes>1</integrantes>
					<integrante valor="1">
						<sexo>completar_sexo</sexo>
						<documento>
							<![CDATA[completar_documento]]>
						</documento>
					</integrante>
				</consulta>
			</mensaje>
		"""

	@api.one
	def solicitar_informe_riesgonet(self):
		riesgonet_configuracion_id = self.company_id.riesgonet_configuracion_id
		riesgonet_xml = self.riesgonet_xml().replace('\n', '').replace('\t', '')
		riesgonet_xml = riesgonet_xml.replace('completar_matriz', riesgonet_configuracion_id.matriz)
		riesgonet_xml = riesgonet_xml.replace('completar_usuario', riesgonet_configuracion_id.usuario)
		riesgonet_xml = riesgonet_xml.replace('completar_clave', riesgonet_configuracion_id.password)
		# riesgonet_xml.replace('completar_medio', medio)
		riesgonet_xml = riesgonet_xml.replace('completar_sector', riesgonet_configuracion_id.sector)
		riesgonet_xml = riesgonet_xml.replace('completar_sucursal', riesgonet_configuracion_id.sucursal)
		riesgonet_xml = riesgonet_xml.replace('completar_cliente_id', str(self.id))
		# riesgonet_xml.replace('completar_apellido', self.apellido)
		# riesgonet_xml.replace('completar_nombre', self.nombre)
		riesgonet_xml = riesgonet_xml.replace('completar_sexo', 'M' if self.sexo == 'masculino' else 'F')
		riesgonet_xml = riesgonet_xml.replace('completar_documento', str(self.dni))
		print('riesgonet_xml', riesgonet_xml)
		root = ET.fromstring(riesgonet_xml)
		response = requests.get(ENDPOINT_RIESGONET_TEST, data=root)
		print('response', response)
		print('response.text', response.text)
		data = response.json()
		print('data', data)
		if response.status_code != 200:
			raise ValidationError("Error en la consulta de informe Riesgonet: "+data['Contenido']['Resultado']['Novedad'])
		else:
			nuevo_informe_id = self.env['financiera.riesgonet.informe'].create({})
			self.riesgonet_informe_ids = [nuevo_informe_id.id]
			self.riesgonet_variable_ids = [(6, 0, [])]
			direccion = []
			direccion_variables = []
			if riesgonet_configuracion_id.asignar_direccion_cliente:
				if riesgonet_configuracion_id.asignar_calle_cliente_variable:
					direccion_variables.append(riesgonet_configuracion_id.asignar_calle_cliente_variable)
				if riesgonet_configuracion_id.asignar_nro_cliente_variable:
					direccion_variables.append(riesgonet_configuracion_id.asignar_nro_cliente_variable)
				if riesgonet_configuracion_id.asignar_piso_cliente_variable:
					direccion_variables.append(riesgonet_configuracion_id.asignar_piso_cliente_variable)
				if riesgonet_configuracion_id.asignar_departamento_cliente_variable:
					direccion_variables.append(riesgonet_configuracion_id.asignar_departamento_cliente_variable)
			list_values = []
			for variable in data['Contenido']['Datos']['Variables']:
				variable_nombre = variable['Nombre']
				variable_valor = variable['Valor']
				variable_fecha = None
				if 'FechaAct' in variable:
					variable_fecha = variable['FechaAct']
				variable_descripcion = variable['Descripcion']
				variable_tipo = variable['Tipo']
				variable_values = {
					'partner_id': self.id,
					'name': variable_nombre,
					'valor': variable_valor,
					'fecha': variable_fecha,
					'descripcion': variable_descripcion,
					'tipo': variable_tipo,
				}
				list_values.append((0,0, variable_values))
				if riesgonet_configuracion_id.asignar_nombre_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_nombre_cliente_variable:
						self.name = variable_valor
				if riesgonet_configuracion_id.asignar_direccion_cliente:
					if variable_nombre in direccion_variables:
						direccion.append(variable_valor)
				if riesgonet_configuracion_id.asignar_ciudad_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_ciudad_cliente_variable:
						self.city = variable_valor
				if riesgonet_configuracion_id.asignar_cp_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_cp_cliente_variable:
						self.zip = variable_valor
				if riesgonet_configuracion_id.asignar_provincia_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_provincia_cliente_variable:
						self.set_provincia(variable_valor)
				if riesgonet_configuracion_id.asignar_identificacion_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_identificacion_cliente_variable:
						self.main_id_number = variable_valor
				if riesgonet_configuracion_id.asignar_genero_cliente:
					if variable_nombre == riesgonet_configuracion_id.asignar_genero_cliente_variable:
						if variable_valor == 'M':
							self.sexo = 'masculino'
						elif variable_valor == 'F':
							self.sexo = 'femenino'
			nuevo_informe_id.write({'variable_ids': list_values})
			self.asignar_variables()
			if riesgonet_configuracion_id.asignar_direccion_cliente:
				if len(direccion) > 0:
					self.street = ' '.join(direccion)
			if riesgonet_configuracion_id.ejecutar_cda_al_solicitar_informe:
				nuevo_informe_id.ejecutar_cdas()

	@api.one
	def asignar_variables(self):
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