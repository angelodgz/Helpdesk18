{
    'name': 'Helpdesk Ticket',
    'version': '18.0.1.0.0',
    'summary': 'Ticketing System with Stage-Based Workflow and Approval',
    'description': """
        A fully functional Ticketing System that allows employees to create,
        manage, and track support/service tickets through defined stages —
        complete with dynamic fields, file attachments, an approval process,
        a reporting dashboard with multiple views, and proper access control.
    """,
    'category': 'Services/Helpdesk',
    'author': 'Elyon Interns',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        # Security — load groups first, then access rules
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # Seed data
        'data/sequence.xml',
        'data/stages.xml',
        # Views
        'views/stage_views.xml',
        'views/ticket_views.xml',
        'views/employee_inherit.xml',
        'wizard/refuse_wizard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
