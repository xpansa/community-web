openerp.website.theme.views['layout'] = openerp.Class.extend({

    init: function() {

        var self = this;

        function dynamic_element(selector, url) {
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
        }

        dynamic_elements = {
            'skill_category': new dynamic_element('.skill_category_block', '/marketplace/profile/get_skills'),
            'skill_tag': new dynamic_element('.skill_tag_block', '/marketplace/profile/get_interests'),
            'limit': new dynamic_element('.limit_block'),
            'balance': new dynamic_element('.balance_block'),
            'proposition_price': new dynamic_element('.proposition_price_block'),
        }

        for (prop in dynamic_elements) {
            dynamic_elements[prop].init();
        }

        self.bind_autocomplete('.skill_category', '/marketplace/profile/get_skills', dynamic_elements.skill_category.cache);
        self.bind_autocomplete('.skill_tag', '/marketplace/profile/get_interests', dynamic_elements.skill_tag.cache);

        $('.selectpicker').selectpicker();

        var dFormat = openerp._t.database.parameters.date_format;
        JQueryDateFormat = dFormat.replace('%m','mm').replace('%d','dd').replace('%Y','yy');

        $('.date-picker').datepicker({dateFormat: JQueryDateFormat});

        $('.dynamic-list').dynamiclist({'addCallbackFn': function(el) {
            // User has clicked "Add new element"
            // Apply uniq name (taken from counter property)
            // Bind autocomplete if nedeed
            el = el[0];
            for (prop in dynamic_elements) {
                if ($(el).hasClass(dynamic_elements[prop].selector.replace('.',''))) {
                    $(el).find('input,select').each(function(i, input){
                        var name = input.name.replace('existing', 'new');
                        $(input).attr('name', name.replace(/\d+/, dynamic_elements[prop].counter));
                    });        
                    dynamic_elements[prop].counter++;
                    if (dynamic_elements[prop].autocomplete_url) {
                        self.bind_autocomplete($(el).find('input'), dynamic_elements[prop].autocomplete_url, dynamic_elements[prop].cache);        
                    }
                }
            }
        }});

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
        $(document).on('fileselect', 'input[type="file"]', function(e, files){
            var allFiles = '';
            $.each(files,function(k,v){
                allFiles += '<div class="label label-warning margin-right-10">'+v+'</div>';
            });
            $(e.target).parent().next('.files-to-upload').append(allFiles);
        });

        // DYNAMIC ELEMENT POSSITIONS ON APPEAR
        $('[data-appear-element]').each(function(){
            var element = $(this);

            $(element.attr('data-appear-element')).on('appear', function() {
                element.addClass('appeared');
            }).appear();

            $(element.attr('data-disappear-element')).on('disappear', function() {
                element.removeClass('appeared');
            }).appear();
        });

        $('.date-picker').keypress(function(e){
            e.preventDefault();
        });
        
    },
    
    bind_autocomplete: function(selector, url, cache) {

        $(selector).autocomplete({
            minLength: 2,
            source: function( request, response ) {
                var term = request.term;
                if ( term in cache ) {
                    response( cache[ term ] );
                    return;
                }
                openerp.jsonRpc(url, 'call', {
                    'term': term,
                    }).then(function (data) {
                        cache[ term ] = data;
                        response( data );
                    });
            },
            select: function(event, ui) {
                if($(event.target).hasClass('skill_category'))
                    $(event.target).attr('name', 'skills[existing][' + ui.item.id + ']');
                else if($(event.target).hasClass('skill_tag'))
                    $(event.target).attr('name', 'tags[existing][' + ui.item.id + ']');
            }
        });

    }
});