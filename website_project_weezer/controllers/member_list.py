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
        return self.get_all_records(cr, uid, registry, 'product.product', 
                                                        search_args=[('membership','=','True')], context=context)


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
                'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
                'membership_dict': self.get_all_membership(cr, uid, registry, context=context),
                'page_count': count/self.PAGE_LIMIT + (1 if count%self.PAGE_LIMIT else 0),
                'next_url': '/marketplace/member_list%s' % (('/' + str(page+1)) if page*self.PAGE_LIMIT < count else ''),
                'prev_url': '/marketplace/member_list%s' % (('/' + str(page-1)) if page > 1 else ''),
            })

    def __build_search_query(self, cr, uid, registry, post, context=None):
        sql = 'SELECT a.id '\
            'FROM res_partner a '  \
            'WHERE a.active = True'

        params = dict()
        search_param = dict()
        if post.get('search_name'):
            sql += ' AND a.name ILIKE %(search_name)s'
            params.update({'search_name': '%' + post.get('search_name') + '%'})
            search_param.update({'search_name': post.get('search_name')})

        if post.get('location'):
            sql += ' AND (a.city ILIKE %(location)s OR a.street ILIKE %(location)s OR a.street2 ILIKE %(location)s)'
            params.update({'location': '%'+post.get('location')+'%'})
            search_param.update({'location': post.get('location')})


        if post.get('tag'):
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'res_partner_marketplace_tag_rel rel LEFT JOIN marketplace_tag tag on tag.id = rel.tag_id '\
                    'WHERE rel.partner_id = a.id AND tag.name = %(tag)s)'
            params.update({'tag': post.get('tag')})
            search_param.update({'tag': post.get('tag')})


        if post.get('group'):
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'mail_group LEFT JOIN mail_followers followers on mail_group.id = followers.res_id '\
                    'WHERE mail_group.name = %(group)s AND followers.res_model = \'mail.group\' AND followers.partner_id = a.id)'
            params.update({'group': post.get('group')})            
            search_param.update({'group': post.get('group')})


        membership_condition = ''
        for membership_id in self.get_all_membership(cr, uid, registry, context=context).keys():
            post_key = 'membership_%s' % membership_id
            if post.get(post_key):
                if membership_condition:
                    membership_condition += ' OR '    
                membership_condition += 'membership.membership_id=%(' + post_key + ')s' 
                params.update({post_key: membership_id})
                search_param.update({post_key: membership_id})
                                                                
        if membership_condition:
            sql += ' AND EXISTS(SELECT 1 FROM ' \
                    'membership_membership_line membership '\
                    'WHERE membership.partner = a.id AND %s)' % membership_condition
        
        currency_id = post.get('currency_id')
        if currency_id and currency_id != 'None':
            amount_condition = ''
            amount_from = post.get('amount_from')
            amount_to = post.get('amount_to')
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
                    search_param.update({'amount_from': amount_from_fl})
                if amount_to_fl:
                    if amount_from_fl:
                        amount_condition += ' AND balance.available <= %(amount_to)s'
                    else:
                        amount_condition = 'balance.available <= %(amount_to)s'
                    params.update({'amount_to': amount_to_fl})
                    search_param.update({'amount_to': amount_to_fl})

            if amount_condition:
                amount_condition += ' AND '
            amount_condition += 'balance.currency_id = %(currency_id)s'
            params.update({'currency_id': currency_id})
            search_param.update({'currency_id': currency_id})

            sql += ' AND EXISTS(' \
                        'SELECT 1 FROM res_partner_centralbank_balance balance '\
                        'WHERE balance.partner_id = a.id AND (%s))' % amount_condition

        sql += ' ORDER BY a.name'
        return sql, params, search_param
                

    @http.route(['/marketplace/member_list/search'], type='http', auth="public", website=True)
    def route_member_list_search(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_pool = registry.get('res.partner')
        sql = self.__build_search_query(cr, uid, registry, post, context=context)
        cr.execute(sql[0], sql[1])
        res_ids = [row[0] for row in cr.fetchall()]
        res_data = partner_pool.browse(cr, uid, res_ids, context=context)

        
        return http.request.website.render('website_project_weezer.member_list_view', {
                'member_list': res_data,
                'page': 1,
                'search_param': sql[2],
                'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
                'membership_dict': self.get_all_membership(cr, uid, registry, context=context),
                'page_count': 0,
                'next_url': '',
                'prev_url': '',
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
