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
import urllib

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers

from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class member_list_controller(http.Controller):

    PAGE_LIMIT = 8

    def convert_tuple_to_dict(self, cr, uid, tuple_list, context=None):
        """ Convert search name tuple to dict
        """
        res = dict()
        for record in tuple_list:
            res.update({record[0]: record[1]})
        return res
    

    def get_all_records(self, cr, uid, registry, model_name, search_args=None, context=None):
        """ Return all records of specified model
        """
        if not search_args:
            search_args = []
        pool = registry.get(model_name)
        res = pool.name_search(cr, uid, '', search_args, context=context)
        return self.convert_tuple_to_dict(cr, uid, res, context=context)

    def get_all_membership(self, cr, uid, registry, context=None):
        """ Return all membership from product
        """
        return self.get_all_records(cr, uid, registry, 'product.product', 
                                                        search_args=[('membership','=','True')], context=context)

    @http.route(['/marketplace/member_list/<int:page>', 
                 '/marketplace/member_list'], type='http', auth="public", website=True)
    def route_member_list(self, page=1):
        """ Router for member list page
        """
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
                'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
                'membership_dict': self.get_all_membership(cr, uid, registry, context=context),
                'page_count': count/self.PAGE_LIMIT + (1 if count%self.PAGE_LIMIT else 0),
                'next_url': '/marketplace/member_list%s' % (('/' + str(page+1)) if page*self.PAGE_LIMIT < count else ''),
                'prev_url': '/marketplace/member_list%s' % (('/' + str(page-1)) if page > 1 else ''),
            })

    def __build_search_query(self, cr, uid, registry, data, limit=None, offset=None, get_count=False,context=None):
        """ Method, which building sql request for searching members by specified parametersMethod building sql
            request for searching members by specified paramrters
            :param cr: database coursor
            :param uid: id of current user
            :param dict data: dict of params from GET request
            :param limit: max count of records to get 
            :param offset: offset in database in records to get 
            :param bool get_count: flag to get record's ids or count of record 
            :param context: odoo context 
            :return: tuple of sql request, values to request, 
        """
        if get_count:
            sql = 'SELECT count(a.id) '
        else:
            sql = 'SELECT a.id '

        sql += 'FROM res_partner a '  \
              'WHERE a.active = True'

        params = dict()
        if data.get('search_name'):
            sql += ' AND a.name ILIKE %(search_name)s'
            params.update({'search_name': '%' + data.get('search_name') + '%'})

        if data.get('location'):
            sql += ' AND (a.city ILIKE %(location)s OR a.street ILIKE %(location)s OR a.street2 ILIKE %(location)s)'
            params.update({'location': '%'+data.get('location')+'%'})

        if data.get('tag'):
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'res_partner_marketplace_tag_rel rel LEFT JOIN marketplace_tag tag on tag.id = rel.tag_id '\
                    'WHERE rel.partner_id = a.id AND tag.name = %(tag)s)'
            params.update({'tag': data.get('tag')})

        if data.get('group'):
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'mail_group LEFT JOIN mail_followers followers on mail_group.id = followers.res_id '\
                    'WHERE mail_group.name = %(group)s AND followers.res_model = \'mail.group\' AND followers.partner_id = a.id)'
            params.update({'group': data.get('group')})            

        membership_condition = ''
        for membership_id in self.get_all_membership(cr, uid, registry, context=context).keys():
            data_key = 'membership_%s' % membership_id
            if data.get(data_key):
                if membership_condition:
                    membership_condition += ' OR '    
                membership_condition += 'membership.membership_id=%(' + data_key + ')s' 
                params.update({data_key: membership_id})
                                                                
        if membership_condition:
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'membership_membership_line membership '\
                    'WHERE membership.partner = a.id AND %s)' % membership_condition
        
        currency_id = data.get('currency_id')
        if currency_id and currency_id != 'None':
            amount_condition = ''
            amount_from = data.get('amount_from')
            amount_to = data.get('amount_to')
            if amount_from or amount_to:
                amount_from_fl = None
                amount_to_fl = None
                try:
                    amount_from_fl = float(amount_from) if amount_from else None
                    amount_to_fl = float(amount_to) if amount_to else None
                except:
                    pass #DO NOTHING
                if amount_from_fl:
                    amount_condition += 'balance.available >= %(amount_from)s' 
                    params.update({'amount_from': amount_from_fl})
                if amount_to_fl:
                    if amount_from_fl:
                        amount_condition += ' AND balance.available <= %(amount_to)s'
                    else:
                        amount_condition = 'balance.available <= %(amount_to)s'
                    params.update({'amount_to': amount_to_fl})

            if amount_condition:
                amount_condition += ' AND '
            amount_condition += 'balance.currency_id = %(currency_id)s'
            params.update({'currency_id': currency_id})

            sql += ' AND EXISTS(' \
                        'SELECT 1 FROM res_partner_centralbank_balance balance '\
                        'WHERE balance.partner_id = a.id AND (%s))' % amount_condition

        if not get_count:
            sql += ' ORDER BY a.name'
        if limit != None:
            sql += ' LIMIT %s' % limit
        if offset != None:
            sql += ' OFFSET %s' % offset
        return sql, params

    def get_url_param(self, params):
        return urllib.urlencode(params)

    @http.route(['/marketplace/member_list/search',
        '/marketplace/member_list/search/<int:page>'], type='http', auth="public", website=True)
    def route_member_list_search(self, page=1, **data):
        """ Router for search in member list
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_pool = registry.get('res.partner')
        offset = (page - 1) * self.PAGE_LIMIT
        sql = self.__build_search_query(cr, uid, registry, data, limit=self.PAGE_LIMIT, offset=offset, context=context)
        cr.execute(sql[0], sql[1])
        res_ids = [row[0] for row in cr.fetchall()]
        res_data = partner_pool.browse(cr, uid, res_ids, context=context)
        count_sql = self.__build_search_query(cr, uid, registry, data, get_count=True, context=context)
        cr.execute(count_sql[0], count_sql[1])
        count = cr.fetchall()
        count = count[0][0]
        params = self.get_url_param(data)
        
        return http.request.website.render('website_project_weezer.member_list_view', {
                'member_list': res_data,
                'page': page,
                'search_param': data,
                'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
                'membership_dict': self.get_all_membership(cr, uid, registry, context=context),
                'page_count': count/self.PAGE_LIMIT + (1 if count % self.PAGE_LIMIT else 0),
                'next_url': '/marketplace/member_list/search%s?%s' % (('/' + str(page+1)) if page*self.PAGE_LIMIT < count else '', params),
                'prev_url': '/marketplace/member_list/search%s?%s' % (('/' + str(page-1)) if page > 1 else '', params),
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
