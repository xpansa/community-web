openerp.website.theme.views['website_project_weezer.view_announcement'] = openerp.Class.extend({

    init: function() {

	    $('.btn-announcement-reply').click( function(e) {
	        e.preventDefault();
	        $('#replycta').fadeOut(300, function() {
	            $(this).addClass('hidden');         
	            $('#replyform').hide().removeClass('hidden').slideDown(300, function() {
	                $('body').animate({scrollTop:$('#replysection').position().top}, 750);
	            });
	        });
	    });

    }
});