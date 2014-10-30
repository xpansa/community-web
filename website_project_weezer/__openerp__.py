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

{
    'name': 'Website Marketplace',
    'category': 'Website',
    'summary': 'Website addition to marketplace module',
    'version': '1.0',
    'description': """
Custom Theme
Website Marketplace

        """,
    'author': 'Author Name • WebByBrains <author@webbybrains.com>, Igor Krivonos <igor.krivonos@xpansa.com>',
    'depends': [
        'auth_signup',
        'event',
        'website',
        'marketplace',
        'association',
        'marketplace_groups',
        'membership',
        'website_blog',
        'website_event',
        'website_mail_group',
    ],
    'data': [
        'data/menu.xml',
        'data/marketplace_announcement_category.xml',
        'data/users.xml',
        'views/assets.xml',
        'views/snippets.xml',
        'views/templates/404.xml',
        'views/templates/layout.xml',
        'views/templates/login.xml',
        'views/templates/login_layout.xml',
        'views/templates/mp_search.xml',
        'views/templates/mp_search_form.xml',
        'views/templates/mp_single_item.xml',
        'views/templates/reset_password.xml',
        'views/templates/signup.xml',
        'views/templates/signup_fields.xml',
        'views/templates/single_reply.xml',
        'views/templates/view_announcement.xml',
        'views/templates/edit_announcement.xml',
        'views/templates/new_announcement.xml',
        'views/templates/profile_edit_template.xml',
        'views/templates/profile_view_template.xml',
        'views/templates/register_template.xml',
        'views/templates/member_list_view.xml',
        'views/templates/single_member_view.xml',
        'views/templates/home.xml',
        'security/ir.model.access.csv',
        'security/website_project_weezer_security.xml',
    ],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
