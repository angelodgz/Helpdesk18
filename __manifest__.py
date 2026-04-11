{
    'name': 'Helpdesk Ticket',
    'version': '1.0',
    'summary': 'Basic helpdesk ticket module',
    'author': 'You',
    'category': 'Tools',
    'depends': ['base', 'mail', 'hr'],
'data': [
        'security/groups.xml',            # DAPAT MAUNA PARA SA ROLES
        'security/ir.model.access.csv',   # SUNOD ANG PERMISSIONS
        'data/sequence.xml',
        'data/stages.xml',
        'views/ticket_views.xml',         # LOAD VIEWS BAGO MENU
        'views/stage_views.xml',
        'views/employee_inherit.xml',
        'views/menus.xml',                # DAPAT HULI ANG MENU
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}