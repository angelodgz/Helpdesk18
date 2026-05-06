from odoo import api, fields, models


class HelpdeskTicketStage(models.Model):
    _name = 'helpdesk.ticket.stage'
    _description = 'Helpdesk Ticket Stage'
    _order = 'sequence asc, id asc'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Controls the order stages appear in the Kanban pipeline.',
    )
    is_done_stage = fields.Boolean(
        string='Done Stage',
        default=False,
        help='When checked, moving a ticket to this stage triggers the approval process.',
    )
    is_cancelled_stage = fields.Boolean(
        string='Cancelled Stage',
        default=False,
        help='When checked, tickets in this stage are considered cancelled.',
    )
    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='Fold this stage by default in the Kanban view.',
    )
    description = fields.Text(
        string='Internal Notes',
        help='Optional internal description of what this stage represents.',
    )
    # Count of tickets in this stage (used for Kanban header)
    ticket_count = fields.Integer(
        string='Tickets',
        compute='_compute_ticket_count',
    )

    def _compute_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            domain=[('stage_id', 'in', self.ids)],
            groupby=['stage_id'],
            aggregates=['__count'],
        )
        counts = {stage.id: count for stage, count in ticket_data}
        for stage in self:
            stage.ticket_count = counts.get(stage.id, 0)
