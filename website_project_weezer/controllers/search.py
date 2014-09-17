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
from datetime import datetime

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class search_controller(http.Controller):

    QUERY_LIMIT = 4
    SEARCH_PARAMS = ['type', 'name', 'category', 'city', 'date_from', 'date_to', 'from_who',
        'qty_from', 'qty_to', 'cur_from', 'cur_to']

    def _get_date_format(self, cr, uid, context):
        lang = context.get('lang')
        lang_params = {}
        if lang:
            res_lang = request.registry.get('res.lang')
            ids = res_lang.search(cr, uid, [('code', '=', lang)])
            if ids:
                lang_params = res_lang.read(cr, uid, ids[0], ['date_format'])
                return lang_params['date_format']
        return DEFAULT_SERVER_DATE_FORMAT

    def _build_query(self, data, limit=QUERY_LIMIT, page=0, return_count=False):
        offset = page*limit
        params = {}
        def _build_sql(ttype, pick_params=False):
            if return_count:
                sql = 'SELECT COUNT(a.id) '
            else:
                sql = 'SELECT a.id '
            sql += 'FROM marketplace_announcement a '\
            'LEFT JOIN res_partner p on p.id = a.partner_id '\
            'WHERE 1=1 '
            
            if ttype:
                sql += 'AND a.type = \'%s\' ' % ('want' if ttype == 'to_offer' else 'offer')
            if data.get('name'): 
                sql += 'AND a.name like %(name)s '
                params.update({'name': '%'+data.get('name')+'%'})
            if data.get('category'):
                sql += 'AND a.category_id = %(category)s '
                params.update({'category': data.get('category')})
            if data.get('city'):
                sql += 'AND a.city like %(city)s '
                params.update({'city': '%'+data.get('city')+'%'})
            if data.get('date_from'): 
                date_from = datetime.strptime(data.get('date_from'), date_format)
                sql += 'AND a.expiration_date >= %(date_from)s '
                params.update({'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            if data.get('date_to'):
                date_to = datetime.strptime(data.get('date_to'), date_format)
                sql += 'AND a.expiration_date <= %(date_to)s '
                params.update({'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            if data.get('from_who'):
                sql += 'AND p.name like %(partner_name)s '
                params.update({'partner_name': '%'+data.get('from_who')+'%'})
            if data.get('price_from') and data.get('cur_from'):
                sql += 'AND EXISTS('\
                    'SELECT 1 FROM account_centralbank_currency_line cl '\
                    'WHERE cl.announcement_id = a.id AND cl.currency_id = %(cur_from)s '\
                    'AND cl.price_unit >= %(price_from)s) '
                params.update({'cur_from': data.get('cur_from'), 'price_from': data.get('price_from')})
            if data.get('price_to') and data.get('cur_to'):
                sql += 'AND EXISTS('\
                    'SELECT 1 FROM account_centralbank_currency_line cl '\
                    'WHERE cl.announcement_id = a.id AND cl.currency_id = %(cur_to)s '\
                    'AND cl.price_unit <= %(price_to)s) '
                params.update({'cur_to': data.get('cur_to'), 'price_to': data.get('price_to')})
            if limit and not return_count:
                sql += 'LIMIT %(limit)s '
                params.update({'limit': limit})
            if offset and not return_count:
                sql += 'OFFSET %(offset)s '
                params.update({'offset': offset})
            return sql

        if not data.get('type') or data.get('type') == 'to_find':
            return '(%s)' % _build_sql('to_offer', True) + 'UNION ' + '(%s)' % _build_sql('to_get'), params
        else:
            return _build_sql(data.get('type')), params

    def _get_url(self, type, offset, params):
        url_pairs = [(k, v) for k,v in params.iteritems() if k in self.SEARCH_PARAMS]
        url_pairs.append(('page', str(offset) if type == 'prev' else str(offset+1)))
        url = '/marketplace/search?' + '&'.join(['='.join(x) for x in url_pairs])
        return url

    def format_text(self, text):
        text = text[0:300]
        dot_pos = text.rfind('.')
        if dot_pos:
            text = text[0:dot_pos]
        else:
            text = text[0:text.rfind(' ')]
        return text + ' '*(300 - len(text))

    @http.route('/marketplace/search', type='http', auth="public", website=True)
    def search(self, **kw):
        """ display search page and first results """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        date_format = self._get_date_format(cr, uid, context)
        params = dict([(k,v) for k,v in kw.iteritems() if k in self.SEARCH_PARAMS])
        sql = self._build_query(params, kw.get('limit',self.QUERY_LIMIT), int(kw.get('page','1'))-1)
        cr.execute(sql[0], sql[1] or ())
        res_ids = [row[0] for row in cr.fetchall()]
        res_data = mp_announcement_pool.browse(cr, uid, res_ids, context=context)

        #select count both of wants and offers
        count_sql = self._build_query(params, False, False, True)
        cr.execute(count_sql[0], count_sql[1] or ())
        counts = cr.fetchall()
        if len(counts) > 1:
            count = max(counts[0][0], counts[1][0])
        else:
            count = counts[0][0]

        for item in res_data:
            if item.type == 'want':
                result['wants'].append(item)
            else:
                result['offers'].append(item)
        return http.request.website.render('website_project_weezer.mp_search', {
            'result': result,
            'page': int(kw.get('page', '1')),
            'page_count': count/self.QUERY_LIMIT + (1 if count%self.QUERY_LIMIT else 0),
            'next_url': self._get_url('next', int(kw.get('page', '1')), params),
            'prev_url': self._get_url('prev', int(kw.get('page', '1'))-1, params),
            'format_text': self.format_text
        })

    @http.route(['/marketplace/search/load_more'], type='http', auth="public", methods=['GET'], website=True)
    def load_more(self, **kw):
        """ display results after load more signal """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        date_format = self._get_date_format(cr, uid, context)
        sql = self._build_query(dict([(k,v) for k,v in kw.iteritems() if k in self.SEARCH_PARAMS]), 
            kw.get('limit',self.QUERY_LIMIT), kw.get('offset'))
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


