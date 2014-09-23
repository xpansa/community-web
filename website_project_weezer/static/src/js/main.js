
function bind_autocomplete(selector, url, cache) {
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
        }
    });
}

$(document).ready(function(){
    $('.selectpicker').selectpicker();
    var dFormat = openerp._t.database.parameters.date_format;
    JQueryDateFormat = dFormat.replace('%m','mm').replace('%d','dd').replace('%Y','yy')
    $('.date-picker').datepicker({dateFormat: JQueryDateFormat});
    $('.dynamic-list').dynamiclist({'addCallbackFn': function(el) {
            el = el[0]
            if($(el).hasClass('skill_category_block'))
                bind_autocomplete($(el).find('input'), '/marketplace/profile/get_skills', skill_category_cache)
            else if($(el).hasClass('skill_tag_block'))
                bind_autocomplete($(el).find('input'), '/marketplace/profile/get_interests', skill_tag_cache)
        }
    });
    $('.scrollable').tinyscrollbar({ thumbSize: 100 });
    var offset = 4;
    var limit = 4;
    $('.btn-simulateload').click( function(e) {
        e.preventDefault();

        var self = $(this);
        self.addClass('loading');
        self.addClass('disabled');

        var URL = "/marketplace/search/load_more";
        if(window.location.search)
            URL += window.location.search + '&'
        else
            URL += '?'

        $.ajax(URL+'load_wants=1'+'&offset='+offset, {'method': 'GET'})
            .then(function (data) {
                console.log(data);
                $('.mp_search_wants').append(data);
                $.ajax(URL+'load_offers=1'+'&offset='+offset, {'method': 'GET'})
                .then(function (data) {
                    $('.mp_search_offers').append(data);
                    self.removeClass('loading');
                    self.removeClass('disabled');
                    offset += 4;
                    $('div.mp_search').tinyscrollbar().data("plugin_tinyscrollbar").update('bottom');
                });
            });
    });

    var skill_category_cache = {};
    var skill_tag_cache = {};
    bind_autocomplete('.skill_category', '/marketplace/profile/get_skills', skill_category_cache);
    bind_autocomplete('.skill_tag', '/marketplace/profile/get_interests', skill_tag_cache);
});


/* 
THIS IS THE MAIN KICKOFF JS FILE FOR VIEW SCRIPTS
THIS FILE MUST BE INCLUDED AFTER ALL THE VIEW SCTIPTS
TO ENABLE THE VIEW SCRIPT MAKE SURE:
    - THE <body> HAS ATTIBUTE data-view-xmlid WITH THE VIEW ID (ex.: <body data-view-xmlid="website.homepage">...</body>)
	- THE VIEW IS IN THE openerp.website.theme.views ARRAY WITH THE VIEW ID AS KEY (ex.: openerp.website.theme.views['website.homepage'])
*/

/*if (typeof openerp.website.theme.views.layout === "function") openerp.website.theme.views.layout = new openerp.website.theme.views.layout();
if (typeof openerp.website.theme.views[$('body').attr('data-view-xmlid')] === "function") openerp.website.theme.views[$('body').attr('data-view-xmlid')] = new openerp.website.theme.views[$('body').attr('data-view-xmlid')]();
*/