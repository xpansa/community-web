openerp.website.theme.views['website_project_weezer.edit_announcement'] = openerp.Class.extend({

    init: function() {

	    $('.remove-attachment').on('click',function(e){
	        e.preventDefault();

	        var self = $(this);

	        openerp.jsonRpc($(this).attr('href')+'/delete', 'call', {})
	            .then(function (data) {
	                self.parent().remove();
	            });
	    });

    }
});