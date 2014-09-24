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

from datetime import datetime
from search import get_date_format


class search_controller(http.Controller):

    PARTNER_FIELDS = ['name', 'title', 'street', 'street2', 'zip', 'city', 'state_id',
                      'country_id', 'birthdate', 'email', 'phone', 'mobile']

    def profile_parse_data(self, data, date_format):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        print data
        values = {'partner': {}}
        for k, val in data.iteritems():
            if k in self.PARTNER_FIELDS:
                if k == 'birthdate':
                    if val:
                        values['partner'][k] = datetime.strptime(val, date_format)
                    else:
                        values['partner'][k] = False
                elif k in ['state_id', 'country_id']:
                    values['partner'][k] = int(val) if val else False
                else:
                    values['partner'].update({k: val})

        return values

    def profile_values(self, data=None):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_pool = request.registry.get('res.users')
        title_pool = request.registry.get('res.partner.title')
        country_pool = request.registry.get('res.country')
        state_pool = request.registry.get('res.country.state')
        config_currency_pool = request.registry.get('account.centralbank.config.currency')
        partner = user_pool.browse(cr, uid, uid, context=context).partner_id
        curr_config_ids = config_currency_pool.search(cr, uid, [], context=context)
        curr_config_lines = config_currency_pool.read(cr, uid, curr_config_ids, 
                                                      ['currency_id'], context=context)
        date_format = get_date_format(cr, uid, context=context)
        values = {
            'partner': partner,
            'partner_titles': title_pool.name_search(cr, uid, '', [], context=context),
            'countries': country_pool.name_search(cr, uid, '', [], context=context),
            'states': state_pool.name_search(cr, uid, '', [], context=context),
            'is_administrator': uid == SUPERUSER_ID,
            'currencies': [(c['currency_id'][0], c['currency_id'][1]) for c in curr_config_lines],
            'birthdate': datetime.strptime(partner.birthdate, DEFAULT_SERVER_DATETIME_FORMAT).strftime(date_format),
            'date_placeholder': date_format.replace('%d','DD').replace('%m','MM').replace('%Y','YYYY'),
        }
        if data:
            values['profile'] = self.profile_parse_data(data, date_format)
        return values

    def profile_form_validate(self, data):
        return {}

    def profile_save(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_pool = request.registry.get('res.users')
        partner_pool = request.registry.get('res.partner')
        partner_id = user_pool.browse(cr, uid, uid, context=context).partner_id
        partner_pool.write(cr, uid, [partner_id.id], data['partner'], context=context)
        

    @http.route('/marketplace/profile/edit', type='http', auth="user", website=True)
    def profile_edit(self, **kw):
        """
        Display profile edit page, save canges
        :param dict kw: POST data from form
        """
        if 'save_form' in kw:
            values = self.profile_values(kw)
            values["error"] = self.profile_form_validate(values['profile'])
            if not values["error"]:
                self.profile_save(values["profile"])
        else:
            values = self.profile_values()

        return request.website.render("website_project_weezer.profile_edit", values)

    @http.route('/marketplace/profile/<model("res.partner"):partner>', type='http', auth="public", website=True)
    def profile_view(self, partner):
        return request.website.render("website_project_weezer.profile_view", {
            'partner': partner    
        })

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
