openerp.website.theme.views['website_project_weezer.homepage'] = openerp.Class.extend({

    init: function() {

    	var self = this;

      	// Set a callback to run when the Google Visualization API is loaded.
      	google.setOnLoadCallback(self.drawChart);

    },

    drawChart: function() {

	    // Create the data table.
	    var data = new google.visualization.DataTable();
	    data.addColumn('string', 'Name');
	    data.addColumn('number', 'Count');
	    data.addRows([
	      ['Part 1', 5],
	      ['Part 2', 2],
	      ['Part 3', 6]
	    ]);

	    // Set chart options
	    var options = {'width':400,
	                   'height':350};

	    // Instantiate and draw our chart, passing in some options.
	    var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
	    chart.draw(data, options);
	}

});