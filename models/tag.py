from odoo import fields, models


class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'
    _order = 'name asc'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='Color index used for the tag widget in form view.',
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'A tag with this name already exists.'),
    ]
