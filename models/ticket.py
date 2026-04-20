from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Name", readonly=True, default='New', copy=False)
    employee_id = fields.Many2one('hr.employee', required=True, string='Requesting Employee')
    category = fields.Selection([
        ('it', 'IT Support'),
        ('hr', 'HR Request'),
        ('facilities', 'Facilities'),
        ('finance', 'Finance'),
        ('general', 'General'),
    ], default='general', tracking=True, string='Category')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical'),
    ], default='1', tracking=True, string='Priority')
    description = fields.Text(string='Description')
    stage_id = fields.Many2one(
        'helpdesk.ticket.stage',
        tracking=True,
        string='Stage',
        default=lambda self: self.env['helpdesk.ticket.stage'].search([], order='sequence asc', limit=1),
    )

    # Ribbon indicator fields for the stage selections.
    is_done_stage = fields.Boolean(
        related='stage_id.is_done_stage',
        string="Is Done Stage",
        store=True,
    )
    is_cancelled_stage = fields.Boolean(
        related='stage_id.is_cancelled_stage',
        string="Is Cancelled Stage",
        store=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], default='draft', tracking=True, string='Approval State')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    date_requested = fields.Datetime(default=fields.Datetime.now, string='Date Requested')
    date_closed = fields.Date(string='Date Closed')
    approved_by = fields.Many2one('res.users', string='Approved By')
    refused_reason = fields.Text(string='Refused Reason')
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags')
    assigned_to = fields.Many2one('res.users', string='Assigned To', default=lambda self: self.env.user)
    color = fields.Integer(string='Color Index')

    # IT Support Fields
    issue_type = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software'),
    ], string='Issue Type')
    urgency = fields.Selection([
        ('low', 'Low'),
        ('high', 'High'),
    ], string='Urgency')
    device_tag = fields.Char(string='Device Tag')
    affected_system = fields.Char(string='Affected System')

    # HR Request Fields
    request_type = fields.Selection([
        ('leave', 'Leave'),
        ('payroll', 'Payroll'),
    ], string='Request Type')
    effective_date = fields.Date(string='Effective Date')
    hr_notes = fields.Text(string='HR Notes')

    # Facilities Fields
    location = fields.Char(string='Location')
    facility_type = fields.Selection([
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance'),
    ], string='Facility Type')
    estimated_cost = fields.Float(string='Estimated Cost')

    # Finance Fields
    amount = fields.Float(string='Amount')
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ], string='Payment Mode')
    expected_liquidation_date = fields.Date(string='Expected Liquidation Date')

    def _get_stage_by_name(self, name):
        # Find a pipeline stage record by its name
        return self.env['helpdesk.ticket.stage'].search([('name', '=', name)], limit=1)

    def _get_default_stage(self):
        # Return the first configured stage used for new tickets
        return self.env['helpdesk.ticket.stage'].search([], order='sequence asc', limit=1)

    def action_mark_done(self):
        # Send the ticket for approval by moving it to the For Approval Done stage
        # This triggers the approval process: state becomes in_review
        self.ensure_one()
        stage = self._get_stage_by_name('For Approval Done')
        values = {'stage_id': stage.id} if stage else {}
        self.write(values)
        # The write() method will automatically set state to 'in_review' via trigger
        self.message_post(body="Ticket marked as done and sent for approval.")

    def action_approve(self):
        # Approve the ticket and record the approver
        # According to refined spec: state=approved, approved_by=current user, date_closed=today
        self.ensure_one()
        values = {
            'state': 'approved',
            'approved_by': self.env.user.id,
            'date_closed': fields.Date.context_today(self),
        }
        self.write(values)
        self.message_post(body=f"Ticket has been approved by {self.env.user.display_name}.")

    def action_refuse(self):
        # Open the refusal wizard so a manager can enter the rejection reason
        # After confirmation, state becomes 'refused' and stage moves to 'In Progress'
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
        # Reopen a refused ticket and move it back into the active pipeline
        # According to refined spec: move back to In Progress stage
        self.ensure_one()
        stage = self._get_stage_by_name('In Progress')
        if not stage:
            stage = self._get_stage_by_name('New')
        values = {
            'state': 'draft',
            'refused_reason': False,
            'approved_by': False,
            'date_closed': False,
        }
        if stage:
            values['stage_id'] = stage.id
        self.write(values)
        self.message_post(body="Ticket has been reopened and returned to the active pipeline.")

    def _check_refused_reason(self):
        # Ensure that refused tickets always include a refusal reason.
        for record in self:
            if record.state == 'refused' and not record.refused_reason:
                raise ValidationError('A reason is required when refusing a ticket.')

    @api.constrains('state', 'refused_reason')
    def _validate_refused_reason(self):
        self._check_refused_reason()

    def _notify_assigned_user(self, old_assigned_map):
        """Post a chatter notification when assignment changes."""
        for record in self:
            old_assigned_id = old_assigned_map.get(record.id)
            if record.assigned_to and old_assigned_id != record.assigned_to.id:
                record.message_post(body=f"Ticket assigned to {record.assigned_to.display_name}.")

    def write(self, vals):
        """
        Enhanced write() to enforce approval workflow logic:
        - When moving to is_done_stage, automatically set state='in_review'
        - When approving (state='approved'), set date_closed
        - Do NOT set date_closed on stage changes
        - Notify assigned user when assignment changes
        """
        # Track old assigned_to for notifications
        old_assigned_map = {record.id: record.assigned_to.id for record in self}

        # WORKFLOW RULE: If moving to is_done_stage, set state to 'in_review' (if not already approved/refused)
        if 'stage_id' in vals:
            stage = self.env['helpdesk.ticket.stage'].browse(vals['stage_id'])
            if stage and stage.is_done_stage:
                # Only change state to in_review if it's not already in a final state
                if 'state' not in vals:
                    vals['state'] = 'in_review'
                elif vals.get('state') not in ('approved', 'refused'):
                    vals['state'] = 'in_review'

        # APPROVAL RULE: When state becomes 'approved', set date_closed
        if vals.get('state') == 'approved' and not vals.get('date_closed'):
            vals['date_closed'] = fields.Date.context_today(self)

        # Perform the write
        result = super().write(vals)

        # POST-WRITE: Log when moved to done stage awaiting approval
        if 'stage_id' in vals:
            for record in self.filtered(lambda rec: rec.stage_id.is_done_stage and rec.state == 'in_review'):
                record.message_post(body='Ticket moved to done stage and is awaiting approval.')

        # POST-WRITE: Notify when assigned_to changes
        if 'assigned_to' in vals:
            self._notify_assigned_user(old_assigned_map)

        return result

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create new helpdesk tickets with proper initialization.
        
        Refined spec requirements:
        - state defaults to 'draft' (approval lifecycle)
        - stage_id defaults to 'New' (pipeline stage)
        - date_requested is set to creation time
        - name is assigned via sequence (TKT-XXXX format)
        """
        for vals in vals_list:
            # 1. ASSIGN SEQUENCE - Generate ticket reference (TKT-0001, TKT-0002, etc.)
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or 'New'
            
            # 2. SET DEFAULT STAGE - New tickets start in 'New' stage
            if not vals.get('stage_id'):
                stage = self.env['helpdesk.ticket.stage'].search([], order='sequence asc', limit=1)
                if stage:
                    vals['stage_id'] = stage.id
            
            # 3. SET APPROVAL STATE - New tickets are in 'draft' approval state
            if 'state' not in vals:
                vals['state'] = 'draft'
            
            # 4. SET REQUEST DATE - Record creation timestamp
            if not vals.get('date_requested'):
                vals['date_requested'] = fields.Datetime.now()

        # Create records with all fields properly initialized
        records = super().create(vals_list)
        
        # 5. POST CHATTER MESSAGE - Notify when ticket is assigned during creation
        for record, vals in zip(records, vals_list):
            if vals.get('assigned_to') and record.assigned_to:
                record.message_post(body=f"Ticket assigned to {record.assigned_to.display_name}.")
        
        return records


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    helpdesk_ticket_count = fields.Integer(
        string='Tickets Submitted',
        compute='_compute_helpdesk_ticket_counts',
    )
    helpdesk_assigned_ticket_count = fields.Integer(
        string='Tickets Assigned',
        compute='_compute_helpdesk_ticket_counts',
    )

    def _compute_helpdesk_ticket_counts(self):
        # Compute the number of tickets created by and assigned to the employee.
        self.helpdesk_ticket_count = 0
        self.helpdesk_assigned_ticket_count = 0

        if not self:
            return

        employee_data = self.env['helpdesk.ticket'].read_group(
            [('employee_id', 'in', self.ids)],
            ['employee_id'],
            ['employee_id'],
        )
        assigned_data = self.env['helpdesk.ticket'].read_group(
            [('assigned_to', 'in', self.mapped('user_id').ids)],
            ['assigned_to'],
            ['assigned_to'],
        )

        employee_count = {item['employee_id'][0]: item['employee_id_count'] for item in employee_data}
        assigned_count = {item['assigned_to'][0]: item['assigned_to_count'] for item in assigned_data}

        for employee in self:
            employee.helpdesk_ticket_count = employee_count.get(employee.id, 0)
            assigned_user_id = employee.user_id.id if employee.user_id else False
            employee.helpdesk_assigned_ticket_count = assigned_count.get(assigned_user_id, 0)

    def action_view_helpdesk_tickets(self):
        # Open a ticket list filtered to tickets created by this employee.
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form,calendar,pivot,graph',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_view_assigned_helpdesk_tickets(self):
        # Open a ticket list filtered to tickets assigned to this employee.
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assigned Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form,calendar,pivot,graph',
            'domain': [('assigned_to', '=', self.user_id.id)] if self.user_id else [('assigned_to', '=', False)],
            'context': {'default_assigned_to': self.user_id.id if self.user_id else False},
        }
