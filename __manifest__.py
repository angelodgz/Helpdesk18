{
    'name': 'Helpdesk Ticket',
    'version': '1.0',
    'summary': 'Basic helpdesk ticket module',
    'author': 'You',
    'category': 'Tools',
    'depends': ['base', 'mail', 'hr'],
'data': [
        'security/groups.xml', 
        'security/ir.model.access.csv', 
        'data/sequence.xml',
        'data/stages.xml',
        'wizard/refuse_wizard_views.xml',
        'views/ticket_views.xml',         # LOAD VIEWS BAGO MENU
        'views/stage_views.xml',
        'views/employee_inherit.xml',
        'views/menus.xml',               
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}