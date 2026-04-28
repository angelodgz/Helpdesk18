"""Main Helpdesk Ticket model with full workflow, approval and smart buttons."""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date_requested desc, id desc'

    # ── Core fields ───────────────────────────────────────────────────────────

    name = fields.Char(
        string='Ticket Reference',
        readonly=True,
        default='New',
        copy=False,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Requesting Employee',
        required=True,
        tracking=True,
    )
    category = fields.Selection([
        ('it',         'IT Support'),
        ('hr',         'HR Request'),
        ('facilities', 'Facilities'),
        ('finance',    'Finance'),
        ('general',    'General'),
    ], string='Category', default='general', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical'),
    ], string='Priority', default='1', tracking=True)

    description = fields.Text(string='Description')

    stage_id = fields.Many2one(
        'helpdesk.ticket.stage',
        string='Stage',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self.env['helpdesk.ticket.stage'].search(
            [], order='sequence asc', limit=1
        ),
    )

    # Approval state — mirrors stage transitions (spec field: Approval_state)
    state = fields.Selection([
        ('draft',     'Draft'),
        ('in_review', 'Waiting Approval'),
        ('approved',  'Approved'),
        ('refused',   'Refused'),
    ], string='Approval State', default='draft', tracking=True)

    # Related booleans stored for domain / decoration use
    is_done_stage = fields.Boolean(
        related='stage_id.is_done_stage', store=True, string='Is Done Stage'
    )
    is_cancelled_stage = fields.Boolean(
        related='stage_id.is_cancelled_stage', store=True, string='Is Cancelled'
    )

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags')

    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)

    date_requested = fields.Datetime(
        string='Date Requested', default=fields.Datetime.now, tracking=True
    )
    date_closed = fields.Date(string='Date Closed')

    approved_by = fields.Many2one(
        'res.users', string='Approved By', readonly=True, tracking=True
    )
    refused_reason = fields.Text(string='Refusal Reason')

    color = fields.Integer(string='Color Index')

    # ── Category-specific fields: IT Support ──────────────────────────────────

    issue_type = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('network',  'Network'),
        ('access',   'Access / Permissions'),
    ], string='Issue Type')

    urgency = fields.Selection([
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ], string='Urgency Level')

    device_tag = fields.Char(string='Device Tag / Serial No.')
    affected_system = fields.Char(string='Affected System')

    # ── Category-specific fields: HR Request ──────────────────────────────────

    request_type = fields.Selection([
        ('leave',       'Leave'),
        ('payroll',     'Payroll'),
        ('certificate', 'Employment Certificate'),
        ('other',       'Other'),
    ], string='Request Type')

    effective_date = fields.Date(string='Effective Date')
    hr_notes = fields.Text(string='HR Notes')

    # ── Category-specific fields: Facilities ──────────────────────────────────

    location = fields.Char(string='Location / Area')

    facility_type = fields.Selection([
        ('repair',        'Repair'),
        ('maintenance',   'Maintenance'),
        ('installation',  'Installation'),
        ('cleaning',      'Cleaning'),
    ], string='Facility Type')

    estimated_cost = fields.Float(string='Estimated Cost', digits=(16, 2))

    # ── Category-specific fields: Finance ────────────────────────────────────

    amount = fields.Float(string='Amount', digits=(16, 2))

    payment_mode = fields.Selection([
        ('cash',  'Cash'),
        ('bank',  'Bank Transfer'),
        ('check', 'Check'),
        ('gcash', 'GCash'),
    ], string='Payment Mode')

    expected_liquidation_date = fields.Date(string='Expected Liquidation Date')

    # ── Kanban group expansion ────────────────────────────────────────────────

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always show all pipeline stages in Kanban, even if empty."""
        return stages.search([], order='sequence asc')

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_stage(self, xml_id):
        """Return a stage record by its XML id, or False."""
        return self.env.ref(f'helpdesk_ticket.{xml_id}', raise_if_not_found=False)

    # ── Action buttons ────────────────────────────────────────────────────────

    def action_mark_done(self):
        """
        Employee/Agent clicks 'Submit for Approval'.
        Moves ticket to the 'For Approval - Done' stage → triggers in_review.
        """
        self.ensure_one()
        stage = self._get_stage('stage_for_approval')
        if not stage:
            raise ValidationError(
                "The 'For Approval - Done' stage is missing. "
                "Please check your stage configuration."
            )
        self.write({'stage_id': stage.id})
        self.message_post(
            body=(
                f"<b>Submitted for approval</b> by {self.env.user.name}. "
                f"Waiting for Manager review."
            )
        )

    def action_approve(self):
        """Manager approves the ticket → moves to Done, records approver."""
        self.ensure_one()
        stage = self._get_stage('stage_done')
        if not stage:
            raise ValidationError("The 'Done' stage is not configured.")
        self.write({
            'stage_id':   stage.id,
            'approved_by': self.env.user.id,
        })
        self.message_post(
            body=(
                f"✅ Ticket <b>approved</b> by <b>{self.env.user.name}</b>. "
                f"Ticket is now closed."
            )
        )

    def action_refuse(self):
        """Manager clicks Refuse → opens the reason wizard as a popup."""
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      'Refuse Reason',
            'res_model': 'helpdesk.refuse.wizard',
            'view_mode': 'form',
            'target':    'new',
            'context':   {'default_ticket_id': self.id},
        }

    def action_apply_refusal(self, reason):
        """
        Called by the refusal wizard after the manager confirms.
        Moves ticket to 'Approval Rejected' and saves the reason.
        """
        self.ensure_one()
        stage = self._get_stage('stage_rejected')
        if not stage:
            raise ValidationError("The 'Approval Rejected' stage is not configured.")
        self.write({
            'stage_id':      stage.id,
            'refused_reason': reason,
        })
        self.message_post(
            body=(
                f"❌ Ticket <b>refused</b> by <b>{self.env.user.name}</b>.<br/>"
                f"<b>Reason:</b> {reason}"
            )
        )

    def action_reopen(self):
        """Reopen a refused ticket back to In Progress."""
        self.ensure_one()
        stage = (
            self._get_stage('stage_in_progress') or self._get_stage('stage_new')
        )
        self.write({
            'stage_id':      stage.id if stage else False,
            'refused_reason': False,
            'approved_by':    False,
            'date_closed':    False,
        })
        self.message_post(
            body=(
                f"🔄 Ticket <b>reopened</b> by {self.env.user.name} "
                f"and moved back to In Progress."
            )
        )

    def action_cancel(self):
        """Cancel the ticket directly."""
        self.ensure_one()
        stage = self._get_stage('stage_cancelled')
        if not stage:
            raise ValidationError("The 'Cancelled' stage is not configured.")
        self.write({'stage_id': stage.id})
        self.message_post(body=f"🚫 Ticket <b>cancelled</b> by {self.env.user.name}.")

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.constrains('state', 'refused_reason')
    def _validate_refused_reason(self):
        for record in self:
            if record.state == 'refused' and not record.refused_reason:
                raise ValidationError(
                    "A refusal reason is required when a ticket is refused."
                )

    # ── ORM overrides ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-assign TKT-XXXX sequence
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('helpdesk.ticket') or 'New'
                )
            # Ensure timestamps
            if not vals.get('date_requested'):
                vals['date_requested'] = fields.Datetime.now()
            vals.setdefault('state', 'draft')

        records = super().create(vals_list)

        for record, vals in zip(records, vals_list):
            if vals.get('assigned_to') and record.assigned_to:
                record.message_post(
                    body=(
                        f"📋 Ticket created and assigned to "
                        f"<b>{record.assigned_to.display_name}</b>."
                    ),
                    partner_ids=[record.assigned_to.partner_id.id],
                )
            else:
                record.message_post(body="📋 Ticket created.")

        return records

    def write(self, vals):
        # Capture current assignment before the write
        old_assigned_map = {r.id: r.assigned_to.id for r in self}

        # ── Auto-manage approval_state and date_closed on stage change ────────
        if 'stage_id' in vals:
            stage = self.env['helpdesk.ticket.stage'].browse(vals['stage_id'])

            approval_stage = self._get_stage('stage_for_approval')
            rejected_stage = self._get_stage('stage_rejected')

            if approval_stage and stage == approval_stage:
                # "For Approval - Done" stage → trigger waiting approval
                vals.setdefault('state', 'in_review')

            elif stage.is_done_stage:
                # Done stage (is_done_stage = True) → approved + auto date_closed
                vals.setdefault('state', 'approved')
                vals.setdefault('date_closed', fields.Date.context_today(self))

            elif rejected_stage and stage == rejected_stage:
                # Approval Rejected stage → refused
                vals.setdefault('state', 'refused')

            else:
                # New, In Progress, Cancelled, or any other → reset to draft
                vals.setdefault('state', 'draft')

        result = super().write(vals)

        # ── Notify newly assigned agent ───────────────────────────────────────
        if 'assigned_to' in vals:
            self._notify_assigned_user(old_assigned_map)

        return result

    def _notify_assigned_user(self, old_assigned_map):
        """Post a chatter message and notify the newly assigned agent."""
        for record in self:
            old_user_id = old_assigned_map.get(record.id)
            if record.assigned_to and old_user_id != record.assigned_to.id:
                record.message_post(
                    body=(
                        f"👤 Ticket assigned to "
                        f"<b>{record.assigned_to.display_name}</b>."
                    ),
                    partner_ids=[record.assigned_to.partner_id.id],
                )


# ── HR Employee extension ─────────────────────────────────────────────────────

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
        Ticket = self.env['helpdesk.ticket']

        # Tickets created by each employee
        created_data = Ticket.read_group(
            domain=[('employee_id', 'in', self.ids)],
            fields=['employee_id'],
            groupby=['employee_id'],
        )
        created_map = {
            d['employee_id'][0]: d['employee_id_count'] for d in created_data
        }

        # Tickets assigned to each employee's linked user
        user_ids = self.mapped('user_id').ids
        assigned_data = Ticket.read_group(
            domain=[('assigned_to', 'in', user_ids)],
            fields=['assigned_to'],
            groupby=['assigned_to'],
        )
        assigned_map = {
            d['assigned_to'][0]: d['assigned_to_count'] for d in assigned_data
        }

        for emp in self:
            emp.helpdesk_ticket_count = created_map.get(emp.id, 0)
            user_id = emp.user_id.id if emp.user_id else False
            emp.helpdesk_assigned_ticket_count = assigned_map.get(user_id, 0)

    def action_view_helpdesk_tickets(self):
        """Smart button: open tickets submitted by this employee."""
        return {
            'type':      'ir.actions.act_window',
            'name':      f'Tickets by {self.name}',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,list,form',
            'domain':    [('employee_id', '=', self.id)],
            'context':   {'default_employee_id': self.id},
        }

    def action_view_assigned_helpdesk_tickets(self):
        """Bonus smart button: open tickets assigned to this employee."""
        domain = (
            [('assigned_to', '=', self.user_id.id)]
            if self.user_id
            else [('assigned_to', '=', False)]
        )
        return {
            'type':      'ir.actions.act_window',
            'name':      f'Tickets Assigned to {self.name}',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,list,form',
            'domain':    domain,
        }
