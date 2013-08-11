$(function() {
    var config = {
	url :         'http://localhost:8080/solr',
	core:         'scalpo',
	rows:          50
    };

    var semaphore = false;

    $('#select').click(function() { query(0) });
    
    $('#pagination').on('click', 'a', function() {
	query(+$(this).data('start'));
	return false;
    });

    function query (start) {
	if (!semaphore) {
	    semaphore = true;
	    $('#query, #select').prop('disabled', true);

	    $.ajax({
		url: config.url + '/' + config.core + '/select',
		data: {
		    wt   : 'json',
		    q    : $('#query').val(),
		    start: start,
		    rows : config.rows
		},
		dataType: 'jsonp',
		jsonp: 'json.wrf',
		success: function(data) {
		    if (data.responseHeader.status == 0) {
			tot = data.response.numFound;
			num = data.response.docs.length;
			$('#reshead').text('Found ' +  tot + 
					   ' documents in ' + data.responseHeader.QTime + 'ms, ' +
					   'showing results ' + start + '-' + (start + num) + '.');
			
			var $pag = $('#pagination').html('Go to page: ')
			for (var i = 0 ; i <= tot ; i += config.rows) {
			    $pag.append('<a href="#" data-start="' + i + '">' + i + '-' + 
					Math.min(i + config.rows, tot) + '</a> ');
			}

			$('#results').html(
			    $.map(data.response.docs, function(doc, pos) {
				return result(pos, doc, data.highlighting)
			    }));
		    } else {
			$('#results').html('Error: ' + data.error.code);
		    }
		},
		complete: function() {
		    $('#query, #select').prop('disabled', false);
		    semaphore = false;
		}
	    });
	}
    }

    function result(pos, doc, highlight) {
	var result = $('<div id="result-' + pos + '" class="result">');

	var fulltext = $('<p class="fulltext">' + doc.text.join(' ') + '</p>')
	    .click(function() { $(this).hide(); });

	var preview = $('<span class="preview">preview</span>')
	    .click(function() { fulltext.show(); });

	var link = $('<h3><a target="_blank" href="' + doc.url + '">' + doc.url + '</a></h3>')
	    .append(preview);

	var meta = $('<h3>').append(
	    $.map(['author', 'category', 'work'], function(key) {
		var popup = $('<div class="popup"><ul>' +
			      '<li class="popup-more">show results by ' + key + ' <em>' 
			      + doc[key] + '</em></li>' +
			      '<li class="popup-less">exclude results by ' + key + ' <em>' 
			      + doc[key] + '</em></li>' +
			      '</ul></div>');
		popup
		    .on('mouseleave', function() {
			$(this).hide()
		    })
		    .on('click', 'li', function(e) {
			var mod = this.className == 'popup-less' ? '-' : '+';
			$q = $('#query');
			$q.val($q.val() + ' ' + mod + key + ':' + doc[key]);
			popup.hide();
		    });

		return $('<span class="' + key + '">' + doc[key] + '</span>')
		    .prepend(popup)
		    .on('mouseenter', function() {
			popup.show();
		    });
	    }));

	return result
	    .append(fulltext)
	    .append('<h2>' + doc.title + '</h2>')
	    .append(link)
	    .append(meta)
	    .append($.map(highlight[doc.url].text, function(sn) {
		return '<p class="snippet">'+sn+'</p>';
	    }));
    }
});
