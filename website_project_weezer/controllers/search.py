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

import os
import base64

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from pprint import pprint


class search_controller(http.Controller):

    @http.route('/marketplace/search', type='http', auth="public", website=True)
    def search(self, **kw):
        """ display search page and first results """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        res_ids = mp_announcement_pool.search(cr, uid, [('type','=','want')], limit=4, context=context)
        res_ids += mp_announcement_pool.search(cr, uid, [('type','=','offer')], limit=4, context=context)
        res_data = mp_announcement_pool.browse(cr, uid, res_ids, context=context)
        
        for item in res_data:
            if item.type == 'want':
                result['wants'].append(item)
            else:
                result['offers'].append(item)

        return http.request.website.render('website_project_weezer.mp_search', {
            'result': result,
        })

    @http.route(['/marketplace/search/load_more'], type='http', auth="public", methods=['GET'], website=True)
    def load_more(self, **kw):
        """ display results after load more signal """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        if kw.get('load_wants'):
            res_ids = mp_announcement_pool.search(cr, uid, [('type','=','want')], limit=4, context=context)
        else:
            res_ids = mp_announcement_pool.search(cr, uid, [('type','=','offer')], limit=4, context=context)
        res_data = mp_announcement_pool.browse(cr, uid, res_ids, context=context)

        for item in res_data:
            if item.type == 'want':
                result['wants'].append(item)
            else:
                result['offers'].append(item)

        if kw.get('load_wants'):
            return request.render('website_project_weezer.mp_search_wants', {'result': result})
        else:
            return request.render('website_project_weezer.mp_search_offers', {'result': result})


