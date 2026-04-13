from odoo import models, fields # pyright: ignore[reportMissingImports]

class HelpdeskTicketStage(models.Model):
    _name = 'helpdesk.ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1)
    is_done_stage = fields.Boolean()
    is_cancelled_stage = fields.Boolean()
    fold = fields.Boolean()
    description = fields.Text()
