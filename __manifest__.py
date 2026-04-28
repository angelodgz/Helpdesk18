{
    'name': 'Helpdesk Ticket',
    'version': '18.0.1.0.0',
    'summary': 'Ticketing System with Stage-Based Workflow & Approval',
    'description': """
        Full-featured Helpdesk Ticketing System for Odoo 18.
        Features:
        - Stage-based workflow with Kanban pipeline
        - Approval process (Manager Approve / Refuse with wizard)
        - Dynamic fields per ticket category
        - All 7 views: Form, List, Kanban, Pivot, Graph, Calendar, Activity
        - Role-based access control (User, Agent, Manager)
        - Chatter integration and activity tracking
        - Smart buttons on hr.employee form
        - Auto-generated TKT-XXXX sequence
    """,
    'author': 'Elyon Interns',
    'category': 'Services/Helpdesk',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        # 1. Security first
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # 2. Data / sequences / stages
        'data/sequence.xml',
        'data/stages.xml',
        # 3. Wizard view (model must exist before its view)
        'wizard/refuse_wizard_views.xml',
        # 4. Main views
        'views/stage_views.xml',
        'views/ticket_views.xml',
        'views/employee_inherit.xml',
        # 5. Menus last (actions must exist first)
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
