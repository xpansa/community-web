$(document).ready(function(){
    $('.selectpicker').selectpicker();
    $('.date-picker').datepicker();
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