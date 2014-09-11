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
import datetime
import logging
import os
import werkzeug.utils

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers

from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

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
                                                      ('res_id','=', announcement.id),
                                                                                          ] )
        attachment_dict = dict()
        for attachment in attach_pool.browse(cr, uid, attachment_ids):
            if attachment.name != 'Marketplace picture':
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

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/attachment/<model("ir.attachment"):attachment>/delete', type='json', auth="public", website=True)
    def delete_attachment(self, announcement, attachment):
        if attachment.res_id == announcement.id:
            cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
            user = registry.get('res.users').browse(cr, uid, uid, context=context)

            if user and announcement.partner_id == user.partner_id or uid == SUPERUSER_ID: 
                registry.get('ir.attachment').unlink(cr, uid, attachment.id, context=context)
                responce = {'status': 'ok'}
            else:
                responce = {'status': 'error', 'error': 'You can not edit this announcement'}
        else:
            responce = {'status': 'error', 'error': 'This attachment is not belong to this announcement'}
        return responce

    def _get_view_announcement_dict(self, cr, uid, registry, announcement, context=None):
        return {
            'announcement':announcement,
            'author': announcement.partner_id,
            'state_status_dict': self.get_state_status_dict(cr, uid, request.registry, context=context),
            'attachment_dict': self.get_attachment_dict(cr, uid, request.registry, announcement, context=context),
        }

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>', type='http', auth="public", website=True)
    def view_announcement(self, announcement):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        return http.request.website.render('website_project_weezer.view_announcement', 
            self._get_edit_announcement_dict(cr, uid, registry, announcement, context=context))

    def _get_edit_announcement_dict(self, cr, uid, registry, announcement, context=None):
        return {
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
            }

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/edit', type='http', auth="public", website=True)
    def edit_announcement(self, announcement):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)

        if user and announcement.partner_id == user.partner_id or uid == SUPERUSER_ID: 
            responce = http.request.website.render('website_project_weezer.edit_announcement', 
                self._get_edit_announcement_dict(cr, uid, registry, announcement, context=context))
        else:
            responce = request.not_found()
        return responce

    def _parse_and_save_announcement(self, cr, uid, registry, announcement, post, context=None):
        error_message_list = list()
        error_param_list = list() 

        vals = dict()
        if post.get('category_id'):
            category_id = post.get('category_id')
            if category_id != 'None':
                res_id = registry.get('marketplace.announcement.category').search(cr, uid, [('id', '=', category_id)], limit=1, context=context)
                res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                if res_id:
                    vals.update({'category_id': res_id})
                else:
                    error_message_list.append(_('There is no such category'))
                    error_param_list.append('category_id')
            else:
                vals.update({'category_id': False})

        tag_list = list()
        if post.get('tag_ids'):
            tag_ids = post.get('tag_ids')
            for tag_id in tag_ids:
                if tag_id != 'None':
                    res_id = registry.get('marketplace.tag').search(cr, uid, [('id', '=', int(tag_id))], limit=1, context=context)
                    res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                    if res_id:
                        tag_list.append(res_id)

        if post.get('new_tags'):
            new_tags = post.get('new_tags')
            category_id = post.get('category_id')
            category_pool = registry.get('marketplace.announcement.category')
            if category_id != 'None':
                if category_id:
                    category_id = category_pool.search(cr, uid, [('id','=', category_id)], limit=1, context=context)
                    category_id = (category_id[0] if len(category_id) else False) if type(category_id) is list else category_id
                else:
                    category_id = announcement.category_id and announcement.category_id.id or False

            if category_id:
                for tag in new_tags:
                    if tag != 'None':
                        res_id = registry.get('marketplace.tag').create(cr, uid, {'name': tag, 'category_id': category_id}, context=context)
                        tag_list.append(res_id)
            else:
                error_message_list.append(_('You can\'t create tags if category is not selected'))
                error_param_list.append('category_id')
                error_param_list.append('new_tags')

        if len(tag_list):
            vals.update({'tag_ids': [(6, 0, tag_list)]})


        if post.get('groups'):
            group_list = list()
            groups = post.get('groups')
            for group in groups:
                if group != 'None':
                    res_id = registry.get('mail.group').search(cr, uid, [('id', '=', int(group))], limit=1, context=context)
                    res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                    if res_id:
                        group_list.append(res_id)
            vals.update({'context_group_ids': [(6, 0, group_list)]})

        if post.get('link'):
            vals.update({'link': post.get('link')})

        if post.get('emergency') and post.get('emergency') == 'on':
            vals.update({'emergency': True})
        else:
            vals.update({'emergency': False})

        if post.get('title'):
            vals.update({'name': post.get('title')})

        if post.get('description'):
            vals.update({'description': post.get('description')})

        if post.get('street'):
            vals.update({'street': post.get('street')})

        if post.get('street2'):
            vals.update({'street2': post.get('street2')})
        
        if post.get('zip'):
            vals.update({'zip': post.get('zip')})

        if post.get('city'):
            vals.update({'city': post.get('city')})

        if post.get('country_id'):
            country_id = post.get('country_id')
            if country_id != 'None':
                country_pool = registry.get('res.country')
                country_id = country_pool.search(cr, uid, [('id','=', country_id)], limit=1, context=context)
                country_id = (country_id[0] if len(country_id) else False) if type(country_id) is list else country_id
                if country_id:
                    vals.update({'country_id': country_id, 'state_id': False})
                else:
                    error_message_list.append(_('There is no such country'))
                    error_param_list.append('country_id')
            else:
                vals.update({'country_id': False, 'state_id': False})


        if post.get('state_id'):
            state_id = post.get('state_id')
            country_id = post.get('country_id')
            country_pool = registry.get('res.country')
            if country_id != 'None' and state_id != 'None':
                if country_id:
                    country_id = country_pool.search(cr, uid, [('id','=', country_id), ('code', '=', 'US')], limit=1, context=context)
                    country_id = (country_id[0] if len(country_id) else False) if type(country_id) is list else country_id
                else:
                    country_id = announcement.country_id and announcement.country_id.code == 'US' and announcement.country_id.id or False

                if country_id:
                    state_pool = registry.get('res.country.state')
                    state_id = state_pool.search(cr, uid, [('id','=',state_id)], limit=1, context=context)
                    state_id = (state_id[0] if len(state_id) else False) if type(state_id) is list else state_id
                    if state_id:
                          vals.update({'state_id': state_id})
                else:
                    error_message_list.append(_('Only announcement from USA can have state'))
                    error_param_list.append('country_id')
                    error_param_list.append('state_id')
            else:
                vals.update({'state_id': False})


        if post.get('date_from'):
            try:
                date_from = datetime.datetime.strptime(post.get('date_from'), '%Y-%m-%d')
            except ValueError:
                error_message_list.append(_('Wrong date format for date from'))
                error_param_list.append('date_from')
            else:
                vals.update({'date_from': date_from})


        if post.get('date_to'):
            try:
                date_to = datetime.datetime.strptime(post.get('date_to'), '%Y-%m-%d')
            except ValueError:
                error_message_list.append(_('Wrong date format for date to'))
                error_param_list.append('date_to')
            else:
                vals.update({'date_to': date_to})


        if vars().has_key('date_to') and vars().has_key('date_from'):
            if date_to < date_from:
                error_message_list.append(_('Date to must be greater or equal to date from'))
                error_param_list.append('date_to')
                error_param_list.append('date_from')

        if post.get('unlimited') and post.get('unlimited') == 'on':
            vals.update({'infinite_qty': True})
        else:
            vals.update({'infinite_qty': False})

        if post.get('qty'):
            try:
                qty = float(post.get('qty'))
            except ValueError:
                error_message_list.append(_('Quantity must be in float format'))
                error_param_list.append('qty')
            else:
                vals.update({'quantity': qty})

        currency = {
            'currency_amount1': 'currency_id1',
            'currency_amount2': 'currency_id2',
            'currency_amount3': 'currency_id3',
        }
        currency_value = dict()

        null_amount = False
        currency_pool = registry.get('res.currency')
        amount_fromat_error = False
        currency_exist_error = False
        null_amount_error = False
        same_currency_error = False
        for currency_amount in currency.keys(): 
            if post.get(currency_amount) and post.get(currency[currency_amount]):
                amount = False
                try:
                    amount = float(post.get(currency_amount))
                except ValueError:
                    amount_fromat_error = True
                    error_param_list.append(currency_amount)
                currency_id = currency_pool.search(cr, uid, [('id', '=', post.get(currency[currency_amount]))], limit=1, context=context)
                currency_id = (currency_id[0] if len(currency_id) else False) if type(currency_id) is list else currency_id
                if currency_id == False:
                    currency_exist_error = True
                    error_param_list.append(currency[currency_amount])

                if null_amount:
                    null_amount_error = True
                    error_param_list.append(currency_amount)

                if amount and currency_id:
                    currency_value.update({currency_id: amount})
            else:
                null_amount = True


        
        if post.get('currency_id1') == post.get('currency_id2') and post.get('currency_amount1') == post.get('currency_amount2') != '':
            error_param_list.append('currency_id1')
            error_param_list.append('currency_id2')
            same_currency_error = True

        if post.get('currency_id1') == post.get('currency_id3') and post.get('currency_amount1') == post.get('currency_amount3') != '':
            error_param_list.append('currency_id1')
            error_param_list.append('currency_id3')
            same_currency_error = True

        if post.get('currency_id3') == post.get('currency_id2') and post.get('currency_amount2') == post.get('currency_amount3') != '':
            error_param_list.append('currency_id3')
            error_param_list.append('currency_id2')
            same_currency_error = True

        if amount_fromat_error:
            error_message_list.append(_('Amount must be in a float format'))

        if currency_exist_error:
            error_message_list.append(_('There is no such currency'))

        if null_amount_error:
            error_message_list.append(_('First fill in previous amount'))

        if same_currency_error:
            error_message_list.append(_('Announcement can\'t have 2 amount with the same currency'))


        currency_line_value = dict()
        new_currency_line_value = list()
        currency_line_to_delete = list()

        if currency_exist_error or null_amount_error or same_currency_error or amount_fromat_error == False:
            currency_ids = announcement.currency_ids
            currency_count_delta = len(currency_ids) - len(currency_value.keys())
            for i in range(min(len(currency_ids), len(currency_value.keys()))):
                currency_id = currency_value.keys()[i]
                currency_amount = currency_value[currency_id]
                currency_line_value.update({currency_ids[i].id: {'currency_id': currency_id, 'price_unit': currency_amount}})

            if currency_count_delta > 0:
                for i in range(1, currency_count_delta + 1):
                    currency_line_to_delete.append(currency_ids[len(currency_ids) - i].id)

            elif currency_count_delta < 0:
                for i in range(1, abs(currency_count_delta) + 1):
                    currency_id = currency_value.keys()[len(currency_value.keys()) - i]
                    currency_amount = currency_value[currency_id]
                    new_currency_line_value.append({'announcement_id': announcement.id, 'currency_id': currency_id, 'price_unit': currency_amount})

        currency_line_pool = registry.get('account.centralbank.currency.line')

        for currency_line_id in currency_line_value.keys():
            currency_line_pool.write(cr, uid, currency_line_id, currency_line_value[currency_line_id], context=context)

        for currency_line in new_currency_line_value:
            currency_line_pool.create(cr, uid, currency_line, context=context)

        for currency_line_id in currency_line_to_delete:
            currency_line_pool.unlink(cr, uid, currency_line_id, context=context)

        if post.get('picture'):
            picture = post.get('picture')
            try:
                vals.update({'picture': base64.encodestring(picture.read())})
            except Exception, e:
                error_message_list.append(unicode(e))
                error_param_list.append('picture')

        if post.get('document'):
            document = post.get('document')
            try:
                attachment_id = registry.get('ir.attachment').create(cr, uid, {
                    'name': document.filename,
                    'datas': base64.encodestring(document.read()),
                    'datas_fname': document.filename,
                    'res_model': 'marketplace.announcement',
                    'res_id': announcement.id,
                }, context=context)
            except Exception, e:
                error_message_list.append(unicode(e))
                error_param_list.append('document')

        if len(error_param_list) > 0:
            cr.rollback()
            if context.get('from_new_announcement') == True:
                responce = self._get_new_announcement_dict(cr, uid, registry, announcement.partner_id, context=context)
                template_id = 'website_project_weezer.new_announcement'
            else:
                responce = self._get_edit_announcement_dict(cr, uid, registry, announcement, context=context)
                template_id = 'website_project_weezer.edit_announcement'

            responce.update({'error_param_list': error_param_list, 'error_message_list': error_message_list})
        else:
            res_id = registry.get('marketplace.announcement').write(cr, uid, announcement.id, vals, context=context)
            announcement = registry.get('marketplace.announcement').browse(cr, uid, announcement.id, context=context)
            responce = self._get_view_announcement_dict(cr, uid, registry, announcement, context=context)
            responce.update({'success_message_list': ['Announcement successfully saved']})
            template_id = 'website_project_weezer.view_announcement'
        
        return {'template_id': template_id, 'response': responce}

    def _prepare_save_announcemet_param(self, cr, uid, request, post):
        if post.get('tag_ids'):
            post['tag_ids'] = request.httprequest.form.getlist('tag_ids')
        if post.get('new_tags'):
            post['new_tags'] = request.httprequest.form.getlist('new_tags')
        if post.get('groups'):
            post['groups'] = request.httprequest.form.getlist('groups')

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/save', type='http', auth="user", website=True)
    def save_announcement(self, announcement, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        if user and announcement.partner_id == user.partner_id or uid == SUPERUSER_ID:  
            self._prepare_save_announcemet_param(cr, uid, request, post)
            res = self._parse_and_save_announcement(cr, uid, registry, announcement, post, context=context)
            responce = http.request.website.render(res['template_id'], res['response'])
        else:
            responce = request.not_found()
        return responce

    def _get_new_announcement_dict(self, cr, uid, registry, partner, context=None):
        return {
            'author': partner,
            'us_state_dict': self.get_us_state_dict(cr, uid, request.registry, context=context),
            'country_dict': self.get_country_dict(cr, uid, request.registry, context=context),
            'state_status_dict': self.get_state_status_dict(cr, uid, request.registry, context=context),
            'category_dict': self.get_category_dict(cr, uid, request.registry, context=context),
            'currency_dict': self.get_currency_dict(cr, uid, request.registry, context=context),
            'group_dict': self.get_group_dict(cr, uid, request.registry, context=context),
        }

    @http.route('/marketplace/announcement_detail/new', type='http', auth="public", website=True)
    def new_announcement(self):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        if user and user.partner_id:  
            responce = http.request.website.render('website_project_weezer.new_announcement', 
                self._get_new_announcement_dict(cr, uid, registry, user.partner_id, context=context))
        else:
            responce = request.not_found()

        return responce

    @http.route('/marketplace/announcement_detail/new/save', type='http', auth="user", website=True)
    def save_new_announcement(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        self._prepare_save_announcemet_param(cr, uid, request, post)
        announcement = registry.get('marketplace.announcement').create(cr, uid, {'name': '', 'partner_id': uid}, context=context)
        announcement = registry.get('marketplace.announcement').browse(cr, uid, announcement, context=context)
        if not context:
            context = dict()
        context.update({'from_new_announcement': True})
        res = self._parse_and_save_announcement(cr, uid, registry, announcement, post, context=context)
        responce = http.request.website.render(res['template_id'], res['response'])
        return responce

announcement_controller()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
