# -*- coding: utf-8 -*-
{
    'name': "Riesgo Net - Informes comerciales",

    'summary': """
        Integración con Riesgo Net""",

    'description': """
        Integración con Riesgo Net
    """,

    'author': "Librasoft",
    'website': "http://www.libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/extends_res_company.xml',
        'views/riesgo_net_configuracion.xml',
        'views/riesgo_net_informe.xml',
        'views/riesgo_net_cda.xml',
        'views/extends_res_partner.xml',
        # 'views/riesgo_net_cuestionario.xml',
        # 'wizards/riesgo_net_pregunta_wizard.xml',
        # 'reports/riesgo_net_reports.xml',
        # 'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}