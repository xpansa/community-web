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

class announcement_controller(http.Controller):
    
    def get_dict_from_list(self, source_list, key='id', value='name', context=None):
        new_dict = dict()
        for item in source_list:
            new_dict.update({item[key]: item[value]})
        return new_dict

    def get_us_state_dict(self, cr, uid, registry, context=None):
        country_pool = registry.get('res.country')
        state_pool = registry.get('res.country.state')
        usa_id = country_pool.search(cr, uid, [('code','=','US')], context=context)[0]
        us_state_list = state_pool.search(cr, uid, [('country_id', '=', usa_id)], context=context)
        us_state_list = state_pool.browse(cr, uid, us_state_list, context=context)
        return self.get_dict_from_list(us_state_list, context=context)

    def get_country_dict(self, cr, uid, registry, context=None):
        country_pool = registry.get('res.country')
        country_list = country_pool.search(cr, uid, [], context=context)
        country_list = country_pool.browse(cr, uid, country_list, context=context)
        return self.get_dict_from_list(country_list, context=context)

    def get_category_dict(self, cr, uid, registry, context=None):
        category_pool = registry.get('marketplace.announcement.category')
        category_list = category_pool.search(cr, uid, [], context=context)
        category_list = category_pool.browse(cr, uid, category_list, context=context)
        return self.get_dict_from_list(category_list, context=context)


    def get_currency_dict(self, cr, uid, registry, context=None):
        currency_pool = registry.get('res.currency')
        currency_list = currency_pool.search(cr, uid, [], context=context)
        currency_list = currency_pool.browse(cr, uid, currency_list, context=context)
        return self.get_dict_from_list(currency_list, context=context)

    def get_group_dict(self, cr, uid, registry, context=None):
        currency_pool = registry.get('mail.group')
        currency_list = currency_pool.search(cr, uid, [], context=context)
        currency_list = currency_pool.browse(cr, uid, currency_list, context=context)
        return self.get_dict_from_list(currency_list, context=context)

    def get_state_status_dict(self, cr, uid, registry, context=None):
        return {
            'draft': 'Draft',
            'open': 'Published',
            'done': 'Closed',
            'cancel': 'Cancelled',
        }

    def get_attachment_dict(self, cr, uid, registry, announcement, context=None):
        attach_pool = registry.get('ir.attachment')
        message_pool = registry.get('mail.attachment')

        attachment_ids = attach_pool.search(cr, uid, [ ('res_model','=','marketplace.announcement'),
                                                      ('res_id','=', announcement.id ),
                                                                                          ] )
        attachment_dict = dict()
        for attachment in attach_pool.browse(cr, uid, attachment_ids):
            attachment_dict.update({attachment.website_url: attachment.name})
        return attachment_dict

    def get_dict_by_category(self, cr, uid, registry, category_id, context=None):
        tag_pool = registry.get('marketplace.tag')
        tag_list = tag_pool.search(cr, uid, [('category_id', '=', category_id)], context=context)
        tag_list = tag_pool.browse(cr, uid, tag_list, context=context)
        return self.get_dict_from_list(tag_list, context=context)

    
    @http.route('/marketplace/announcement_detail/tags/<int:category_id>/get', type='json', auth="public", website=True)
    def tag_dict_by_category(self, category_id):
        cr, uid, context = request.cr, request.uid, request.context

        return {
        	'tag_dict': self.get_tag_dict_by_category(cr, uid, request.registry, category_id, context=context),
        }


    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/edit', type='http', auth="public", website=True)
    def edit_announcement(self, announcement):
        cr, uid, context = request.cr, request.uid, request.context
        
        return http.request.website.render('website_project_weezer.edit_announcement', {
            'announcement':announcement,
            'author': announcement.partner_id,
            'us_state_dict': self.get_us_state_dict(cr, uid, request.registry, context=context),
            'country_dict': self.get_country_dict(cr, uid, request.registry, context=context),
            'state_status_dict': self.get_state_status_dict(cr, uid, request.registry, context=context),
            'category_dict': self.get_category_dict(cr, uid, request.registry, context=context),
            'currency_dict': self.get_currency_dict(cr, uid, request.registry, context=context),
            'group_dict': self.get_group_dict(cr, uid, request.registry, context=context),
            'attachment_dict': self.get_attachment_dict(cr, uid, request.registry, announcement, context=context),
        })

    @http.route('/marketplace/announcement_detail/new', type='http', auth="public", website=True)
    def new_announcement(self):
        cr, uid, context = request.cr, request.uid, request.context
        user = request.registry.get('res.users').search(cr, uid, [('id', '=', uid)], context=context)
        if user and type(user) is list:
            user = user[0]
            user = request.registry.get('res.users').browse(cr, uid, user, context=context)[0]

        return http.request.website.render('website_project_weezer.new_announcement', {
            'author': user,
            'us_state_dict': self.get_us_state_dict(cr, uid, request.registry, context=context),
            'country_dict': self.get_country_dict(cr, uid, request.registry, context=context),
            'state_status_dict': self.get_state_status_dict(cr, uid, request.registry, context=context),
            'category_dict': self.get_category_dict(cr, uid, request.registry, context=context),
            'currency_dict': self.get_currency_dict(cr, uid, request.registry, context=context),
            'group_dict': self.get_group_dict(cr, uid, request.registry, context=context),
        })

announcement_controller()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
