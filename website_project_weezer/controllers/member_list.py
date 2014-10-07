# -*- coding: utf-8 -*-
#
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
#

import logging

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers

from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class member_list_controller(http.Controller):

    PAGE_LIMIT = 8

    @http.route(['/marketplace/member_list/<int:page>', 
                 '/marketplace/member_list'], type='http', auth="public", website=True)
    def route_member_list(self, page=1):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_pool = registry.get('res.partner')
        count = len(partner_pool.search(cr, uid, [], context=context))
        member_list = partner_pool.search(cr, uid, [], limit=self.PAGE_LIMIT, 
            offset=(page-1)*self.PAGE_LIMIT, context=context)
        member_list = partner_pool.browse(cr, uid, member_list, context = context)
        member_list = [member_list] if isinstance(member_list, (int, long)) else member_list
        member_list = [rec for rec in member_list]

        return http.request.website.render('website_project_weezer.member_list_view', {
                'member_list': member_list,
                'page': page,
                'page_count': count/self.PAGE_LIMIT + (1 if count%self.PAGE_LIMIT else 0),
                'next_url': '/marketplace/member_list%s' % (('/' + str(page+1)) if page*self.PAGE_LIMIT < count else ''),
                'prev_url': '/marketplace/member_list%s' % (('/' + str(page-1)) if page > 1 else ''),
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
