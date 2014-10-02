openerp.website.theme.views['website_project_weezer.member_list_view'] = openerp.Class.extend({

    init: function() {

        // MEMBERS WRAP
	    var divs = $("#members-list > .member");
	    for(var i = 0; i < divs.length; i+=2) {
	      divs.slice(i, i+2).wrapAll("<div class='row'></div>");
	    }

    }
});