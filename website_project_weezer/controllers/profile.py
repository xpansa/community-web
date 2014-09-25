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

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

import base64
from datetime import datetime
import re
from search import get_date_format
from search import format_text
import time


class search_controller(http.Controller):

    PARTNER_FIELDS = ['name', 'title', 'street', 'street2', 'zip', 'city', 'state_id',
                      'country_id', 'birthdate', 'email', 'phone', 'mobile', 'image']
    LAST_EXCHANGES_LIMIT = 3
    ANNOUNCEMENT_LIMIT = 3
    date_format = '%d-%m-%Y'

    def profile_parse_data(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        values = {
            'partner': {},
            'limits': {'new': {}, 'existing': {}},
            'balances': {'new': {}, 'existing': {}},
            'skills': {'new': [], 'existing': []},
            'interests': {'new': [], 'existing': []},
        }
        for k, val in data.iteritems():
            if k in self.PARTNER_FIELDS:
                if k == 'birthdate':
                    if val:
                        try:
                            values['partner'][k] = datetime.strptime(val, self.date_format)
                        except:
                            values['partner'][k] = False
                    else:
                        values['partner'][k] = False
                elif k in ['state_id', 'country_id']:
                    values['partner'][k] = int(val) if val else False
                elif k == 'image':
                    if val:
                        values['partner'][k] = base64.encodestring(val.read())
                else:
                    values['partner'].update({k: val})
            elif k.startswith('skills'):
                existing = re.search('skills\[existing\]\[(\d+)\]', k)
                if existing:
                    values['skills']['existing'].append(existing.group(1))
                else:
                    values['skills']['new'].append(val)
            elif k.startswith('tags'):
                existing = re.search('tags\[existing\]\[(\d+)\]', k)
                if existing:
                    values['interests']['existing'].append(existing.group(1))
                else:
                    values['interests']['new'].append(val)
            elif k.startswith('limits'):
                for key in ['currency', 'min', 'max']:
                    for key2 in ['new', 'existing']:
                        limit_number = re.search('limits\[%s\]\[(\d+)\]\[%s\]' % (key2, key), k)
                        if limit_number:
                            limit_number = int(limit_number.group(1))
                            if not limit_number in values['limits'][key2]:
                                values['limits'][key2][limit_number] = {key: val}
                            else:
                                values['limits'][key2][limit_number].update({key: val})
            elif k.startswith('balances'):
                for key in ['currency', 'amount']:
                    for key2 in ['new', 'existing']:
                        balance_number = re.search('balances\[%s\]\[(\d+)\]\[%s\]' % (key2, key), k)
                        if balance_number:
                            balance_number = int(balance_number.group(1))
                            if not balance_number in values['balances'][key2]:
                                values['balances'][key2][balance_number] = {key: val}
                            else:
                                values['balances'][key2][balance_number].update({key: val})
        values['limits']['new'] = [val for k, val in values['limits']['new'].iteritems()]
        values['balances']['new'] = [val for k, val in values['balances']['new'].iteritems()]
        return values

    def profile_images(self, partner):
        values = {
            'image_big': partner.image and ("data:image/png;base64,%s" % partner.image) or \
            '/web/static/src/img/placeholder.png',
            'image_small': partner.image_small and ("data:image/png;base64,%s" % partner.image_small) or \
            '/web/static/src/img/placeholder.png',
        }
        return values

    def profile_last_exchanges(self, partner_id):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        proposition_pool = registry.get('marketplace.proposition')
        args = ['|', ('sender_id', '=', partner_id), ('receiver_id', '=', partner_id)]
        proposition_ids = proposition_pool.search(cr, uid, args, limit=self.LAST_EXCHANGES_LIMIT, 
                                                  order='write_date desc', context=context)
        return proposition_pool.browse(cr, uid, proposition_ids, context=context)

    def profile_announcements(self, partner_id, ttype):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        announcement_pool = registry.get('marketplace.announcement')
        announcement_ids = announcement_pool.search(cr, uid, [('partner_id', '=', partner_id),
            ('type', '=', ttype), ('state', '=', 'open')], limit=self.ANNOUNCEMENT_LIMIT, context=context)
        return announcement_pool.browse(cr, uid, announcement_ids, context=context)

    def profile_values(self, partner, data=None):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        title_pool = registry.get('res.partner.title')
        country_pool = registry.get('res.country')
        state_pool = registry.get('res.country.state')
        config_currency_pool = registry.get('account.centralbank.config.currency')
        curr_config_ids = config_currency_pool.search(cr, uid, [], context=context)
        curr_config_lines = config_currency_pool.read(cr, uid, curr_config_ids, 
                                                      ['currency_id'], context=context)
        self.date_format = get_date_format(cr, uid, context=context)
        values = {
            'errors': {},
            'partner': partner,
            'partner_titles': title_pool.name_search(cr, uid, '', [], context=context),
            'countries': country_pool.name_search(cr, uid, '', [], context=context),
            'states': state_pool.name_search(cr, uid, '', [], context=context),
            'is_administrator': uid == SUPERUSER_ID,
            'currencies': [(c['currency_id'][0], c['currency_id'][1]) for c in curr_config_lines],
            'birthdate': '',
            'date_placeholder': self.date_format.replace('%d','DD').replace('%m','MM').replace('%Y','YYYY'),
            'last_exchanges': self.profile_last_exchanges(partner.id),
            'wants': self.profile_announcements(partner.id, 'want'),
            'offers': self.profile_announcements(partner.id, 'offer'),
        }
        if partner.birthdate:
            values.update({
                'birthdate': datetime.strptime(partner.birthdate, DEFAULT_SERVER_DATETIME_FORMAT).strftime(self.date_format),    
            })
        if data:
            values['profile'] = self.profile_parse_data(data)
        return values

    def profile_form_validate(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        errors = {}
        for k, val in data['partner'].iteritems():
            if k == 'name' and not val:
                errors[k] = _('Name cannot be empty')
            elif k == 'email' and val:
                if not re.match('[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}', val):
                    errors[k] = _('Email is not correct')
        print data['limits']
        print data['balances']
        return errors

    def profile_save(self, partner, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_pool = registry.get('res.partner')
        skill_category_pool = registry.get('marketplace.announcement.category')
        tag_pool = registry.get('marketplace.tag')
        limit_pool = registry.get('res.partner.centralbank.currency')
        balance_pool = registry.get('res.partner.centralbank.balance')
        partner_pool.write(cr, uid, [partner.id], data['partner'], context=context)
        
        # Create new skills (marketplace.announcement.category)
        for skill in data['skills']['new']:
            skill_id = skill_category_pool.search(cr, uid, [('name','=',skill)], context=context)
            if not skill_id:
                skill_id = skill_category_pool.create(cr, uid, {'name': skill}, context=context)
                data['skills']['existing'].append(skill_id)
        # Create new interests (marketplace.tag)
        for tag in data['interests']['new']:
            tag_id = tag_pool.search(cr, uid, [('name','=',tag)], context=context)
            if not tag_id:
                tag_id = tag_pool.create(cr, uid, {'name': tag}, context=context)
                data['interests']['existing'].append(tag_id)
        # Update partner skills and interests
        partner_pool.write(cr, uid, [partner.id], {
            'skill_category_ids': [(6, 0, data['skills']['existing'])],
            'skill_tag_ids': [(6, 0, data['interests']['existing'])],
        }, context=context)

        
        limits_to_delete = list(set([item.id for item in partner.centralbank_currency_ids]) \
            - set(data['limits']['existing'].keys()))
        # Update existing limits
        for id, limit in data['limits']['existing'].iteritems():
            if limit['currency'] and (limit['min'] or limit['max']):
                limit_pool.write(cr, uid, id, {
                    'limit_negative_value': float(limit['min']),
                    'limit_positive_value': float(limit['max']),
                    'currency_id': int(limit['currency']),
                }, context=context)
            else:
                limits_to_delete.append(id)
        # Delete limits
        limit_pool.unlink(cr, uid, limits_to_delete, context=context)
        # Create limits
        for limit in data['limits']['new']:
            if limit['currency'] and (limit['min'] or limit['max']):
                limit_pool.create(cr, uid, {
                    'limit_negative_value': float(limit['min']),
                    'limit_positive_value': float(limit['max']),
                    'currency_id': int(limit['currency']),
                    'partner_id': partner.id,
                }, context=context)

        
        balances_to_delete = list(set([item.id for item in partner.centralbank_balance_ids]) \
            - set(data['balances']['existing'].keys()))
        # Update existing balances
        for id, balance in data['balances']['existing'].iteritems():
            if balance['currency'] and balance['amount']:
                balance_pool.write(cr, uid, id, {
                    'available': float(balance['amount']),
                    'currency_id': int(balance['currency']),
                }, context=context)
            else:
                balances_to_delete.append(id)
        # Delete balances
        balance_pool.unlink(cr, uid, balances_to_delete, context=context)
        # Create balances
        for balance in data['balances']['new']:
            if balance['currency'] and balance['amount']:
                balance_pool.create(cr, uid, {
                    'available': float(balance['amount']),
                    'currency_id': int(balance['currency']),
                    'partner_id': partner.id,
                }, context=context)

    @http.route('/marketplace/profile/edit/<model("res.partner"):partner>', type='http', auth="user", website=True)
    def profile_edit(self, partner, **kw):
        """
        Display profile edit page, save canges
        :param dict kw: POST data from form
        """
        if 'save_form' in kw:
            values = self.profile_values(partner, kw)
            # values['errors'] = self.profile_form_validate(values['profile'])
            if not values['errors']:
                self.profile_save(partner, values['profile'])
        else:
            values = self.profile_values(partner)
        values['images'] = self.profile_images(partner)
        values['format_text'] = format_text

        return request.website.render("website_project_weezer.profile_edit", values)

    @http.route('/marketplace/profile/edit', type='http', auth="user", website=True)
    def profile_edit_me(self, **kw):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_pool = registry.get('res.users')
        partner = user_pool.browse(cr, uid, uid, context=context).partner_id

        return self.profile_edit(partner, **kw)

    @http.route('/marketplace/profile/<model("res.partner"):partner>', type='http', auth="public", website=True)
    def profile_view(self, partner=None):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        date_format = get_date_format(cr, uid, context=context)
        return request.website.render("website_project_weezer.profile_view", {
            'partner': partner,
            'images': self.profile_images(partner),
            'wants': self.profile_announcements(partner.id, 'want'),
            'offers': self.profile_announcements(partner.id, 'offer'),
            'format_text': format_text,
            'last_exchanges': self.profile_last_exchanges(partner.id),
            'birthdate': datetime.strptime(partner.birthdate, DEFAULT_SERVER_DATETIME_FORMAT).strftime(date_format) \
                        if partner.birthdate else '',
        })

    @http.route('/marketplace/profile', type='http', auth="user", website=True)
    def profile_view_me(self):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_pool = registry.get('res.users')
        partner = user_pool.browse(cr, uid, uid, context=context).partner_id

        return self.profile_view(partner)

    @http.route('/marketplace/profile/get_skills', type='json', auth='user', website=True)
    def get_skills(self, term):
        cr, uid, context = request.cr, request.uid, request.context
        skill_pool = request.registry.get('marketplace.announcement.category')
        skills = skill_pool.name_search(cr, uid, term, [], context=context)
        return [{'label': s[1], 'id': s[0], 'value': s[1]} for s in skills]

    @http.route('/marketplace/profile/get_interests', type='json', auth='user', website=True)
    def get_interests(self, term):
        cr, uid, context = request.cr, request.uid, request.context
        tag_pool = request.registry.get('marketplace.tag')
        tags = tag_pool.name_search(cr, uid, term, [], context=context)
        return [{'label': s[1], 'id': s[0], 'value': s[1]} for s in tags]
