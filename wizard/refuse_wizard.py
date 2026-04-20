from odoo import api, fields, models


class HelpdeskRefuseWizard(models.TransientModel):
    _name = 'helpdesk.refuse.wizard'
    _description = 'Helpdesk Ticket Refusal Wizard'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', required=True, readonly=True)
    refused_reason = fields.Text(string='Refusal Reason', required=True)

    def action_confirm_refusal(self):
        # Confirm the refusal and update the linked ticket
        # According to refined spec: state='refused', stage_id='In Progress', refused_reason saved
        self.ensure_one()
        stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'In Progress')], limit=1)
        values = {
            'state': 'refused',
            'refused_reason': self.refused_reason,
        }
        if stage:
            values['stage_id'] = stage.id
        self.ticket_id.write(values)
        self.ticket_id.message_post(body=f"Ticket has been refused. Reason: {self.refused_reason}")
        return {'type': 'ir.actions.act_window_close'}