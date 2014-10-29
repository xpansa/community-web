# -*- coding: utf-8 -*-
##############################################################################
#
#    Website Marketplace
#    Copyright (C) 2014 Xpansa Group (<http://xpansa.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime

from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class marketplace_announcement(osv.osv):

    _inherit = "marketplace.announcement"

    _columns = {
        'emergency': fields.boolean('Emergency'),
        'link': fields.char('Link', size=140),
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
    }


class account_invoice_line(osv.Model):
    _inherit='account.invoice.line'

    def write(self, cr, uid, ids, vals, context=None):
        """Overrides orm write method
        """
        member_line_obj = self.pool.get('membership.membership_line')
        res = super(account_invoice_line, self).write(cr, uid, ids, vals, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.invoice_id.type == 'out_invoice':
                ml_ids = member_line_obj.search(cr, uid, [('account_invoice_line', '=', line.id)], context=context)
                if line.product_id and line.product_id.membership:
                    # Product line has changed to a membership product
                    current_date = datetime.now()
                    date_from = datetime.strptime(line.product_id.membership_date_from, 
                                                  DEFAULT_SERVER_DATE_FORMAT)
                    date_to = datetime.strptime(line.product_id.membership_date_to, 
                                                  DEFAULT_SERVER_DATE_FORMAT)
                    if line.invoice_id.date_invoice \
                        and line.invoice_id.date_invoice > date_from \
                        and line.invoice_id.date_invoice < date_to:
                        date_from = datetime.strptime(line.invoice_id.date_invoice, 
                                                      DEFAULT_SERVER_DATE_FORMAT)
                    if not ml_ids:
                        member_line_obj.create(cr, uid, {
                            'partner': line.invoice_id.partner_id.id,
                            'membership_id': line.product_id.id,
                            'member_price': line.price_unit,
                            'date': time.strftime('%Y-%m-%d'),
                            'date_from': current_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            'date_to': (current_date + (date_to - date_from)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                            'account_invoice_line': line.id,
                        }, context=context)
                    else:
                        member_line_obj.write(cr, uid, ml_ids, {
                            'date_from': current_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            'date_to': (current_date + (date_to - date_from)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                        }, context=context)
                if line.product_id and not line.product_id.membership and ml_ids:
                    # Product line has changed to a non membership product
                    member_line_obj.unlink(cr, uid, ml_ids, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        """Remove Membership Line Record for Account Invoice Line
        """
        member_line_obj = self.pool.get('membership.membership_line')
        for id in ids:
            ml_ids = member_line_obj.search(cr, uid, [('account_invoice_line', '=', id)], context=context)
            member_line_obj.unlink(cr, uid, ml_ids, context=context)
        return super(account_invoice_line, self).unlink(cr, uid, ids, context=context)

    def create(self, cr, uid, vals, context=None):
        """Overrides orm create method
        """
        member_line_obj = self.pool.get('membership.membership_line')
        result = super(account_invoice_line, self).create(cr, uid, vals, context=context)
        line = self.browse(cr, uid, result, context=context)
        if line.invoice_id.type == 'out_invoice':
            ml_ids = member_line_obj.search(cr, uid, [('account_invoice_line', '=', line.id)], context=context)
            if line.product_id and line.product_id.membership:
                # Product line is a membership product
                current_date = datetime.now()
                date_from = datetime.strptime(line.product_id.membership_date_from, 
                                              DEFAULT_SERVER_DATE_FORMAT)
                date_to = datetime.strptime(line.product_id.membership_date_to, 
                                            DEFAULT_SERVER_DATE_FORMAT)
                if line.invoice_id.date_invoice \
                    and line.invoice_id.date_invoice > date_from \
                    and line.invoice_id.date_invoice < date_to:
                    date_from = datetime.strptime(line.invoice_id.date_invoice, 
                                                  DEFAULT_SERVER_DATE_FORMAT)
                if not ml_ids:
                    member_line_obj.create(cr, uid, {
                        'partner': line.invoice_id.partner_id and line.invoice_id.partner_id.id or False,
                        'membership_id': line.product_id.id,
                        'member_price': line.price_unit,
                        'date': time.strftime('%Y-%m-%d'),
                        'date_from': current_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'date_to': (current_date + (date_to - date_from)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'account_invoice_line': line.id,
                    }, context=context)
                else:
                    member_line_obj.write(cr, uid, ml_ids, {
                        'date_from': current_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'date_to': (current_date + (date_to - date_from)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    }, context=context)
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
