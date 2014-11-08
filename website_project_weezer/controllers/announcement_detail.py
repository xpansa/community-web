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
from datetime import datetime
import logging
import re

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp import workflow
from main import get_date_format, format_date

from attrdict import AttrDict

_logger = logging.getLogger(__name__)

DEFAULT_COUNTRY = 'US'

class announcement_controller(http.Controller):

    
    class save_annnouncement_parser():
        """ Class for parsing and validate save announcement request's params
        """
        def __init__(self, cr, uid, registry, context=None):
            self.error_message_list = list()
            self.error_param_list = list()
            self.vals = dict()
            self.cr = cr
            self.uid = uid
            self.registry = registry
            self.context = context

        def __parse_bool_param(self, post, param, attr):
            """ Process bool value from post params and save it to vals dict
            """
            if post.get(param):
                self.vals.update({attr: True})
            else:
                self.vals.update({attr: False})

        def __parse_text_param(self, post, param, attr):
            """ Process text value from post params and save it to vals dict
            """
            if post.get(param):
                self.vals.update({attr: post.get(param)})

        def __parse_date_param(self, post, param, attr, error_msg):
            """ Process date value from post params and save it to vals dict
            """
            if post.get(param):
                try:
                    date_val = datetime.strptime(post.get(param), \
                        get_date_format(self.cr, self.uid, self.context))
                except ValueError:
                    self.error_message_list.append(_(error_msg))
                    self.error_param_list.append(param)
                else:
                    self.vals.update({attr: date_val})            

        def __parse_float_param(self, post, param, attr, error_msg):
            """ Process float value from post params and save it to vals dict
            """
            if post.get(param):
                try:
                    value = float(post.get(param))
                except ValueError:
                    self.error_message_list.append(_(error_msg))
                    self.error_param_list.append(param)
                else:
                    self.vals.update({attr: value})

        def __parse_binary_param(self, post, param, attr):
            """ Process binary value from post params and save it to vals dict
            """
            if post.get(param):
                binary = post.get(param)
                try:
                    self.vals.update({attr: base64.encodestring(binary.read())})
                except Exception, e:
                    self.error_message_list.append(unicode(e))
                    self.error_param_list.append(param)

        def __parse_m2o_param(self, post, param, attr, res_model, error_msg):
            """ Process many2one value from post params and save it to vals dict
            """
            if post.get(param):
                model_id = post.get(param)
                if model_id != 'None':
                    res_id = self.registry.get(res_model).search(self.cr, self.uid, [('id', '=', model_id)], limit=1, context=self.context)
                    res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                    if res_id:
                        self.vals.update({attr: res_id})
                    else:
                        error_message_list.append(_(error_msg))
                        error_param_list.append(param)
                else:
                    self.vals.update({attr: False})

        def __parse_o2m_param(self, post, param, attr, res_model):
            """ Process one2many value from post params and save it to vals dict
            """
            if post.get(param):
                many_value_list = list()
                value_list = post.get(param)
                for value in value_list:
                    value_id = None
                    try:
                        value_id = int(value)
                    except Exception:
                        continue
                    if value_id:
                        res_id = self.registry.get(res_model).search(self.cr, self.uid, [('id', '=', value_id)], limit=1, context=self.context)
                        res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                        if res_id:
                            many_value_list.append(res_id)
                self.vals.update({attr: [(6, 0, many_value_list)]})

        def _parse_param(self, post):
            """ Parse post params with simple values
            """
            bool_params = [
                ('unlimited', 'infinite_qty'),
            ]
            text_params = [
                ('title', 'name'),
                ('description', 'description'),
                ('street', 'street'),
                ('street2', 'street2'),
                ('zip', 'zip'),
                ('city', 'city'),
                ('type', 'type'),
            ]
            date_param_list = [
                ('date_to', 'date_to', 'Wrong date format for date to'),
                ('date_from', 'date_from', 'Wrong date format for date from'),
            ]

            float_param_list = [
                ('qty', 'quantity', 'Quantity must be a float number'),
            ]

            binary_param_list = [
                ('picture', 'picture'),
            ]

            m2o_param_list = [
                ('category_id', 'category_id', 'marketplace.announcement.category', 'There is no such category'),
                ('country_id', 'country_id', 'res.country', 'There is no such country'),
                ('state_id', 'state_id', 'res.country.state', 'There is no such state'),
                ('uom_id', 'uom_id', 'product.uom', 'There is no such unit of measure'),
            ]

            o2m_param_list = [
                ('groups', 'context_group_ids', 'mail.group'),
            ]

            params_and_parsers = [
                (bool_params, self.__parse_bool_param, None),
                (text_params, self.__parse_text_param, None),
                (date_param_list, self.__parse_date_param, self.check_date_interval),
                (float_param_list, self.__parse_float_param, None),
                (binary_param_list, self.__parse_binary_param, None),
                (m2o_param_list, self.__parse_m2o_param, self.check_m2o_value),
                (o2m_param_list, self.__parse_o2m_param, None),
            ]

            for param_and_parser in params_and_parsers:
                for param in param_and_parser[0]:
                    parse_def = param_and_parser[1]
                    parse_def(post, *param)
                if param_and_parser[2]:
                    callback = param_and_parser[2]
                    callback()

            self.check_required_value()

        def check_date_interval(self):
            """ Check interval from date_from to date_to 
            """
            date_to = self.vals.get('date_to')
            date_from = self.vals.get('date_from')
            if date_to and date_from:
                if date_to < date_from:
                    self.error_message_list.append(_('Date to must be greater or equal to date from'))
                    self.error_param_list.append('date_to')
                    self.error_param_list.append('date_from')

        def check_m2o_value(self):
            """ Check all many2one values 
            """
            vals = self.vals
            country_pool = self.registry.get('res.country')

            if vals.get('country_id'):
                country_id = country_pool.search(self.cr, self.uid, [('id','=', vals.get('country_id')), \
                                                           ('code', '=', DEFAULT_COUNTRY)], limit=1, context=self.context)
                country_id = (country_id[0] if len(country_id) else False) if type(country_id) is list else country_id
                if vals.get('state_id') and not country_id:
                    self.error_message_list.append(_('Only announcement from USA can have state'))
                    self.error_param_list.append('country_id')
                    self.error_param_list.append('state_id')

        def check_required_value(self):
            """ Check if required fields are not empty
            """
            if not self.vals.get('name'):
                self.error_message_list.append(_('Title cannot be empty'))
                self.error_param_list.append('title')
            if not 'qty' in self.error_param_list and self.vals.get('qty'):
                self.error_message_list.append(_('Quantity cannot be 0.0'))
                self.error_param_list.append('qty')
        
        def _parse_attachment(self, post, param, res_model, res_id):
            """ Process attachment from post params
            """
            if post.get(param):
                document = post.get(param)
                try:
                    attachment_id = self.registry.get('ir.attachment').create(self.cr, self.uid, {
                        'name': document.filename,
                        'datas': base64.encodestring(document.read()),
                        'datas_fname': document.filename,
                        'res_model': res_model,
                        'res_id': res_id,
                    }, context=self.context)
                except Exception, e:
                    self.error_message_list.append(unicode(e))
                    self.error_param_list.append(param)

        def _parse_tags(self, post, exist_tag_param, new_tag_param, attr, category_attr):
            """ Process exited tags from post params and create new
            """
            tag_list = list()
            if post.get(exist_tag_param):
                marketplace_tag_pool = self.registry.get('marketplace.tag')
                tag_ids = post.get(exist_tag_param)
                for tag in tag_ids:
                    tag_id = None
                    try:
                        tag_id = int(tag)
                    except Exception:
                        continue
                    if tag_id:
                        res_id = marketplace_tag_pool.search(self.cr, self.uid, [('id', '=', int(tag_id))], limit=1, context=self.context)
                        res_id = (res_id[0] if len(res_id) else False) if type(res_id) is list else res_id
                        if res_id:
                            tag_list.append(res_id)

            if post.get(new_tag_param):
                new_tags = post.get(new_tag_param)
                category_id = self.vals.get(category_attr)
                if category_id:
                    for tag in new_tags:
                        if tag != 'None':
                            res_id = marketplace_tag_pool.create(self.cr, self.uid, {'name': tag, 'category_id': category_id}, context=self.context)
                            tag_list.append(res_id)
                else:
                    error_message_list.append(_('You can\'t create tags if category is not selected'))
                    error_param_list.append(new_tag_param)

            if len(tag_list):
                self.vals.update({attr: [(6, 0, tag_list)]})

        def _parse_currency(self, post, announcement):
            """ Process currency amounts and currency ids from post params. 

            Convert amount to float format then check existence of currency_id. Check currency_id duplication.
            Then, if there is no error raising in parse process, edit existed currency line and, if it necessary,
            remove or create new currency line.  

            """
            currency_dict = dict()

            currency_pool = self.registry.get('res.currency')
            currency_count = len(currency_pool.search(self.cr, self.uid, [('wallet_currency', '=', True)], 
                                                      context=self.context))
            amount_fromat_error = False
            currency_exist_error = False
            same_currency_error = False
            for index in range(1,currency_count):
                amount_key = 'currency_amount%s' % index
                id_key = 'currency_id%s' % index
                if post.get(amount_key) and post.get(id_key):
                    amount = False
                    try:
                        amount = float(post.get(amount_key))
                    except ValueError:
                        amount_fromat_error = True
                        self.error_param_list.append(amount_key)
                    currency_id = post.get(id_key)
                    currency_id = currency_pool.search(self.cr, self.uid, [('id', '=', currency_id)], limit=1, context=self.context)
                    currency_id = (currency_id[0] if len(currency_id) else False) if type(currency_id) is list else currency_id
                    if currency_id == False:
                        currency_exist_error = True
                        error_param_list.append(id_key)

                    if amount and currency_id:
                        currency_dict.update({currency_id: amount})
        
            post_currency_ids = [post.get('currency_id%s' % _i for _i in range(1, currency_count))]
            for i in range(1, currency_count):
                if post_currency_ids.count(post.get('currency_id%s' % i)) > 1:
                    self.error_param_list.append('currency_id%s' % i)
                    same_currency_error = True

            error_tuple = [
                (amount_fromat_error, 'Amount must be in a float format'),
                (currency_exist_error, 'There is no such currency'),
                (same_currency_error, 'Announcement can\'t have 2 amount with the same currency'),
            ]

            for error in error_tuple:
                if error[0]:
                    self.error_message_list.append(_(error[1]))

            if len(self.error_message_list) == 0:
                currency_line_value = dict()
                new_currency_line_value = list()
                currency_line_to_delete = list()

                currency_ids = announcement.currency_ids
                currency_count_delta = len(currency_ids) - len(currency_dict.keys())
                for i in range(min(len(currency_ids), len(currency_dict.keys()))):
                    currency_id = currency_dict.keys()[i]
                    currency_amount = currency_dict[currency_id]
                    currency_line_value.update({currency_ids[i].id: {
                        'currency_id': currency_id, 
                        'price_unit': currency_amount
                    }})

                if currency_count_delta > 0:
                    for i in range(1, currency_count_delta + 1):
                        currency_line_to_delete.append(currency_ids[len(currency_ids) - i].id)

                elif currency_count_delta < 0:
                    for i in range(1, abs(currency_count_delta) + 1):
                        currency_id = currency_dict.keys()[len(currency_dict.keys()) - i]
                        currency_amount = currency_dict[currency_id]
                        new_currency_line_value.append({
                            'model': 'marketplace.announcement',
                            'res_id': announcement.id, 
                            'currency_id': currency_id, 
                            'price_unit': currency_amount
                        })

                currency_line_pool = self.registry.get('account.wallet.currency.line')
                for currency_line_id in currency_line_value.keys():
                    currency_line_pool.write(self.cr, self.uid, currency_line_id, currency_line_value[currency_line_id], context=self.context)

                for currency_line in new_currency_line_value:
                    currency_line_pool.create(self.cr, self.uid, currency_line, context=self.context)

                for currency_line_id in currency_line_to_delete:
                    currency_line_pool.unlink(self.cr, self.uid, currency_line_id, context=self.context)

        def parse(self, announcement, post):
            """ Process all post params and create vals dict to write to announcement
            """
            self._parse_param(post)
            self._parse_attachment(post, 'document', 'marketplace.announcement', announcement.id)
            self._parse_tags(post, 'tag_ids', 'new_tags', 'tag_ids', 'category_id')
            self._parse_currency(post, announcement)

    def convert_tuple_to_dict(self, cr, uid, tuple_list, context=None):
        """ Convert search name tuple to dict
        """
        res = dict()
        for record in tuple_list:
            res.update({record[0]: record[1]})
        return res

    def get_default_country_state(self, cr, uid, registry, context=None):
        """ Return states of default country
        """
        country_pool = registry.get('res.country')
        state_pool = registry.get('res.country.state')
        usa_id = country_pool.search(cr, uid, [('code','=',DEFAULT_COUNTRY)], context=context)[0]
        res = state_pool.name_search(cr, uid, args=[('country_id', '=', usa_id)], context=context) 
        return self.convert_tuple_to_dict(cr, uid, res, context=context)

    
    def get_all_records(self, cr, uid, registry, model_name, context=None):
        """ Return all records of specified model
        """
        pool = registry.get(model_name)
        args = []
        if model_name == 'res.currency':
            args = [('wallet_currency','=',True)]
        res = pool.name_search(cr, uid, '', args, context=context)
        return self.convert_tuple_to_dict(cr, uid, res, context=context)

    def get_type_dict(self, cr, uid, registry, context=None):
        """ Return all state statuses
        """
        return {
            'offer': 'Offer',
            'want': 'Want',
        }

    def get_vote_types(self, cr, uid, registry, context=None):
        propoistion_obj = registry.get('marketplace.proposition')
        vote_config_obj = registry.get('vote.config.line')
        vote_config_ids = vote_config_obj.search(
            cr, uid,
            [
                ('model', '=', 'community.config.settings'),
                ('target_model.model', '=', propoistion_obj._vote_category_model or propoistion_obj._name)
            ], context=context
        )
        return vote_config_obj.browse(cr, uid, vote_config_ids, context=context)

    def get_attachment_dict(self, cr, uid, registry, announcement, context=None):
        """ Return all attachment of specified announcement
        """
        attach_pool = registry.get('ir.attachment')

        attachment_ids = attach_pool.search(cr, uid, [ ('res_model','=','marketplace.announcement'),
                                                      ('res_id','=', announcement.id),
                                                                                          ] )
        attachment_dict = dict()
        for attachment in attach_pool.browse(cr, uid, attachment_ids):
            # Marketplace picture there is name of picture from announcement.picture field
            if attachment.name != 'Marketplace picture':
                attachment_dict.update({'/marketplace/announcement_detail/%s/attachment/%s' % (announcement.id, attachment.id): attachment.name})
        return attachment_dict

    @http.route('/marketplace/announcement_detail/tags/<int:category_id>/get', type='json', auth="public", website=True)
    def tag_dict_by_category(self, category_id):
        """ JSON route for getting tags of specified category 
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        tag_pool = registry.get('marketplace.tag')
        tag_list = tag_pool.name_search(cr, uid, '', [('category_id', 'child_of', category_id)],
                                        context=context)
        return {'tag_dict': self.convert_tuple_to_dict(cr, uid, tag_list, context=context)}

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/attachment/<model("ir.attachment"):attachment>', type='http', auth="public", website=True)
    def download_attachment(self, announcement, attachment):
        """ Route for download attachment
        """
        if attachment.res_id == announcement.id:
            filecontent = base64.b64decode(attachment.datas)
            if not filecontent:
                response = request.not_found()
            else:
                filename = attachment.name
                response = request.make_response(filecontent,
                [('Content-Type', 'application/octet-stream'),
                 ('Content-Disposition', content_disposition(filename))])
        else:
            response = request.not_found()
        return response

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/attachment/<model("ir.attachment"):attachment>/delete', type='json', auth="public", website=True)
    def delete_attachment(self, announcement, attachment):
        """ Route for process delete attachment request 
        """
        if attachment.res_id == announcement.id:
            cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
            user = registry.get('res.users').browse(cr, uid, uid, context=context)

            if user and announcement.partner_id == user.partner_id or uid == SUPERUSER_ID: 
                registry.get('ir.attachment').unlink(cr, uid, attachment.id, context=context)
                response = {'status': 'ok'}
            else:
                response = {'status': 'error', 'error': 'You can not edit this announcement'}
        else:
            response = {'status': 'error', 'error': 'This attachment is not belong to this announcement'}
        return response

    def _get_my_reply(self):
        return AttrDict({
            'errors': {},
            'quantity': 0.0,
            'description': '',
            'write_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'currency_ids': [AttrDict({
                'id': 0,
                'is_new': True,
                'price_unit': 0.0,
                'currency_id': AttrDict({'id': 0}),
                'subtotal': '',
            })],
            'state': 'draft',
        })

    def _get_my_vote(self, cr, uid, registry, announcement, partner_id, context=None):
        vote_pool = registry.get('vote.vote')
        res = False
        vote_ids = vote_pool.search(cr, uid, [
            ('partner_id', '=', partner_id),
            ('model', '=', 'marketplace.announcement'),
            ('res_id', '=', announcement.id)
        ], context=context)
        if vote_ids:
            res = vote_pool.browse(cr, uid, vote_ids[0], context=context)
        else:
            res = AttrDict({
                'comment': '',
                'line_ids': [AttrDict({
                    'type_id': vote_type.name,
                    'vote': '0',
                }) for vote_type in self.get_vote_types(cr, uid, registry, context)]
            })
        return res

    def _parse_vote(self, data):
        res = {
            'comment': data.get('vote_comment'),
            'line_ids': []
        }
        vote_lines = []
        for key, val in data.iteritems():
            if key.startswith('vote_lines'):
                    type_id = re.search('vote_lines\[(\d+)\]\[vote]', key)
                    if type_id:
                        type_id = int(type_id.group(1))
                        vote_lines.append(AttrDict({
                            'type_id': AttrDict({'id': type_id}),
                            'vote': val
                        }))
        res['line_ids'] = vote_lines
        return AttrDict(res)

    def _validate_reply(self, data, id=None):
        res = {
            'id': id,
            'quantity': data.get('quantity'),
            'description': data.get('description'),
            'write_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'currency_ids': [],
        }
        currency_ids = {'existing': {}, 'new': {}}
        currencies_uniq = []
        errors = {}
        for key, val in data.iteritems():
            if key.startswith('currency_ids'):
                for f in ['currency_id', 'price_unit']:
                    for t in ['new', 'existing']:
                        curr_number = re.search('currency_ids\[%s\]\[(\d+)\]\[%s\]' % (t, f), key)
                        if curr_number:
                            curr_number = int(curr_number.group(1))
                            if f == 'currency_id':
                                if val in currencies_uniq:
                                    errors['currency_ids'] = _('Currency cannot have multiple unit prices')
                                else:
                                    currencies_uniq.append(val)
                            if not curr_number in currency_ids[t]:
                                currency_ids[t][curr_number] = {
                                    'id': curr_number,
                                    f: AttrDict({'id': val}) if f == 'currency_id' else val,
                                    'is_new': True if t == 'new' else False,
                                    'subtotal': '',
                                }
                            else:
                                currency_ids[t][curr_number].update({f: AttrDict({'id': val}) if f == 'currency_id' else val})
        res['currency_ids'] = [AttrDict(line) for key in ['existing', 'new'] for line in currency_ids[key].values()]
        if not data['quantity']:
            errors.update({'quantity': _('Please input quantity')})
        else:
            try:
                float(data['quantity'])
            except:
                errors.update({'quantity': _('Quantity should be a float number e.g. 12.99')})
        if not 'currency_ids' in errors:
            for line in res['currency_ids']:
                try:
                    float(line.price_unit)
                except:
                    errors.update({'currency_ids': _('Unit price should be a float number e.g. 12.99')})
                    break
        res['errors'] = errors
        return AttrDict(res)

    def _save_reply(self, cr, uid, registry, announcement, reply, id=None, context=None):
        proposition_pool = registry.get('marketplace.proposition')
        vals = {
            'quantity': reply.quantity,
            'write_date': reply.write_date,
            'description': reply.description,
            'announcement_id': announcement.id,
            'currency_ids': [],
        }
        currency_ids = []
        # Collect vlues for o2m field currency_ids to create and write
        for line in reply.currency_ids:
            vals['currency_ids'].append((0 if getattr(line, 'is_new', False) else 1,
                                         0 if getattr(line, 'is_new', False) else line.id,
                                         {
                                            'model': 'account.wallet.transaction',
                                            'price_unit': line.price_unit,
                                            'currency_id': line.currency_id.id,
                                         })
            )
        if id:
            # Collect vlues for o2m field currency_ids to delete
            proposition = proposition_pool.browse(cr, uid, id, context=context)
            if not proposition.is_sender:
                return False
            currency_to_del_ids = list(set([c.id for c in proposition.currency_ids]) - \
                                set([c.id for c in reply.currency_ids if not getattr(c, 'is_new', False)]))
            for c_id in currency_to_del_ids:
                vals['currency_ids'].insert(0, (2, c_id))
            # Update proposition
            proposition_pool.write(cr, uid, [id], vals, context=context)
        else:
            # Create and publish proposition
            id = proposition_pool.create(cr, uid, vals, context=context)
            # workflow.trg_validate(uid, 'marketplace.proposition', id, 'proposition_draft_open', cr)

    def _save_vote(self, cr, uid, registry, announcement, my_vote, partner_id, context=None):
        vote_pool = registry.get('vote.vote')
        ids = vote_pool.search(cr, uid, [
            ('partner_id', '=', partner_id),
            ('model', '=', 'marketplace.announcement'),
            ('res_id', '=', announcement.id)
        ], context=context)
        vals = {
            'model': 'marketplace.announcement',
            'res_id': announcement.id,
            'partner_id': partner_id,
            'comment': my_vote.comment,
            'line_ids': [(0,0,{
                'type_id': int(line.type_id.id),
                'vote': line.vote,
            }) for line in my_vote.line_ids if line.type_id.id]
        }
        if ids:
            vals['line_ids'].insert(0, (6, 0, []))
            vote_pool.write(cr, uid, ids, vals, context=context)
        else:
            vote_pool.create(cr, uid, vals, context=context)
        return True

    def _get_view_announcement_dict(self, cr, uid, registry, announcement, my_reply=None, 
                                    updated_reply=None, updated_reply_saved=False, my_vote=None, context=None):
        """ Return dict of values needed to view announcement template
        """
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        date_format = get_date_format(cr, uid, context)
        return {
            'announcement':announcement,
            'author': announcement.partner_id,
            'vote_list': dict([(v.partner_id.id, v) for v in announcement.vote_vote_ids]),
            'my_reply': my_reply or self._get_my_reply(),
            'updated_reply': updated_reply,
            'my_vote': my_vote or self._get_my_vote(cr, uid, request.registry, announcement, 
                                                    user.partner_id.id, context=context),
            'type_dict': self.get_type_dict(cr, uid, request.registry, context=context),
            'attachment_dict': self.get_attachment_dict(cr, uid, request.registry, announcement, context=context),
            'date_from': '' if not announcement.date_from else \
                datetime.strptime(announcement.date_from, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format),
            'date_to': '' if not announcement.date_to else \
                datetime.strptime(announcement.date_to, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format),
            'getattr': getattr,
            'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
            'format_date': format_date,
            'vote_types': self.get_vote_types(cr, uid, registry, context=context),
            'allow_reply': len([1 for p in announcement.proposition_ids 
                if p.is_sender and p.state in ('draft', 'open')]) == 0,
            'updated_reply_saved': updated_reply_saved
        }

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>', type='http', auth="public", website=True)
    def view_announcement(self, announcement, **post):
        """ Route for process view announcement request
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)

        my_reply = self._get_my_reply()
        updated_reply = None
        my_vote = None
        updated_reply_saved = False
        if 'make_reply' in post:
            my_reply = self._validate_reply(post)
            if not my_reply.errors:
                self._save_reply(cr, uid, registry, announcement, my_reply, id=None, context=context)
                my_reply = None
                # my_vote = self._parse_vote(post)
                # self._save_vote(cr, uid, registry, announcement, my_vote, user.partner_id.id, context=context)
                # my_vote = None
        elif 'update_reply' in post:
            updated_reply = self._validate_reply(post, id=int(post.get('update_reply')))
            if not updated_reply.errors:
                self._save_reply(cr, uid, registry, announcement, updated_reply, 
                                 id=int(post.get('update_reply')), context=context)
                updated_reply = None
                updated_reply_saved = int(post.get('update_reply'))
        web_page = http.request.website.render('website_project_weezer.view_announcement', 
            self._get_view_announcement_dict(cr, uid, registry, announcement, my_reply,
                                             updated_reply, updated_reply_saved, my_vote, context=context))
        return web_page

    def _get_edit_announcement_dict(self, cr, uid, registry, announcement, context=None):
        """ Return dict of values needed to edit announcement template
        """
        date_format = get_date_format(cr, uid, context)
        res = {
            'announcement':announcement,
            'announcement_picture': ('data:image/jpeg;base64,%s' % announcement.picture)
                                                            if announcement.picture else '/web/static/src/img/placeholder.png',
            'announcement_group_ids': [group.id for group in announcement.context_group_ids],
            'author': announcement.partner_id,
            'us_state_dict': self.get_default_country_state(cr, uid, request.registry, context=context),
            'country_dict': self.get_all_records(cr, uid, request.registry, 'res.country', context=context),
            'type_dict': self.get_type_dict(cr, uid, request.registry, context=context),
            'category_dict': self.get_all_records(cr, uid, request.registry, \
                                                        'marketplace.announcement.category', context=context),
            'currency_dict': self.get_all_records(cr, uid, request.registry, 'res.currency', context=context),
            'group_dict': self.get_all_records(cr, uid, request.registry, 'mail.group', context=context),
            'attachment_dict': self.get_attachment_dict(cr, uid, request.registry, announcement, context=context),
            'tag_dict': self.get_all_records(cr, uid, request.registry, 'marketplace.tag', context=context),
            'uom_dict': self.get_all_records(cr, uid, registry, 'product.uom', context=context),
            'date_placeholder': date_format.replace('%d','DD').replace('%m','MM').replace('%Y','YYYY'),
            'date_from': announcement.date_from,
            'date_to': announcement.date_to,
            'format_date': format_date,
            'vote_list': dict([(v.partner_id.id, v) for v in announcement.vote_vote_ids]),
        }
        if type(announcement) != AttrDict:
            res.update({
                'date_from': '' if not announcement.date_from else \
                    datetime.strptime(announcement.date_from, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format),
                'date_to': '' if not announcement.date_to else \
                    datetime.strptime(announcement.date_to, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format),
            })
        return res

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/edit', type='http', auth="public", website=True)
    def edit_announcement(self, announcement):
        """ Route for process edit announcement request
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        if user and announcement.partner_id.id == user.partner_id.id or uid == SUPERUSER_ID: 
            response = http.request.website.render('website_project_weezer.edit_announcement', 
                self._get_edit_announcement_dict(cr, uid, registry, announcement, context=context))
        else:
            response = request.not_found()
        return response

    def _get_announcement_from_post(self, post, announcement):
        res = dict()
        simple = [
            ('name', 'title'),
            ('description', 'description'),
            ('street', 'street'),
            ('street2', 'street2'),
            ('zip', 'zip'),
            ('city', 'city'),
            ('quantity', 'qty'),
            ('infinite_qty', 'unlimited'),
            ('new_tags', 'new_tags'),
            ('date_from', 'date_from'),
            ('date_to', 'date_to'),
            ('state', 'state'),
            ('type', 'type'),
        ]
        for param_val in simple:
            val, param = param_val
            res.update({val: post.get(param)})

        m2o = [
            ('category_id', 'category_id'),
            ('state_id', 'state_id'),
            ('country_id', 'country_id'),
            ('uom_id', 'uom_id'),
        ]
        for param_val in m2o:
            val, param = param_val
            value = post.get(param)
            if value:
                if value != 'None':
                    int_id = int(value)
                else:
                    int_id = False
                value = AttrDict({'id': int_id})
            res.update({val: value})

        o2m = [
            ('tag_ids', 'tag_ids'),
            ('context_group_ids', 'groups'),
        ]
        for param_val in o2m:    
            val, param = param_val    
            list_ids = None
            if post.get(param):
                list_ids = list()
                id_list = post.get(param)
                for id_value in id_list:
                    if id_value != 'None':
                        list_ids.append(AttrDict({'id': int(id_value)}))
            res.update({val: list_ids})
        currency_ids = list()
        for i in range(1,4):
            amount = post.get('currency_amount%s' % i)
            currency = post.get('currency_id%s' % i)
            if amount:
                currency_ids.append(AttrDict({'price_unit': amount, 'currency_id': AttrDict({'id': int(currency)})}))
        res.update({
            'id': announcement.id,
            'currency_ids': currency_ids,
            'partner_id': announcement.partner_id,
            'picture': announcement.picture,
            'quantity_available': announcement.quantity_available,
            'vote_vote_ids': announcement.vote_vote_ids,
            'proposition_ids': announcement.proposition_ids,
        })
        return AttrDict(res)

    def _parse_and_save_announcement(self, cr, uid, registry, announcement, post, context=None):
        """ Parse all post params and render to the appropriate page

        Parse post params. In case, if some values was no valid, rollback all changes in cache, and render
        new announcement or edit announcement page. In case, if all values was successfully parsed - write vals dict
        to announcement and render view announcement page. 

        """
        parser = self.save_annnouncement_parser(cr, uid, registry, context=context)
        parser.parse(announcement, post)

        if len(parser.error_param_list) > 0:
            edited_announcement = self._get_announcement_from_post(post, announcement)
            response = self._get_edit_announcement_dict(cr, uid, registry, edited_announcement, context=context)
            template_id = 'website_project_weezer.edit_announcement'
            response.update({'error_param_list': parser.error_param_list, 'error_message_list': parser.error_message_list})
            cr.rollback()
        else:
            res_id = registry.get('marketplace.announcement').write(cr, uid, announcement.id, parser.vals, context=context)
            announcement = registry.get('marketplace.announcement').browse(cr, uid, announcement.id, context=context)
            response = self._get_view_announcement_dict(cr, uid, registry, announcement, context=context)
            response.update({'success_message_list': [_('Announcement successfully saved')]})
            template_id = 'website_project_weezer.view_announcement'
        
        return {'template_id': template_id, 'response': response}

    def _prepare_save_announcemet_param(self, cr, uid, request, post):
        """ Update post dict with params that openerp wrongly process
        """
        if post.get('tag_ids'):
            post['tag_ids'] = request.httprequest.form.getlist('tag_ids')
        if post.get('new_tags'):
            post['new_tags'] = request.httprequest.form.getlist('new_tags')
        if post.get('groups'):
            post['groups'] = request.httprequest.form.getlist('groups')

    @http.route('/marketplace/announcement_detail/<model("marketplace.announcement"):announcement>/save', type='http', auth="user", website=True)
    def save_announcement(self, announcement, **post):
        """ Route to process save announcement request
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        if user and announcement.partner_id == user.partner_id or uid == SUPERUSER_ID:  
            self._prepare_save_announcemet_param(cr, uid, request, post)
            res = self._parse_and_save_announcement(cr, uid, registry, announcement, post, context=context)
            response = http.request.website.render(res['template_id'], res['response'])
        else:
            response = request.not_found()
        return response

    def _get_new_announcement_dict(self, cr, uid, registry, partner, context=None):
        """ Return dict of values needed to new announcement template
        """
        return {
            'author': partner,
            'us_state_dict': self.get_default_country_state(cr, uid, registry, context=context),
            'country_dict': self.get_all_records(cr, uid, registry, 'res.country', context=context),
            'type_dict': self.get_type_dict(cr, uid, request.registry, context=context),
            'category_dict': self.get_all_records(cr, uid, registry, \
                                                            'marketplace.announcement.category', context=context),
            'currency_dict': self.get_all_records(cr, uid, registry, 'res.currency', context=context),
            'group_dict': self.get_all_records(cr, uid, registry, 'mail.group', context=context),
            'uom_dict': self.get_all_records(cr, uid, registry, 'product.uom', context=context),
            'date_placeholder': get_date_format(cr, uid, context) \
                .replace('%d','DD').replace('%m','MM').replace('%Y','YYYY'),
        }

    @http.route('/marketplace/announcement_detail/new', type='http', auth="public", website=True)
    def new_announcement(self):
        """ Route to process create new announcement request
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        if user and user.partner_id:  
            response = http.request.website.render('website_project_weezer.new_announcement', 
                self._get_new_announcement_dict(cr, uid, registry, user.partner_id, context=context))
        else:
            response = request.not_found()

        return response

    @http.route('/marketplace/announcement_detail/new/save', type='http', auth="user", website=True)
    def save_new_announcement(self, **post):
        """ Route to process save new announcement request
        """
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user = registry.get('res.users').browse(cr, uid, uid, context=context)
        self._prepare_save_announcemet_param(cr, uid, request, post)
        announcement = registry.get('marketplace.announcement').create(cr, uid, {
            'name': '', 
            'partner_id': user.partner_id.id,
        }, context=context)
        announcement = registry.get('marketplace.announcement').browse(cr, uid, announcement, context=context)
        if not context:
            context = dict()
        context.update({'from_new_announcement': True})
        res = self._parse_and_save_announcement(cr, uid, registry, announcement, post, context=context)
        response = http.request.website.render(res['template_id'], res['response'])
        return response

    @http.route('/marketplace/announcement/<model("marketplace.announcement"):announcement>/<any("draft_cancel","draft_open","open_cancel","open_done", "done_open","cancel_draft"):state>', type='http', auth="user", website=True)
    def announcement_change_state(self, announcement, state):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        state_signal = {
            'draft_cancel': 'announcement_draft_cancel',
            'draft_open': 'announcement_draft_open',
            'open_cancel': 'announcement_open_cancel',
            'open_done': 'announcement_open_done',
        }
        if state in state_signal.keys():
            workflow.trg_validate(uid, 'marketplace.announcement', announcement.id,
                                  state_signal.get(state), cr)
        if state in ['cancel_draft', 'done_open']:
            registry.get('marketplace.announcement').reset_workflow(cr, uid, [announcement.id])
        return self.view_announcement(announcement)

    @http.route('/marketplace/reply/<model("marketplace.proposition"):proposition>/<any("draft_cancel","draft_open","open_cancel","accept","reject","reject_draft","accepted_cancel","invoice","invoiced_cancel","pay","confirm","refund","confirmrefund_paid","confirmrefund_cancel","cancel_draft"):state>', type='http', auth="user", website=True)
    def proposition_change_state(self, proposition, state):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        state_signal = {
            'draft_cancel': 'proposition_draft_cancel',
            'draft_open': 'proposition_draft_open',
            'open_cancel': 'proposition_open_cancel',
            'accept': 'proposition_open_accepted',
            'reject': 'proposition_open_rejected',
            'accepted_cancel': 'proposition_accepted_cancel',
            'invoice': 'proposition_accepted_invoiced',
            'invoiced_cancel': 'proposition_invoiced_cancel',
            'confirmrefund_paid': 'proposition_confirm_refund_paid',
            'confirmrefund_cancel': 'proposition_confirm_refund_cancel',
        }
        if state in state_signal.keys():
            workflow.trg_validate(uid, 'marketplace.proposition', proposition.id, 
                                  state_signal.get(state), cr)

        if state == 'pay':
            registry.get('marketplace.proposition').pay(cr, uid, [proposition.id])
        if state == 'confirm':
            registry.get('marketplace.proposition').confirm(cr, uid, [proposition.id])
        if state in ['cancel_draft', 'reject_draft', 'refund']:
            registry.get('marketplace.proposition').reset_workflow(cr, uid, [proposition.id])

        user = registry.get('res.users').browse(cr, uid, uid, context=context)

        return self.view_announcement(proposition.announcement_id)

announcement_controller()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
