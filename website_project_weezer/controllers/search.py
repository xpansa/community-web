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

    QUERY_LIMIT = 4

    def _build_query(self, type, name, category, city, limit=QUERY_LIMIT, offset=0):
        params = {}

        def _build_sql(ttype, pick_params=False):
            sql = 'SELECT id '\
            'FROM marketplace_announcement a '\
            'WHERE 1=1 '
            if ttype:
                sql += 'AND a.type = \'%s\' ' % ('want' if ttype == 'to_offer' else 'offer')
            if name: 
                sql += 'AND a.name like %(name)s '
                params.update({'name': '%'+name+'%'})
            if category:
                sql += 'AND a.category_id = %(category)s '
                params.update({'category': category_id})
            if city:
                sql += 'AND a.city like %(city)s '
                params.update({'city': '%'+city+'%'})
            if limit:
                sql += 'LIMIT %(limit)s '
                params.update({'limit': limit})
            if offset:
                sql += 'OFFSET %(offset)s '
                params.update({'offset': offset})
            return sql

        if not type or type == 'to_find':
            return '(%s)' % _build_sql('to_offer', True) + 'UNION ' + '(%s)' % _build_sql('to_get'), params
        else:
            return _build_sql(type), params


    @http.route('/marketplace/search', type='http', auth="public", website=True)
    def search(self, **kw):
        """ display search page and first results """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        sql = self._build_query(kw.get('type'), kw.get('name'), kw.get('category_id'), 
            kw.get('city'), kw.get('limit',self.QUERY_LIMIT), kw.get('offset'))
        cr.execute(sql[0], sql[1] or ())
        res_ids = [row[0] for row in cr.fetchall()]
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
        sql = self._build_query(kw.get('type'), kw.get('name'), kw.get('category_id'), 
            kw.get('city'), kw.get('limit',self.QUERY_LIMIT), kw.get('offset'))
        cr.execute(sql[0], sql[1] or ())
        res_ids = [row[0] for row in cr.fetchall()]
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


