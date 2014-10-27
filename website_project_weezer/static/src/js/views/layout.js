openerp.website.theme.views['layout'] = openerp.Class.extend({

    dynamic_elements: {},

    init: function() {

        var self = this;

        self.dynamic_elements = {
            'skill_category': new self.dynamic_element('.skill_category_block', '/marketplace/profile/get_skills'),
            'skill_tag': new self.dynamic_element('.skill_tag_block', '/marketplace/profile/get_interests'),
            'limit': new self.dynamic_element('.limit_block'),
            'balance': new self.dynamic_element('.balance_block'),
            'proposition_price': new self.dynamic_element('.proposition_price_block'),
            'vote': new self.dynamic_element('.vote_block'),
        }

        for (prop in self.dynamic_elements) {
            self.dynamic_elements[prop].init();
        }

        self.bind_autocomplete('.skill_category', '/marketplace/profile/get_skills', self.dynamic_elements.skill_category.cache);
        self.bind_autocomplete('.skill_tag', '/marketplace/profile/get_interests', self.dynamic_elements.skill_tag.cache);

        $('.selectpicker').selectpicker();

        var dFormat = openerp._t.database.parameters.date_format;
        JQueryDateFormat = dFormat.replace('%m', 'mm').replace('%d', 'dd').replace('%Y', 'yy');

        $('.date-picker').datepicker({
            dateFormat: JQueryDateFormat
        });

        self.bind_dynamiclist($('.dynamic-list'));

        // FILESELECT CUSTOM EVENT
        $(document).on('change', '.btn-file :file', function(e) {
            var input = $(this);
            var files = [];
            for (var i = 0; i < input[0].files.length; ++i) {
                var name = input[0].files.item(i).name;
                files.push(name);
            }
            input.trigger('fileselect', [files]);
        });

        // FILESELECT
        $(document).on('fileselect', 'input[type="file"]', function(e, files) {
            var allFiles = '';
            $.each(files, function(k, v) {
                allFiles += '<div class="label label-warning margin-right-10">' + v + '</div>';
            });
            var target = $(e.target);
            var multiple = target.attr('multiple');
            var container = target.parent().next('.files-to-upload');
            if (typeof multiple == typeof undefined || multiple == false) container.empty();
            container.append(allFiles);
        });

        // DYNAMIC ELEMENT POSSITIONS ON APPEAR
        $('[data-appear-element]').each(function() {
            var element = $(this);

            $(element.attr('data-appear-element')).on('appear', function() {
                element.addClass('appeared');
            }).appear();

            $(element.attr('data-disappear-element')).on('disappear', function() {
                element.removeClass('appeared');
            }).appear();
        });

        $('.date-picker').keypress(function(e) {
            e.preventDefault();
        });

    },

    dynamic_element: function(selector, url) {
        this.counter = 1;
        this.cache = {};
        this.selector = selector; //Should be .classname
        this.autocomplete_url = url;
        this.init = function() {
            // set digital part of name to te uniq valus e.g. limit[new][12][currency]
            $(this.selector + ' input').each(function(i, el){
                el_number = el.name.match(/\d+/);
                if (el_number) {
                    el_number = parseInt(el_number[0]);
                    this.counter = el_number > this.counter ? el_number : this.counter;
                }
            });
        }
    },

    bind_dynamiclist: function(selector) {
        var self = this;

        selector.dynamiclist({
            'addCallbackFn': function(el) {
                // User has clicked "Add new element"
                // Apply uniq name (taken from counter property)
                // Bind autocomplete if nedeed
                el = el[0];
                for (prop in self.dynamic_elements) {
                    if ($(el).hasClass(self.dynamic_elements[prop].selector.replace('.', ''))) {
                        $(el).find('input,select').each(function(i, input) {
                            var name = input.name.replace('existing', 'new');
                            $(input).attr('name', name.replace(/\d+/, self.dynamic_elements[prop].counter));
                        });
                        self.dynamic_elements[prop].counter++;
                        if (self.dynamic_elements[prop].autocomplete_url) {
                            self.bind_autocomplete($(el).find('input'), self.dynamic_elements[prop].autocomplete_url, self.dynamic_elements[prop].cache);
                        }
                    }
                }
                $(el).find('.bootstrap-select').remove();
                $(el).find('.selectpicker').selectpicker();
            }
        });
    },

    bind_autocomplete: function(selector, url, cache) {

        $(selector).autocomplete({
            minLength: 2,
            source: function(request, response) {
                var term = request.term;
                if (term in cache) {
                    response(cache[term]);
                    return;
                }
                openerp.jsonRpc(url, 'call', {
                    'term': term,
                }).then(function(data) {
                    cache[term] = data;
                    response(data);
                });
            },
            select: function(event, ui) {
                if ($(event.target).hasClass('skill_category'))
                    $(event.target).attr('name', 'skills[existing][' + ui.item.id + ']');
                else if ($(event.target).hasClass('skill_tag'))
                    $(event.target).attr('name', 'tags[existing][' + ui.item.id + ']');
            }
        });

    }
});