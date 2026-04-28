"""Stage model for the helpdesk ticket pipeline."""

from odoo import models, fields


class HelpdeskTicketStage(models.Model):
    _name = 'helpdesk.ticket.stage'
    _description = 'Helpdesk Ticket Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)

    # ── Stage-type flags ──────────────────────────────────────────────────────
    is_done_stage = fields.Boolean(
        string='Is Done Stage',
        help='When True, moving a ticket here triggers the approval process.',
    )
    is_cancelled_stage = fields.Boolean(
        string='Is Cancelled Stage',
        help='Marks this stage as a closed / cancelled state.',
    )
    is_approval_stage = fields.Boolean(
        string='Is "For Approval" Stage',
        help='Internal flag: the stage that triggers Waiting Approval state.',
    )

    fold = fields.Boolean(
        string='Folded in Kanban',
        help='Fold this column by default in the Kanban pipeline.',
    )
    description = fields.Text(string='Internal Notes')
