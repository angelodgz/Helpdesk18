"""Transient model: popup dialog for manager to enter a refusal reason."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskRefuseWizard(models.TransientModel):
    _name = 'helpdesk.refuse.wizard'
    _description = 'Helpdesk Ticket Refusal Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True,
    )
    refused_reason = fields.Text(
        string='Refusal Reason',
        required=True,
        help='Provide a clear reason for refusing this ticket.',
    )

    def action_confirm_refusal(self):
        """Confirm the refusal: delegate logic to the ticket model."""
        self.ensure_one()
        if not self.ticket_id:
            raise ValidationError("No ticket is linked to this wizard.")
        if not self.refused_reason or not self.refused_reason.strip():
            raise ValidationError("Please enter a refusal reason before confirming.")

        # Delegate to ticket — keeps business logic in one place
        self.ticket_id.action_apply_refusal(self.refused_reason.strip())

        return {'type': 'ir.actions.act_window_close'}
