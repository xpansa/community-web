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

import openerp
from openerp.addons.auth_signup.controllers.main import AuthSignupHome
from openerp.addons.auth_signup.res_users import SignupError
from openerp.addons.web import http
from openerp.tools.translate import _
from openerp.http import request

from HTMLParser import HTMLParser
import werkzeug


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def get_date_format(cr, uid, context):
    """ Returns date_from from locale of current user 
    to parse dates from forms. 
    """
    if context is None:
        context = {}
    lang = context.get('lang')
    if lang:
        res_lang = request.registry.get('res.lang')
        ids = res_lang.search(cr, uid, [('code', '=', lang)])
        if ids:
            lang_params = res_lang.read(cr, uid, ids[0], ['date_format'])
            return lang_params['date_format']
    return DEFAULT_SERVER_DATE_FORMAT

def format_text(text, length=300):
        """ Cut long descriptions 
        """
        if not text:
            return ''
        text = text[0:length]
        dot_pos = text.rfind('.')
        if dot_pos:
            text = text[0:dot_pos]
        else:
            text = text[0:text.rfind(' ')]
        return text + ' '*(length - len(text))


class Website(http.Controller):

    ANNOUNCEMENT_LIMIT = 3

    def get_last_announcements(self, ttype):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        announcement_pool = registry.get('marketplace.announcement')
        announcement_ids = announcement_pool.search(cr, uid, [('state','=', 'open'), ('type', '=', ttype)],
             limit=self.ANNOUNCEMENT_LIMIT, order="delivery_date DESC", context=context)
        return announcement_pool.browse(cr, uid, announcement_ids, context=context)

    def get_last_event(self):
        """
        Get one last event
        :return: browse_record
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        event_pool = registry.get('event.event')
        event_id = event_pool.search(cr, uid, [('state','=','confirm')], order="date_begin DESC", 
                                     limit=1, context=context)
        return event_pool.browse(cr, uid, event_id, context=context)[0] if event_id else False

    def get_last_blog_post(self):
        """
        Get one last blog post
        :return: browse_record
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        post_pool = registry.get('blog.post')
        post_id = post_pool.search(cr, uid, [('website_published','=',True)], order="id DESC", 
                                     limit=1, context=context)
        return post_pool.browse(cr, uid, post_id, context=context)[0] if post_id else False

    @http.route('/page/homepage', type='http', auth="public", website=True)
    def page(self):
        """
        Homepage
        """
        values = {
            'wants': self.get_last_announcements('want'),
            'offers': self.get_last_announcements('offer'),
            'format_text': format_text,
            'event': self.get_last_event(),
            'strip_tags': strip_tags,
            'blog_post': self.get_last_blog_post(),
        }
        return request.render('website_project_weezer.homepage', values)


class MarketPlaceHome(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        """
        Extend signup page to redirect user to step 2 of registration
        """
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                return super(AuthSignupHome, self).web_login(redirect='/marketplace/register-part2')
            except (SignupError, AssertionError), e:
                qcontext['error'] = _(e.message)

        return request.render('auth_signup.signup', qcontext)