from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── Smart Button 1: Tickets submitted by this employee ──────────────────

    submitted_ticket_count = fields.Integer(
        string='Submitted Tickets',
        compute='_compute_submitted_ticket_count',
    )

    def _compute_submitted_ticket_count(self):
        ticket_data = self.env['helpdesk.ticket']._read_group(
            domain=[('employee_id', 'in', self.ids)],
            groupby=['employee_id'],
            aggregates=['__count'],
        )
        counts = {emp.id: count for emp, count in ticket_data}
        for employee in self:
            employee.submitted_ticket_count = counts.get(employee.id, 0)

    def action_open_submitted_tickets(self):
        self.ensure_one()
        return {
            'name': f'Tickets by {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    # ── Smart Button 2 (Bonus): Tickets assigned to this employee ───────────

    assigned_ticket_count = fields.Integer(
        string='Assigned Tickets',
        compute='_compute_assigned_ticket_count',
    )

    def _compute_assigned_ticket_count(self):
        user_ids = self.mapped('user_id').ids
        if not user_ids:
            for employee in self:
                employee.assigned_ticket_count = 0
            return
        ticket_data = self.env['helpdesk.ticket']._read_group(
            domain=[('assigned_to', 'in', user_ids)],
            groupby=['assigned_to'],
            aggregates=['__count'],
        )
        counts = {user.id: count for user, count in ticket_data}
        for employee in self:
            uid = employee.user_id.id if employee.user_id else False
            employee.assigned_ticket_count = counts.get(uid, 0) if uid else 0

    def action_open_assigned_tickets(self):
        self.ensure_one()
        if not self.user_id:
            return {}
        return {
            'name': f'Tickets Assigned to {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'domain': [('assigned_to', '=', self.user_id.id)],
            'context': {'default_assigned_to': self.user_id.id},
        }
