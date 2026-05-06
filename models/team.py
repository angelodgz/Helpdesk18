from odoo import fields, models


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Support Team'
    _order = 'name asc'

    name = fields.Char(
        string='Team Name',
        required=True,
        translate=True,
    )
    member_ids = fields.Many2many(
        'res.users',
        'helpdesk_team_member_rel',
        'team_id',
        'user_id',
        string='Team Members',
        domain="[('share', '=', False)]",
    )
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index', default=0)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A team with this name already exists.'),
    ]
