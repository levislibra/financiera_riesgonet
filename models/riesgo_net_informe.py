# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraRiesgonetInforme(models.Model):
	_name = 'financiera.riesgonet.informe'
	
	_order = 'create_date desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	# Nueva integracion
	variable_ids = fields.One2many('financiera.riesgonet.informe.variable', 'informe_id', 'Variables')
	cda_resultado_ids = fields.One2many('financiera.riesgonet.cda.resultado', 'informe_id', 'Resultados')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.riesgonet.informe'))
	
	@api.model
	def create(self, values):
		rec = super(FinancieraRiesgonetInforme, self).create(values)
		rec.update({
			'name': 'RIESGONET/INFORME/' + str(rec.id).zfill(8),
		})
		return rec

	@api.one
	def ejecutar_cdas(self):
		cda_obj = self.pool.get('financiera.riesgonet.cda')
		cda_ids = cda_obj.search(self.env.cr, self.env.uid, [
			('activo', '=', True),
			('company_id', '=', self.company_id.id),
		])
		if len(cda_ids) > 0:
			self.partner_id.riesgonet_capacidad_pago_mensual = 0
			self.partner_id.capacidad_pago_mensual = 0
			self.partner_id.riesgonet_partner_tipo_id = None
			self.partner_id.partner_tipo_id = None
		for _id in cda_ids:
			cda_id = cda_obj.browse(self.env.cr, self.env.uid, _id)
			ret = cda_id.ejecutar(self.id)
			if ret['resultado'] == 'aprobado':
				self.partner_id.riesgonet_capacidad_pago_mensual = ret['cpm']
				self.partner_id.capacidad_pago_mensual = ret['cpm']
				self.partner_id.riesgonet_partner_tipo_id = ret['partner_tipo_id']
				self.partner_id.partner_tipo_id = ret['partner_tipo_id']
				break

class FinancieraRiesgonetInformeVariable(models.Model):
	_name = 'financiera.riesgonet.informe.variable'
	
	informe_id = fields.Many2one('financiera.riesgonet.informe', 'Informe')
	partner_id = fields.Many2one('res.partner', 'Cliente')
	name = fields.Char('Nombre')
	valor = fields.Char('Valor')
	fecha = fields.Date('Fecha')
	descripcion = fields.Char('Descripcion')
	tipo = fields.Char('Tipo')
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.riesgonet.informe.variable'))
	