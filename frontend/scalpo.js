$(function() {
    // Remove all listeners first
    $('*').off('.scalpo')

    // Controls for editing the config parameters from the UI
    $('#config')
	.empty()
	.append($.map(scalpo.config, function(v, k) {
	    return $('<div>')
		.append('<label for="config-' + k + '">' + k +'</label>')
		.append($('<input id="config-' + k + '" type="text">')
			.data('key', k)
			.data('type', typeof v)
			.val(v));
	}))
	.append('<div><a id="reload-js" href="#">reload .js</a></div>')
	.on('change.scalpo', 'input', function(e) {
	    $this = $(this);
	    types = {
		number: Number,
		string: String,
		boolean: Boolean
	    };
	    scalpo.config[$this.data('key')] = types[$this.data('type')]($this.val());
	})
	.on('click.scalpo', '#reload-js', function() {
	    $.getScript('scalpo.js');
	    return false;
	});

    // Handle history
    $(window).on('popstate.scalpo', function(e) {
	$('#query').val(e.originalEvent.state.query);
    });
    
    // Query launchers
    $('#select').on('click.scalpo', function() { query(0) });
    
    $('#pagination').on('click.scalpo', 'a', function() {
	query(+$(this).data('start'));
	return false;
    });

    // Events on search results
    $('#results')
    // toggle preview
	.on('click.scalpo', '.preview', function() { 
	    $(this).data('fulltext').show(); 
	})
	.on('click.scalpo', '.fulltext', function() {
	    $(this).hide();
	})
    // meta keyword popups
	.on('mouseenter.scalpo', '.meta', function() {
	    $(this).data('popup').show();
	})
	.on('mouseleave.scalpo', '.popup', function() {
	    $(this).hide();
	})
	.on('click.scalpo', '.popup li', function(e) {
	    var mod = this.className == 'popup-less' ? '-' : '+';
	    popup = $(this).parent().parent()
	    $q = $('#query');
	    $q.val($q.val() + ' ' + mod + popup.data('key') + ':"' + popup.data('val') + '"');
	    popup.hide();
	})
    // toggle snippet
	.on('click.scalpo', '.snip-show, .snip-hide', function() {
	    $(this)
		.toggleClass('snip-show snip-hide')
		.parent().parent().find('.snippet').toggle('fast');
	});

    var semaphore = false;

    function query (start) {
	if (!semaphore) {
	    semaphore = true;

	    var query = $('#query').val()
	    history.pushState({ query: query }, query)

	    $('input, button')
		.prop('disabled', true)
		.toggleClass('loading');
	    $('#msg').empty()

	    $.ajax({
		url: scalpo.config.url + '/' + scalpo.config.core + '/select',
		data: {
		    wt   : 'json',
		    q    : query,
		    start: start,
		    rows : scalpo.config.rows
		},
		dataType: 'jsonp',
		jsonp: 'json.wrf',
		success: function(data) {
		    if (data.responseHeader.status == 0) {
			tot = data.response.numFound;
			num = data.response.docs.length;
			$('#reshead .text')
			    .text('Found ' +  tot + 
				  ' documents in ' + data.responseHeader.QTime + 'ms, ' +
				  'showing results ' + start + '-' + (start + num) + '.');
			
			var $pag = $('#pagination').html('Go to results: ')
			for (var i = 0 ; i <= tot ; i += scalpo.config.rows) {
			    $pag.append('<a href="#" data-start="' + i + '">' + i + '-' + 
					Math.min(i + scalpo.config.rows, tot) + '</a> ');
			}

			$('#results').html(
			    $.map(data.response.docs, function(doc, pos) {
				return result(pos, doc, data.highlighting)
			    }));
		    } else {
			$('#msg').html('Error: ' + data.error.code);
		    }
		},
		timeout: 20000,
		error: function() {
		    $('#msg').html('Hmmm, 20s and no reply... This might be an error. Correct your query and try again, or try reloading the page.')
		},
		complete: function() {
		    $('input, button')
			.prop('disabled', false)
			.toggleClass('loading');
		    semaphore = false;
		}
	    });
	}
    }

    // This function constructs a block holding one search result
    function result(pos, doc, highlight) {
	var fulltext = $('<p class="fulltext">' + doc.text.join(' ') + '</p>')

	return $('<div id="result-' + pos + '" class="result">')
	// The full text of the result (constructed earlier)
	    .append(fulltext)
	// The title text
	    .append('<h2 class="title">' + doc.title + '</h2>')
	// The link to the source and the preview widget
	    .append($('<h3><a target="_blank" href="' + doc.url + '">' + doc.url + '</a></h3>')
		    .append($(' <span class="preview">preview</span>')
			    .data('fulltext', fulltext)))
	// The metadata (category, author, work, section) and collapse widget
	    .append($('<h3>')
		    .append($.map(['author', 'category', 'work', 'section'], function(key) {
			var popup = $();
			if (doc[key]) {
			    popup = $('<div class="popup"><ul>' +
				      '<li class="popup-more">show results by ' + key + ' <em>' 
				      + doc[key] + '</em></li>' +
				      '<li class="popup-less">exclude results by ' + key + ' <em>' 
				      + doc[key] + '</em></li>' +
				      '</ul></div>')
				.data('key', key)
				.data('val', doc[key]);
			}

			return $('<span class="meta ' + key + '">' + (doc[key] || ' ') + '</span>')
			    .prepend(popup)
			    .data('popup', popup);
		    }))
		    .append($('<span class="snip-show">')))
	// The source (if present)
	    .append(doc.source
		    ? ('<h4>Source: <a target="_blank" href="' 
		       + doc.source + '">' + doc.source + '</a></h4>')
		    : null)
	// The snippets
	    .append($.map(highlight[doc.url].text, function(sn) {
		return $('<p class="snippet">'+sn+'</p>');
	    }));
    }
});
