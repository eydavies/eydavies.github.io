/* Schedule page: click an icon in the key to show only that kind of talk or meeting (click it again to clear it),
   and hide or show the key with the +/- button. */
(function () {
	'use strict';
	document.documentElement.classList.add('js');
	var legend = document.getElementById('key');
	if (!legend) { return; }
	var toggle = legend.querySelector('.key-toggle'), note = legend.querySelector('.key-note');
	var buttons = Array.prototype.slice.call(legend.querySelectorAll('.key-btn'));
	var meetings = Array.prototype.slice.call(document.querySelectorAll('.meetings > li'));
	var empty = document.getElementById('no-match'), status = document.getElementById('filter-status');
	var state = { type: null, freq: null };

	function apply(announce) {
		var shown = 0;
		meetings.forEach(function (li) {
			var freqOk = !state.freq || li.getAttribute('data-freq') === state.freq;
			var talks = Array.prototype.slice.call(li.querySelectorAll('.talks > li')), any = false, first = true;
			talks.forEach(function (t) {
				var ok = !state.type || t.getAttribute('data-type') === state.type;
				t.hidden = !ok;
				t.classList.toggle('first', ok && first);
				if (ok) { any = true; first = false; }
			});
			var show = freqOk && (!state.type || any);
			li.hidden = !show;
			if (show) { shown++; }
		});
		if (empty) { empty.hidden = shown > 0; }
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
})();
