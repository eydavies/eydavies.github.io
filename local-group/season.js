/* Picks the season from today's date in Boston and tags <html data-season="...">.
   Loaded (tiny, not deferred) in <head> so the page never flashes the wrong colours.
     Dec-Feb winter (snow)   Mar-May spring (blossom)   Jun-Aug summer   Sep-Nov fall (foliage)
   To preview a season, add ?season=winter (or spring / summer / fall) to the address. */
(function () {
	'use strict';
	var BY_MONTH = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'fall', 'fall', 'fall', 'winter'];

	function bostonMonth() {                       /* 0 = January */
		try {
			var m = parseInt(new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', month: 'numeric' }).format(new Date()), 10);
			if (m >= 1 && m <= 12) { return m - 1; }
		} catch (e) { /* very old browser: fall back to the visitor's own clock */ }
		return new Date().getMonth();
	}

	var forced = /[?&]season=(winter|spring|summer|fall|autumn)\b/.exec(window.location.search);
	var season = forced ? (forced[1] === 'autumn' ? 'fall' : forced[1]) : BY_MONTH[bostonMonth()];
	document.documentElement.setAttribute('data-season', season);
})();
