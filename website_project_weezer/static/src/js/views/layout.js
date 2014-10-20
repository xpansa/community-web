openerp.website.theme.views['layout'] = openerp.Class.extend({

    init: function() {

        var self = this;

        var skill_category_cache = {};
        var skill_category_new_counter = 1;
        $('.skill_category_block input').each(function(i, el) {
            el_number = parseInt(el.name.match(/\d+/)[0]);
            skill_category_new_counter = el_number > skill_category_new_counter ? el_number : skill_category_new_counter;
        });
        var skill_tag_cache = {};
        var skill_tag_new_counter = 1;
        $('.skill_tag_block input').each(function(i, el) {
            el_number = parseInt(el.name.match(/\d+/)[0]);
            skill_tag_new_counter = el_number > skill_tag_new_counter ? el_number : skill_tag_new_counter;
        });
        var limit_new_counter = 1;
        $('.limit_block input').each(function(i, el) {
            el_number = parseInt(el.name.match(/\d+/)[0]);
            limit_new_counter = el_number > limit_new_counter ? el_number : limit_new_counter;
        });
        var balance_new_counter = 1;
        $('.balance_block input').each(function(i, el) {
            el_number = parseInt(el.name.match(/\d+/)[0]);
            balance_new_counter = el_number > balance_new_counter ? el_number : balance_new_counter;
        });
        self.bind_autocomplete('.skill_category', '/marketplace/profile/get_skills', skill_category_cache);
        self.bind_autocomplete('.skill_tag', '/marketplace/profile/get_interests', skill_tag_cache);

        $('.selectpicker').selectpicker();

        var dFormat = openerp._t.database.parameters.date_format;
        JQueryDateFormat = dFormat.replace('%m', 'mm').replace('%d', 'dd').replace('%Y', 'yy');

        $('.date-picker').datepicker({
            dateFormat: JQueryDateFormat
        });

        $('.dynamic-list').dynamiclist({
            'addCallbackFn': function(el) {
                el = el[0]
                if ($(el).hasClass('skill_category_block')) {
                    $(el).find('input').attr('name', 'skills[new][' + skill_category_new_counter + ']');
                    self.bind_autocomplete($(el).find('input'), '/marketplace/profile/get_skills', skill_category_cache);
                    skill_category_new_counter++;
                } else if ($(el).hasClass('skill_tag_block')) {
                    $(el).find('input').attr('name', 'tags[new][' + skill_tag_new_counter + ']');
                    self.bind_autocomplete($(el).find('input'), '/marketplace/profile/get_interests', skill_tag_cache);
                    skill_tag_new_counter++;
                } else if ($(el).hasClass('limit_block')) {
                    $(el).find('input.limit_min_input').attr('name', 'limits[new][' + limit_new_counter + '][min]');
                    $(el).find('input.limit_max_input').attr('name', 'limits[new][' + limit_new_counter + '][max]');
                    $(el).find('select').attr('name', 'limits[new][' + limit_new_counter + '][currency]');
                    limit_new_counter++;
                } else if ($(el).hasClass('balance_block')) {
                    $(el).find('input').attr('name', 'balances[new][' + balance_new_counter + '][amount]');
                    $(el).find('select').attr('name', 'balances[new][' + balance_new_counter + '][currency]');
                    balance_new_counter++;
                }
            }
        });

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