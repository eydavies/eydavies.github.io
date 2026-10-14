/* Progressive enhancement for the Local Group map. Without this file the
   buildings are plain links, the boat sits still, and everything still works. */
(function () {
	'use strict';

	var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ---------- buildings hop before the page changes ---------- */
	var links = Array.prototype.slice.call(document.querySelectorAll('.campus'));
	links.forEach(function (a) {
		a.addEventListener('click', function (e) {
			if (reduce || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) { return; }
			var href = a.getAttribute('href');
			if (!href) { return; }
			e.preventDefault();
			a.classList.add('go');
			setTimeout(function () { window.location.href = href; }, 420);
		});
	});
	/* coming back with the Back button: reset any building mid-hop */
	window.addEventListener('pageshow', function () {
		links.forEach(function (a) { a.classList.remove('go'); });
	});

	/* ---------- tall, narrow screens: crop the empty sides so the pixels come out bigger ---------- */
	var svg = document.querySelector('.scene');
	function fit() {
		if (!svg) { return; }
		var box = svg.getBoundingClientRect();
		var narrow = box.height > 0 && box.width / box.height < 1.1;
		svg.classList.toggle('compact', narrow);
		if (!narrow) { svg.setAttribute('viewBox', svg.getAttribute('data-view')); return; }
		/* phones: fixed width, but the view starts just above the highest thing on the map and is as tall as the
		   screen allows; any spare height is used to space BU further below the river instead of leaving a blank band */
		var vb = svg.getAttribute('data-compact').split(' ').map(Number);
		var scale = box.width / vb[2];
		var top = Number(svg.getAttribute('data-ctop')) - 6;
		var vh = box.height / scale;
		svg.setAttribute('viewBox', [vb[0], top, vb[2], vh].join(' '));
		var free = Math.max(0, vh - (Number(svg.getAttribute('data-cbot')) - top));
		svg.style.setProperty('--drop', Math.min(free * 0.6, 45).toFixed(1));
	}
	fit();
	window.addEventListener('resize', fit);

	/* ---------- the rower: whole-pixel steps along the (pixel) river ---------- */
	var boat = document.getElementById('boat');
	if (!boat || reduce) { return; }

	/* the river's shape comes from the generated page: "centre line, amplitude, period" */
	var river = (svg.getAttribute('data-river') || '113,4,64').split(',').map(Number);
	function riverY(x) { return river[0] + Math.floor(river[1] * Math.sin(2 * Math.PI * x / river[2]) + 0.5); }

	var START = -60, END = Number(svg.getAttribute('data-w') || 380) + 60, SPEED = 11;   /* art pixels per second */
	var t0 = null, last = null;
	function frame(t) {
		if (t0 === null) { t0 = t; }
		var x = START + Math.floor(((t - t0) / 1000 * SPEED + 100) % (END - START));
		if (x !== last) {
			last = x;
			boat.setAttribute('transform', 'translate(' + x + ' ' + riverY(x) + ')');
		}
		requestAnimationFrame(frame);
	}
	requestAnimationFrame(frame);
})();
