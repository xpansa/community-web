$(document).ready(function(){
     $('.selectpicker').selectpicker();
     $(".date-picker").datepicker();
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