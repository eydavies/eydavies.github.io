/* Schedule and campus pages:
   - the day after a meeting's date it moves from the upcoming list to "Past events" (a collapsed toggle underneath;
     the date is Boston's, and the page was already split the same way when it was built);
   - schedule page only: click an icon in the key to show only that kind of talk or meeting (click it again to clear
     it), and hide or show the key with the +/- button. */
(function () {
	'use strict';
	document.documentElement.classList.add('js');
	var upList = document.getElementById('upcoming'), pastWrap = document.getElementById('past'), pastList = document.getElementById('past-list');
	if (!upList || !pastWrap || !pastList) { return; }
	var noUp = document.getElementById('no-upcoming'), pastBtn = pastWrap.querySelector('.past-toggle'), pastCount = pastWrap.querySelector('.pt-count');
	var legend = document.getElementById('key');
	var empty = document.getElementById('no-match'), status = document.getElementById('filter-status');
	var state = { type: null, freq: null };

	/* ---------- upcoming or past, by Boston's calendar ---------- */
	function bostonToday() {                                        /* "YYYY-MM-DD" */
		try {
			var parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date()), o = {};
			parts.forEach(function (p) { o[p.type] = p.value; });
			return o.year + '-' + o.month + '-' + o.day;
		} catch (e) {
			var d = new Date(), z = function (n) { return (n < 10 ? '0' : '') + n; };
			return d.getFullYear() + '-' + z(d.getMonth() + 1) + '-' + z(d.getDate());
		}
	}
	function dateOf(li) { return li.getAttribute('data-date') || ''; }
	function sortInto() {
		var today = bostonToday();
		var all = Array.prototype.slice.call(upList.children).concat(Array.prototype.slice.call(pastList.children));
		all.sort(function (a, b) { return dateOf(a) < dateOf(b) ? -1 : dateOf(a) > dateOf(b) ? 1 : 0; });
		var up = all.filter(function (li) { return dateOf(li) >= today; });
		var past = all.filter(function (li) { return dateOf(li) < today; }).reverse();      /* most recent first */
		up.forEach(function (li) { upList.appendChild(li); });
		past.forEach(function (li) { pastList.appendChild(li); });
	}

	/* ---------- what is visible: counts, the Past events button, the "nothing here" messages ---------- */
	function visible(list) {
		return Array.prototype.filter.call(list.children, function (li) { return !li.hidden; }).length;
	}
	function render() {
		var upTot = upList.children.length, pastTot = pastList.children.length, upVis = visible(upList), pastVis = visible(pastList);
		var filtering = !!(state.type || state.freq);
		pastWrap.hidden = pastVis === 0;
		if (pastCount) { pastCount.textContent = '(' + pastVis + ')'; }
		if (noUp) {
			var msg = '';
			if (upVis === 0) {
				if (upTot > 0) { if (pastVis > 0) { msg = noUp.getAttribute('data-nomatch'); } }
				else if (pastTot === 0) { msg = noUp.getAttribute('data-none'); }
				else if (pastVis > 0 || !filtering) { msg = noUp.getAttribute('data-noup'); }
			}
			noUp.textContent = msg;
			noUp.hidden = !msg;
		}
		return upVis + pastVis;
	}
	if (pastBtn) {
		pastBtn.addEventListener('click', function () {
			var open = pastWrap.classList.toggle('open');
			pastBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
			pastBtn.querySelector('.pt-sign').textContent = open ? '-' : '+';
		});
	}

	sortInto();
	if (!legend) { render(); return; }

	/* ---------- schedule page: the key ---------- */
	var toggle = legend.querySelector('.key-toggle'), note = legend.querySelector('.key-note');
	var buttons = Array.prototype.slice.call(legend.querySelectorAll('.key-btn'));
	function allMeetings() { return Array.prototype.slice.call(document.querySelectorAll('.meetings > li')); }

	function apply(announce) {
		var meetings = allMeetings();
		meetings.forEach(function (li) {
			var freqOk = !state.freq || li.getAttribute('data-freq') === state.freq;
			var talks = Array.prototype.slice.call(li.querySelectorAll('.talks > li')), any = false, first = true;
			talks.forEach(function (t) {
				var ok = !state.type || t.getAttribute('data-type') === state.type;
				t.hidden = !ok;
				t.classList.toggle('first', ok && first);
				if (ok) { any = true; first = false; }
			});
			li.hidden = !(freqOk && (!state.type || any));
		});
		var shown = render();
		if (empty) { empty.hidden = shown > 0 || meetings.length === 0; }
		if (announce && status) {
			status.textContent = shown === 0 ? 'No meetings match this selection.' : (state.type || state.freq ? 'Showing ' + shown + ' of ' + meetings.length + ' meetings.' : 'Showing all ' + meetings.length + ' meetings.');
		}
		buttons.forEach(function (b) {
			b.setAttribute('aria-pressed', state[b.getAttribute('data-kind')] === b.getAttribute('data-val') ? 'true' : 'false');
		});
		if (note) { note.hidden = !(legend.classList.contains('is-collapsed') && (state.type || state.freq)); }
	}

	buttons.forEach(function (b) {
		b.addEventListener('click', function () {
			var kind = b.getAttribute('data-kind'), val = b.getAttribute('data-val');
			state[kind] = state[kind] === val ? null : val;
			apply(true);
		});
	});

	if (toggle) {
		toggle.addEventListener('click', function () {
			var collapsed = legend.classList.toggle('is-collapsed');
			toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
			toggle.title = collapsed ? 'Show the key' : 'Hide the key';
			toggle.firstChild.textContent = collapsed ? '+' : '-';
			toggle.lastChild.textContent = collapsed ? 'Show the key' : 'Hide the key';
			apply();
		});
	}
	apply();
})();
