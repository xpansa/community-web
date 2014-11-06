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

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime
from main import get_date_format, format_text

class search_controller(http.Controller):

    QUERY_LIMIT = 4
    SEARCH_PARAMS = [
        'type', 'name', 'category', 'city', 'date_from', 
        'date_to', 'from_who', 'qty_from', 'qty_to', 'currency'
    ]

    def _build_query(self, data, date_format, limit=QUERY_LIMIT, page=0, return_count=False):
        """ Returns SQL query and params that should be applied 

        :param dict data: POST data from forms
        :param str date_format: pattern for parsing dates
        :param int limit: LIMIT in SQL query
        :param int page: used to calc OFFSET
        :param bool return_count: do not select list of IDs 
            and do not apply limit and offset if it's True
        """
        offset = page*limit
        params = {}

        def _build_sql(ttype, pick_params=False):
            """ Returns full SQL query or part for UNION query

            :param str ttype: determines either find offers or wants
            :param bool pick_params: should be False 
                if used second time in UNION query
            :return tuple: sql and params
            """
            if return_count:
                sql = 'SELECT COUNT(a.id) '
            else:
                sql = 'SELECT a.id, a.delivery_date '
            sql += 'FROM marketplace_announcement a '\
            'LEFT JOIN res_partner p on p.id = a.partner_id '\
            'WHERE state=\'open\' '
            
            if ttype:
                sql += 'AND a.type = \'%s\' ' % ('want' if ttype == 'to_offer' else 'offer')
            if data.get('name'): 
                sql += 'AND a.name ILIKE %(name)s '
                params.update({'name': '%'+data.get('name')+'%'})
            if data.get('categories', []):
                sql += 'AND a.category_id IN %(category)s '
                params.update({'category': tuple(data.get('categories', []))})
            if data.get('city'):
                sql += 'AND (a.city ILIKE %(city)s OR a.street2 ILIKE %(city)s) '
                params.update({'city': '%'+data.get('city')+'%'})
            if data.get('date_from'): 
                date_from = datetime.strptime(data.get('date_from'), date_format)
                sql += 'AND (a.delivery_date >= %(date_from)s OR delivery_date IS NULL)  '
                params.update({'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            if data.get('date_to'):
                date_to = datetime.strptime(data.get('date_to'), date_format)
                sql += 'AND (a.delivery_date <= %(date_to)s OR delivery_date IS NULL) '
                params.update({'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            if data.get('from_who'):
                sql += 'AND p.name ILIKE %(partner_name)s '
                params.update({'partner_name': '%'+data.get('from_who')+'%'})
            if int(data.get('currency','0')):
                params.update({'currency': int(data.get('currency','0'))})
                if not data.get('price_from') and not data.get('price_to'):
                    sql += 'AND EXISTS(SELECT 1 FROM account_wallet_currency_line cl '\
                        'WHERE cl.model = \'marketplace.announcement\' '\
                        'AND cl.res_id = a.id AND cl.currency_id = %(currency)s) '
            if data.get('qty_from') and data.get('currency'):
                sql += 'AND EXISTS('\
                    'SELECT 1 FROM account_wallet_currency_line cl '\
                    'WHERE cl.model = \'marketplace.announcement\' '\
                    'AND cl.res_id = a.id AND cl.currency_id = %(currency)s '\
                    'AND cl.price_unit >= %(price_from)s) '
                params.update({'price_from': data.get('qty_from')})
            if data.get('qty_to') and data.get('currency'):
                sql += 'AND EXISTS('\
                    'SELECT 1 FROM account_wallet_currency_line cl '\
                    'WHERE cl.model = \'marketplace.announcement\' '\
                    'AND cl.res_id = a.id AND cl.currency_id = %(currency)s '\
                    'AND cl.price_unit <= %(price_to)s) '
                params.update({'price_to': data.get('qty_to')})
            if not return_count:
                sql += 'GROUP BY a.id '
                sql += 'ORDER BY a.delivery_date ASC '
                if limit:
                    sql += 'LIMIT %(limit)s '
                    params.update({'limit': limit})
                if offset:
                    sql += 'OFFSET %(offset)s '
                    params.update({'offset': offset})

            return sql

        if not data.get('type') or data.get('type') == 'to_get':
            # Find both wants and offers using UNION query
            return '(%s) UNION (%s)' % (_build_sql('to_offer', True), _build_sql('to_get')) \
                + (' ORDER BY delivery_date ASC' if not return_count else ''), params
        else:
            return _build_sql(data.get('type')), params

    def _get_url(self, type, offset, params):
        """ Returns url for Prev and Next buttons in the pager 
        """
        url_pairs = [(k, v) for k,v in params.iteritems() if k in self.SEARCH_PARAMS]
        url_pairs.append(('page', str(offset) if type == 'prev' else str(offset+1)))
        url = '/marketplace/search?' + '&'.join(['='.join(x) for x in url_pairs])
        return url

    @http.route('/marketplace/search', type='http', auth="public", website=True)
    def search(self, **kw):
        """ Display search page and first results 
        :param dict kw: POST data
        """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        category_pool = request.registry.get('marketplace.announcement.category')
        result = {'wants': [], 'offers': []}
        date_format = get_date_format(cr, uid, context)
        post_params = dict([(k,v) for k,v in kw.iteritems() if k in self.SEARCH_PARAMS])
        # Search in child categories
        category_id = int(kw.get('category','0'))
        if category_id:
            post_params.update({
                'categories': category_pool.search(cr, uid, 
                    [('id','child_of',category_id)],context=context)
            })
        sql = self._build_query(post_params, date_format, kw.get('limit',self.QUERY_LIMIT), int(kw.get('page','1'))-1)
        cr.execute(sql[0], sql[1] or ())
        res_ids = [row[0] for row in cr.fetchall()]
        res_data = mp_announcement_pool.browse(cr, uid, res_ids, context=context)
        
        #select number both of wants and offers
        count_sql = self._build_query(post_params, date_format, False, False, True)
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
            'next_url': self._get_url('next', int(kw.get('page', '1')), post_params),
            'prev_url': self._get_url('prev', int(kw.get('page', '1'))-1, post_params),
            'format_text': format_text
        })

    @http.route(['/marketplace/search/load_more'], type='http', auth="public", methods=['GET'], website=True)
    def load_more(self, **kw):
        """ Display results after load more signal(only for ajax) 
        """
        cr, uid, context = request.cr, request.uid, request.context
        mp_announcement_pool = request.registry.get('marketplace.announcement')
        result = {'wants': [], 'offers': []}
        date_format = get_date_format(cr, uid, context)
        sql = self._build_query(dict([(k,v) for k,v in kw.iteritems() if k in self.SEARCH_PARAMS]), 
            date_format, kw.get('limit',self.QUERY_LIMIT), kw.get('offset'))
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


