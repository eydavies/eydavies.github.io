/* Small progressive enhancements. The site works without this file: abstracts
   stay visible, and the CV page shows every section with plain anchor links. */
(function () {
	'use strict';

	/* ---------- Publications: abstract buttons ---------- */
	var toggles = Array.prototype.slice.call(document.querySelectorAll('.abs-toggle'));

	function setAbstract(btn, open) {
		var panel = document.getElementById(btn.getAttribute('aria-controls'));
		if (!panel) { return; }
		btn.setAttribute('aria-expanded', open ? 'true' : 'false');
		panel.classList.toggle('is-open', open);
	}

	toggles.forEach(function (btn) {
		btn.addEventListener('click', function () {
			setAbstract(btn, btn.getAttribute('aria-expanded') !== 'true');
			syncAllButton();
		});
	});

	var allBtn = document.querySelector('.abs-all');
	function syncAllButton() {
		if (!allBtn) { return; }
		var allOpen = toggles.length > 0 && toggles.every(function (b) {
			return b.getAttribute('aria-expanded') === 'true';
		});
		allBtn.setAttribute('aria-pressed', allOpen ? 'true' : 'false');
		allBtn.textContent = allOpen ? 'Hide all abstracts' : 'Show all abstracts';
	}
	if (allBtn) {
		allBtn.addEventListener('click', function () {
			var open = allBtn.getAttribute('aria-pressed') !== 'true';
			toggles.forEach(function (b) { setAbstract(b, open); });
			syncAllButton();
		});
	}

	/* ---------- Publications: BibTeX buttons ---------- */
	Array.prototype.forEach.call(document.querySelectorAll('.bib-toggle'), function (btn) {
		btn.addEventListener('click', function () {
			var open = btn.getAttribute('aria-expanded') !== 'true';
			var panel = document.getElementById(btn.getAttribute('aria-controls'));
			if (!panel) { return; }
			btn.setAttribute('aria-expanded', open ? 'true' : 'false');
			panel.classList.toggle('is-open', open);
		});
	});

	Array.prototype.forEach.call(document.querySelectorAll('.bib-copy'), function (btn) {
		btn.addEventListener('click', function () {
			var code = btn.parentNode.querySelector('code');
			var text = code ? code.textContent : '';
			function done(ok) {
				btn.textContent = ok ? 'Copied' : 'Press Ctrl/Cmd+C';
				setTimeout(function () { btn.textContent = 'Copy'; }, 1800);
			}
			function fallback() {
				var sel = window.getSelection();
				var range = document.createRange();
				range.selectNodeContents(code);
				sel.removeAllRanges();
				sel.addRange(range);
				var ok = false;
				try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
				done(ok);
			}
			if (navigator.clipboard && navigator.clipboard.writeText) {
				navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
			} else {
				fallback();
			}
		});
	});

	/* ---------- CV page ---------- */
	var cv = document.querySelector('[data-cv]');
	if (!cv) { return; }

	var sections = Array.prototype.slice.call(cv.querySelectorAll('.cv-section'));
	var chips = Array.prototype.slice.call(cv.querySelectorAll('.cv-chips a'));
	var toggleAll = cv.querySelector('.cv-toggle-all');
	var chipBar = cv.querySelector('.cv-chips');

	function setCollapsed(sec, collapsed) {
		sec.classList.toggle('is-collapsed', collapsed);
		var btn = sec.querySelector('.cv-section-toggle');
		if (btn) { btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true'); }
	}

	function syncToggleAll() {
		if (!toggleAll) { return; }
		var anyOpen = sections.some(function (s) { return !s.classList.contains('is-collapsed'); });
		toggleAll.textContent = anyOpen ? 'Collapse all' : 'Expand all';
	}

	/* Turn each section heading into a button that folds the section. */
	sections.forEach(function (sec) {
		var h2 = sec.querySelector('h2');
		var body = sec.querySelector('.cv-body');
		var name = h2.textContent;
		var count = sec.querySelectorAll('.cv-entry').length;
		var btn = document.createElement('button');
		btn.type = 'button';
		btn.className = 'cv-section-toggle';
		btn.setAttribute('aria-expanded', 'true');
		btn.setAttribute('aria-controls', body.id);
		var label = document.createElement('span');
		label.className = 'cv-section-name';
		label.textContent = name;
		var badge = document.createElement('span');
		badge.className = 'cv-count';
		badge.textContent = count;
		var chevron = document.createElement('span');
		chevron.className = 'cv-chevron';
		chevron.setAttribute('aria-hidden', 'true');
		btn.appendChild(label);
		btn.appendChild(badge);
		btn.appendChild(chevron);
		h2.textContent = '';
		h2.appendChild(btn);
		btn.addEventListener('click', function () {
			setCollapsed(sec, !sec.classList.contains('is-collapsed'));
			syncToggleAll();
		});
	});

	if (toggleAll) {
		toggleAll.addEventListener('click', function () {
			var anyOpen = sections.some(function (s) { return !s.classList.contains('is-collapsed'); });
			sections.forEach(function (s) { setCollapsed(s, anyOpen); });
			syncToggleAll();
		});
	}

	/* Jumping to a folded section (chip click, or a #section link) opens it. */
	function openFromHash() {
		var id = decodeURIComponent(location.hash.slice(1));
		var sec = id && document.getElementById(id);
		if (sec && sec.classList.contains('cv-section')) {
			setCollapsed(sec, false);
			syncToggleAll();
		}
	}
	chips.forEach(function (chip) {
		chip.addEventListener('click', function () {
			var sec = document.getElementById(chip.getAttribute('href').slice(1));
			if (sec) { setCollapsed(sec, false); syncToggleAll(); }
		});
	});
	window.addEventListener('hashchange', openFromHash);
	openFromHash();

	/* Highlight the chip of the section being read. */
	if ('IntersectionObserver' in window && chipBar) {
		var visible = new Set();
		var observer = new IntersectionObserver(function (changes) {
			changes.forEach(function (c) {
				if (c.isIntersecting) { visible.add(c.target); } else { visible.delete(c.target); }
			});
			var current = sections.filter(function (s) { return visible.has(s); })[0];
			chips.forEach(function (chip) {
				var on = !!current && chip.getAttribute('href') === '#' + current.id;
				chip.classList.toggle('is-current', on);
				if (on) {
					chip.setAttribute('aria-current', 'true');
					var target = chip.offsetLeft - (chipBar.clientWidth - chip.offsetWidth) / 2;
					if (chipBar.scrollWidth > chipBar.clientWidth) { chipBar.scrollLeft = target; }
				} else {
					chip.removeAttribute('aria-current');
				}
			});
		}, { rootMargin: '-15% 0px -70% 0px' });
		sections.forEach(function (s) { observer.observe(s); });
	}
}());
