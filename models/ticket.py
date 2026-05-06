from odoo import api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_requested desc, id desc'

    # ─────────────────────────────────────────────────────────────────────────
    # Core Fields
    # ─────────────────────────────────────────────────────────────────────────

    name = fields.Char(
        string='Ticket Reference',
        default='New',
        readonly=True,
        copy=False,
        index=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Submitted By',
        required=True,
        tracking=True,
        default=lambda self: self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1
        ),
    )
    category = fields.Selection(
        selection=[
            ('it_support', 'IT Support'),
            ('hr_request', 'HR Request'),
            ('facilities', 'Facilities'),
            ('finance', 'Finance'),
            ('general', 'General'),
        ],
        string='Category',
        required=True,
        tracking=True,
        index=True,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Critical'),
        ],
        string='Priority',
        default='1',
        tracking=True,
        index=True,
    )
    description = fields.Text(string='Description')
    stage_id = fields.Many2one(
        'helpdesk.ticket.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        tracking=True,
        copy=False,
        index=True,
        default=lambda self: self._default_stage_id(),
    )
    approval_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_review', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        string='Approval Status',
        default='draft',
        tracking=True,
        copy=False,
        index=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_attachment_rel',
        'ticket_id',
        'attachment_id',
        string='Attachments',
    )
    date_requested = fields.Datetime(
        string='Date Submitted',
        default=fields.Datetime.now,
        readonly=True,
        copy=False,
    )
    date_closed = fields.Date(
        string='Date Closed',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    refused_reason = fields.Text(
        string='Refusal Reason',
        readonly=True,
        copy=False,
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_ticket_tag_rel',
        'ticket_id',
        'tag_id',
        string='Tags',
    )
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        tracking=True,
        index=True,
        help='The partner (contact) who submitted or is associated with this ticket.',
        default=lambda self: self.env.user.partner_id,
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Support Team',
        tracking=True,
        index=True,
        help='The support team responsible for handling this ticket.',
    )
    color = fields.Integer(string='Color Index', default=0)

    # ─────────────────────────────────────────────────────────────────────────
    # IT Support Category Fields
    # ─────────────────────────────────────────────────────────────────────────

    issue_type = fields.Selection(
        selection=[
            ('hardware', 'Hardware'),
            ('software', 'Software'),
            ('network', 'Network / Connectivity'),
            ('account', 'Account Access / Credentials'),
            ('email', 'Email / Communication Tools'),
            ('other', 'Other'),
        ],
        string='Issue Type',
    )
    urgency = fields.Selection(
        selection=[
            ('low', 'Low — Can wait'),
            ('medium', 'Medium — Affects work but has workaround'),
            ('high', 'High — Significant impact on operations'),
            ('critical', 'Critical — Complete stoppage'),
        ],
        string='Urgency Level',
    )
    device_tag = fields.Char(string='Device Tag / Asset No.')
    affected_system = fields.Char(string='Affected System / Application')

    # ─────────────────────────────────────────────────────────────────────────
    # HR Request Category Fields
    # ─────────────────────────────────────────────────────────────────────────

    request_type = fields.Selection(
        selection=[
            ('leave', 'Leave Request'),
            ('payroll', 'Payroll Concern'),
            ('benefits', 'Benefits Inquiry'),
            ('clearance', 'Clearance / Exit'),
            ('certificate', 'Employment Certificate'),
            ('other', 'Other'),
        ],
        string='Request Type',
    )
    effective_date = fields.Date(string='Effective Date')
    hr_notes = fields.Text(string='Additional HR Notes')

    # ─────────────────────────────────────────────────────────────────────────
    # Facilities Category Fields
    # ─────────────────────────────────────────────────────────────────────────

    location = fields.Char(string='Location / Area')
    facility_type = fields.Selection(
        selection=[
            ('office', 'Office / Workspace'),
            ('equipment', 'Equipment / Furniture'),
            ('utilities', 'Utilities (Electricity, Water, A/C)'),
            ('maintenance', 'Preventive / Corrective Maintenance'),
            ('sanitation', 'Sanitation / Cleaning'),
            ('other', 'Other'),
        ],
        string='Facility Type',
    )
    estimated_cost = fields.Float(string='Estimated Cost (PHP)', digits=(12, 2))

    # ─────────────────────────────────────────────────────────────────────────
    # Finance Category Fields
    # ─────────────────────────────────────────────────────────────────────────

    amount = fields.Float(string='Amount (PHP)', digits=(12, 2))
    payment_mode = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('bank_transfer', 'Bank Transfer'),
            ('gcash', 'GCash / E-Wallet'),
            ('other', 'Other'),
        ],
        string='Payment Mode',
    )
    expected_liquidation_date = fields.Date(string='Expected Liquidation Date')

    # ─────────────────────────────────────────────────────────────────────────
    # Computed / Relational Helpers
    # ─────────────────────────────────────────────────────────────────────────

    is_done_stage = fields.Boolean(
        related='stage_id.is_done_stage',
        string='Is Done Stage',
        store=False,
    )
    is_cancelled_stage = fields.Boolean(
        related='stage_id.is_cancelled_stage',
        string='Is Cancelled Stage',
        store=False,
    )
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count',
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Defaults & Group Expand
    # ─────────────────────────────────────────────────────────────────────────

    def _default_stage_id(self):
        """Return the first stage (lowest sequence) as the default."""
        return self.env['helpdesk.ticket.stage'].search(
            [], order='sequence asc', limit=1
        )

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.model
    def _read_group_stage_ids(self, stages, domain, **kwargs):
        """Always show all stages in Kanban, even if empty."""
        return stages.search([], order='sequence asc')

    # ─────────────────────────────────────────────────────────────────────────
    # ORM Overrides
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('helpdesk.ticket') or 'New'
                )
            if not vals.get('date_requested'):
                vals['date_requested'] = fields.Datetime.now()
            # Auto-populate partner_id from the submitting employee if not set
            if not vals.get('partner_id') and vals.get('employee_id'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.user_id and employee.user_id.partner_id:
                    vals['partner_id'] = employee.user_id.partner_id.id
            elif not vals.get('partner_id'):
                vals['partner_id'] = self.env.user.partner_id.id
        records = super().create(vals_list)
        for record in records:
            if record.assigned_to:
                record._notify_assigned()
        return records

    def write(self, vals):
        # Auto-fill date_closed when moved to a terminal stage
        if 'stage_id' in vals:
            new_stage = self.env['helpdesk.ticket.stage'].browse(vals['stage_id'])
            if new_stage.is_done_stage or new_stage.is_cancelled_stage:
                vals.setdefault('date_closed', fields.Date.today())
            else:
                vals['date_closed'] = False

            # Auto-trigger review when dragged into a done stage from draft.
            # Never overwrite an already-approved or already-refused state,
            # and never overwrite an approval_state being explicitly set in vals.
            if new_stage.is_done_stage and 'approval_state' not in vals:
                for record in self:
                    if record.approval_state == 'draft':
                        vals['approval_state'] = 'in_review'
                        break  # all records in this multi-write share the same vals dict

        # Notify newly assigned agents
        if 'assigned_to' in vals and vals['assigned_to']:
            result = super().write(vals)
            for record in self:
                record._notify_assigned()
            return result

        return super().write(vals)

    # ─────────────────────────────────────────────────────────────────────────
    # Business Logic / Button Actions
    # ─────────────────────────────────────────────────────────────────────────

    def action_mark_as_done(self):
        """Move ticket to the Done stage and submit for manager approval."""
        self.ensure_one()
        done_stage = self.env['helpdesk.ticket.stage'].search(
            [('is_done_stage', '=', True)], order='sequence asc', limit=1
        )
        if not done_stage:
            raise UserError(
                'No stage is marked as "Done Stage". '
                'Please configure a Done stage under Helpdesk → Configuration → Stages.'
            )
        self.write({
            'stage_id': done_stage.id,
            'approval_state': 'in_review',
            'date_closed': fields.Date.today(),
        })
        self.message_post(
            body=(
                f'<b>Submitted for Approval</b><br/>'
                f'Ticket <b>{self.name}</b> has been moved to <b>{done_stage.name}</b> '
                f'and is now awaiting manager approval.'
            )
        )

    def action_approve(self):
        """Approve the ticket. Only Helpdesk Managers can call this."""
        self.ensure_one()
        if self.approval_state != 'in_review':
            raise UserError('Only tickets waiting for approval can be approved.')
        self.write({
            'approval_state': 'approved',
            'approved_by': self.env.uid,
        })
        # Notify the ticket submitter
        partner_ids = []
        if self.employee_id.user_id and self.employee_id.user_id.partner_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)
        self.message_post(
            body=(
                f'<b>Ticket Approved ✔</b><br/>'
                f'Approved by <b>{self.env.user.name}</b>. '
                f'This ticket is now officially closed.'
            ),
            partner_ids=partner_ids,
        )

    def action_open_refuse_wizard(self):
        """Open the refuse reason wizard. Only Helpdesk Managers can call this."""
        self.ensure_one()
        if self.approval_state != 'in_review':
            raise UserError('Only tickets waiting for approval can be refused.')
        return {
            'name': 'Refuse Ticket',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id},
        }

    def action_reopen(self):
        """Reopen a refused ticket and move it back to In Progress."""
        self.ensure_one()
        in_progress_stage = self.env['helpdesk.ticket.stage'].search(
            [('name', 'ilike', 'In Progress')], order='sequence asc', limit=1
        )
        if not in_progress_stage:
            # Fallback: second stage by sequence
            in_progress_stage = self.env['helpdesk.ticket.stage'].search(
                [], order='sequence asc', limit=2
            )
            in_progress_stage = in_progress_stage[-1] if len(in_progress_stage) > 1 else in_progress_stage

        self.write({
            'stage_id': in_progress_stage.id,
            'approval_state': 'draft',
            'date_closed': False,
            'refused_reason': False,
        })
        self.message_post(
            body=(
                f'<b>Ticket Reopened</b><br/>'
                f'Reopened by <b>{self.env.user.name}</b>. '
                f'Ticket moved back to <b>{in_progress_stage.name}</b>.'
            )
        )

    def action_open_attachments_view(self):
        """Open attachments linked to this ticket."""
        self.ensure_one()
        return {
            'name': 'Attachments',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
        }

    def action_cancel(self):
        """Cancel the ticket."""
        self.ensure_one()
        cancelled_stage = self.env['helpdesk.ticket.stage'].search(
            [('is_cancelled_stage', '=', True)], order='sequence asc', limit=1
        )
        if not cancelled_stage:
            raise UserError(
                'No stage is marked as "Cancelled Stage". '
                'Please configure one under Helpdesk → Configuration → Stages.'
            )
        self.write({
            'stage_id': cancelled_stage.id,
            'approval_state': 'draft',
            'date_closed': fields.Date.today(),
        })
        self.message_post(
            body=(
                f'<b>Ticket Cancelled</b><br/>'
                f'Cancelled by <b>{self.env.user.name}</b>.'
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Onchange Helpers
    # ─────────────────────────────────────────────────────────────────────────

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Auto-fill date_closed when stage is terminal."""
        if self.stage_id.is_done_stage or self.stage_id.is_cancelled_stage:
            self.date_closed = fields.Date.today()
        else:
            self.date_closed = False

    @api.onchange('assigned_to')
    def _onchange_assigned_to(self):
        """Warn if the assigned user has no helpdesk group membership."""
        pass  # Extend if needed

    # ─────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _notify_assigned(self):
        """Post a chatter message notifying the newly assigned agent."""
        self.ensure_one()
        if not self.assigned_to:
            return
        partner = self.assigned_to.partner_id
        self.message_post(
            body=(
                f'<b>Ticket Assigned</b><br/>'
                f'This ticket has been assigned to <b>{self.assigned_to.name}</b>.'
            ),
            partner_ids=[partner.id] if partner else [],
        )
