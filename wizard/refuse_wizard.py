from odoo import api, fields, models
from odoo.exceptions import UserError


class HelpdeskRefuseWizard(models.TransientModel):
    _name = 'helpdesk.refuse.wizard'
    _description = 'Refuse Ticket Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    ticket_name = fields.Char(
        related='ticket_id.name',
        string='Ticket Reference',
        readonly=True,
    )
    refused_reason = fields.Text(
        string='Refusal Reason',
        required=True,
        help='Provide a clear reason for refusing this ticket. '
             'This will be visible to the ticket submitter via the chatter.',
    )

    def action_confirm_refuse(self):
        """Persist the refusal on the ticket and post a chatter message."""
        self.ensure_one()
        ticket = self.ticket_id

        if ticket.approval_state != 'in_review':
            raise UserError('This ticket is no longer waiting for approval.')

        # Move to the Approval Rejected stage if it exists
        rejected_stage = self.env['helpdesk.ticket.stage'].search(
            [('name', 'ilike', 'Approval Rejected')],
            order='sequence asc',
            limit=1,
        )

        write_vals = {
            'approval_state': 'refused',
            'refused_reason': self.refused_reason,
        }
        if rejected_stage:
            write_vals['stage_id'] = rejected_stage.id

        ticket.write(write_vals)

        # Notify submitter via chatter
        partner_ids = []
        if ticket.employee_id.user_id and ticket.employee_id.user_id.partner_id:
            partner_ids.append(ticket.employee_id.user_id.partner_id.id)

        ticket.message_post(
            body=(
                f'<b>Ticket Refused ✗</b><br/>'
                f'Refused by <b>{self.env.user.name}</b>.<br/>'
                f'<b>Reason:</b> {self.refused_reason}'
            ),
            partner_ids=partner_ids,
        )
        return {'type': 'ir.actions.act_window_close'}
