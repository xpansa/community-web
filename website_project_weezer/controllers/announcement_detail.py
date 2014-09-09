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

import base64
import logging
import os

from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers

from openerp.tools.translate import _

logger = logging.getLogger(__name__)

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

        attachment_ids = attach_pool.search(cr, uid, [ ('res_model','=','marketplace.announcement'),
                                                      ('res_id','=', announcement.id ),
                                                                                          ] )
        attachment_dict = dict()
        for attachment in attach_pool.browse(cr, uid, attachment_ids):
            attachment_dict.update({'/marketplace/announcement_detail/%s/attachment/%s' % (announcement.id, attachment.id): attachment.name})
        return attachment_dict

    def get_tag_dict_by_category(self, cr, uid, registry, category_id, context=None):
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

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/attachment/<model("ir.attachment"):attachment>', type='http', auth="public", website=True)
    def download_attachment(self, announcement, attachment):
        if attachment.res_id == announcement.id:
            filecontent = base64.b64decode(attachment.datas)
            if not filecontent:
                responce = request.not_found()
            else:
                filename = attachment.name
                responce = request.make_response(filecontent,
                [('Content-Type', 'application/octet-stream'),
                 ('Content-Disposition', content_disposition(filename))])
        else:
            responce = request.not_found()
        return responce

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
            'tag_dict': self.get_tag_dict_by_category(cr, uid, request.registry, announcement.category_id.id, context=context)
        })

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/save', type='http', auth="user")
    def save_announcement(self, announcement, **post):
        cr, uid, context = request.cr, request.uid, request.context

        error_message_list = list()
        error_param_list = list() 

        vals = dict()
        if post.get('category_id'):
            category_id = post.get('category_id')
            if category_id != 'None':
                res_id = request.registry.get('marketplace.announcement.category').search(cr, uid, [('id', '=', category_id)], limit=1, context=context)
                if res_id == category_id:
                    vals.update({'category_id': res_id})
                else:
                    error_message_list.append(_('There is no such category'))
                    error_param_list.append('category_id')
            else:
                vals.update({'category_id': False})

        if post.get('tag_ids'):
            logger.error("======================================")
            logger.error(post.get('tags_ids'))
            logger.error(type(post.get('tags_ids')))


        if post.get('document'):
            picture = post.get('picture')
            try:
                attachment_id = request.registry.get('ir.attachment').create(cr, uid, {
                    'name': picture.filename,
                    'datas': base64.encodestring(picture.read()),
                    'datas_fname': picture.filename,
                    'res_model': 'marketplace.announcement',
                    'res_id': announcement.id,
                }, context=context)
            except Exception, e:
                error_message_list.append(unicode(e))
                error_param_list.append('document')

        if len(error_param_list) > 0:
            if vars().has_key('attachment_id') and attachment_id:
                request.registry.get('ir.attachment').unlink(cr, uid, attachment_id, context=context)
        return "%s%s%s" % (post,2, 1)





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
