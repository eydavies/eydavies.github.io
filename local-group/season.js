/* Picks the season from today's date in Boston and tags <html data-season="...">.
   Loaded (tiny, not deferred) in <head> so the page never flashes the wrong colours.
     Dec-Feb winter (snow)   Mar-May spring (blossom)   Jun-Aug summer   Sep-Nov fall (foliage)
   i.e. the season changes on 1 Dec, 1 Mar, 1 Jun and 1 Sep (Boston time); on 25 Dec a Christmas tree appears.
   To preview a season, add ?season=winter (or spring / summer / fall) to the address; add ?xmas to see the tree. */
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
	if ((today.month === 11 && today.day === 25) || /[?&]xmas\b/.test(window.location.search)) {
		document.documentElement.setAttribute('data-xmas', '1');
	}
})();
