from odoo import models, fields, api # pyright: ignore[reportMissingImports]

class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(default='New', tracking=True)
    employee_id = fields.Many2one('hr.employee', required=True)
    category = fields.Selection([
        ('it', 'IT Support'),
        ('hr', 'HR Request'),
        ('facilities', 'Facilities'),
        ('finance', 'Finance'),
        ('general', 'General'),
    ], default='general', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical'),
    ], default='1', tracking=True)
    description = fields.Text()
    stage_id = fields.Many2one('helpdesk.ticket.stage', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], default='draft', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment')
    date_requested = fields.Datetime()
    date_closed = fields.Date()
    approved_by = fields.Many2one('res.users')
    refused_reason = fields.Text()
    tag_ids = fields.Many2many('helpdesk.tag')
    assigned_to = fields.Many2one('res.users')
    color = fields.Integer()

    # IT Support Fields
    issue_type = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software')
    ])
    urgency = fields.Selection([
        ('low', 'Low'),
        ('high', 'High')
    ])
    device_tag = fields.Char()
    affected_system = fields.Char()

    # HR Request Fields
    request_type = fields.Selection([
        ('leave', 'Leave'),
        ('payroll', 'Payroll')
    ])
    effective_date = fields.Date()
    hr_notes = fields.Text()

    # Facilities Fields
    location = fields.Char()
    facility_type = fields.Selection([
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance')
    ])
    estimated_cost = fields.Float()

    # Finance Fields
    amount = fields.Float()
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank')
    ])
    expected_liquidation_date = fields.Date()



    def action_mark_done(self):
        self.ensure_one()
        self.write({'state': 'in_review'})
        self.message_post(body="Ticket marked as done. Waiting for approval.")

    def action_approve(self):
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
        })
        self.message_post(body="Ticket has been approved.")

    def action_refuse(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refuse Reason',
            'res_model': 'helpdesk.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id},
        }

    def action_reopen(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body="Ticket has been reopened.")

        