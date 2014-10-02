$(document).ready(function(){
    if (typeof openerp.website.theme.views.layout === "function") openerp.website.theme.views.layout = new openerp.website.theme.views.layout();
    if (typeof openerp.website.theme.views[$('#xmlid').attr('data-xmlid')] === "function") openerp.website.theme.views[$('#xmlid').attr('data-xmlid')] = new openerp.website.theme.views[$('#xmlid').attr('data-xmlid')]();
});