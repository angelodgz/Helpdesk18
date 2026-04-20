"""Stage model for configurable helpdesk ticket pipeline stages."""

from odoo import models, fields


class HelpdeskTicketStage(models.Model):
    _name = 'helpdesk.ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(default=10, string='Sequence')
    is_done_stage = fields.Boolean(
        string='Is Done Stage',
        help='Indicates this stage is considered completed for the ticket.',
    )
    is_cancelled_stage = fields.Boolean(
        string='Is Cancelled Stage',
        help='Indicates this stage represents a cancelled ticket.',
    )
    fold = fields.Boolean(string='Folded in Kanban', help='Fold this stage in kanban views.')
    description = fields.Text(string='Description')
    