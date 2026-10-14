/* Picks the season from today's date in Boston and tags <html data-season="...">.
   Loaded (tiny, not deferred) in <head> so the page never flashes the wrong colours.
     Dec-Feb winter (snow)   Mar-May spring (blossom)   Jun-Aug summer   Sep-Nov fall (foliage)
   i.e. the season changes on 1 Dec, 1 Mar, 1 Jun and 1 Sep (Boston time); on 25 Dec a Christmas tree appears.
   To preview a season, add ?season=winter (or spring / summer / fall) to the address; add ?xmas to see the tree, ?night or ?day for night mode. */
(function () {
	'use strict';
	var BY_MONTH = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall', 'fall', 'winter'];

	function bostonDate() {                        /* { month: 0 = January, day: 1-31 } */
		try {
			var f = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', month: 'numeric', day: 'numeric' }).formatToParts(new Date()), o = {};
			for (var i = 0; i < f.length; i++) { o[f[i].type] = parseInt(f[i].value, 10); }
			if (o.month >= 1 && o.month <= 12 && o.day >= 1) { return { month: o.month - 1, day: o.day }; }
		} catch (e) { /* very old browser: fall back to the visitor's own clock */ }
		var d = new Date(); return { month: d.getMonth(), day: d.getDate() };
	}

	var forced = /[?&]season=(winter|spring|summer|fall|autumn)\b/.exec(window.location.search);
	var season = forced ? (forced[1] === 'autumn' ? 'fall' : forced[1]) : BY_MONTH[bostonDate().month];
	document.documentElement.setAttribute('data-season', season);
	var today = bostonDate();
	/* night mode: remembered between visits; ?night / ?day force it (handy for previews) */
	var night = false;
	try { night = window.localStorage.getItem('lg-night') === '1'; } catch (e) { /* storage blocked: stay in day mode */ }
	if (/[?&]night\b/.test(window.location.search)) { night = true; }
	if (/[?&]day\b/.test(window.location.search)) { night = false; }
	if (night) { document.documentElement.setAttribute('data-time', 'night'); }
	if ((today.month === 11 && today.day === 25) || /[?&]xmas\b/.test(window.location.search)) {
		document.documentElement.setAttribute('data-xmas', '1');
	}

	/* which colour sits behind the page when it is pulled past an edge: sky at the top, ground at the bottom (see style.css) */
	var root = document.documentElement;
	function lowerHalf() {
		var max = root.scrollHeight - window.innerHeight, y = window.pageYOffset || 0;
		root.classList.toggle('lower', max > 0 && y > max / 2);
	}
	window.addEventListener('scroll', lowerHalf, { passive: true });
	window.addEventListener('resize', lowerHalf);
	window.addEventListener('load', lowerHalf);
})();
