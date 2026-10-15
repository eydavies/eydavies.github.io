/* Progressive enhancement for the Cambridge map: zoom and pan, the day/night button and the boat.
   Without this file the whole map is shown at once, the colleges are plain links and everything works. */
(function () {
	'use strict';

	var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ---------- the moon / sun button: day <-> night (season.js applies the saved choice before first paint) ---------- */
	var tod = document.getElementById('tod'), root = document.documentElement;
	function syncTod() {
		if (!tod) { return; }
		var night = root.getAttribute('data-time') === 'night';
		tod.setAttribute('aria-pressed', night ? 'true' : 'false');
		tod.setAttribute('title', night ? 'Day mode' : 'Night mode');
	}
	if (tod) {
		syncTod();
		tod.addEventListener('click', function () {
			var night = root.getAttribute('data-time') !== 'night';
			if (night) { root.setAttribute('data-time', 'night'); } else { root.removeAttribute('data-time'); }
			try { window.localStorage.setItem('lg-night', night ? '1' : '0'); } catch (e) { /* fine: just not remembered */ }
			syncTod();
		});
	}

	var svg = document.querySelector('.scene'), world = document.getElementById('world');
	if (!svg || !world) { return; }
	var wrap = svg.parentNode, hint = document.querySelector('.map-hint');
	var zin = document.getElementById('zin'), zout = document.getElementById('zout'), zfit = document.getElementById('zfit');

	/* ---------- zoom and pan ----------
	   The svg's own viewBox is dropped, so one SVG unit is one screen pixel, and the whole map hangs off one transform:
	   translate(tx ty) scale(s), where s is screen pixels per art pixel. */
	var map = svg.getAttribute('data-map').split(' ').map(Number);               /* x0 y0 x1 y1 of the map, in art pixels */
	var mw = map[2] - map[0], mh = map[3] - map[1];
	svg.removeAttribute('viewBox');
	var bw = 0, bh = 0, s = 1, tx = 0, ty = 0, fitS = 1, minS = 0.2, maxS = 12, auto = true, raf = null;

	function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
	function measure() {
		var r = svg.getBoundingClientRect(); bw = r.width; bh = r.height;
		var pad = Math.min(24, bw * 0.04);
		fitS = Math.min((bw - 2 * pad) / mw, (bh - 2 * pad) / mh);
		minS = fitS * 0.4; maxS = Math.max(10, fitS * 6);
	}
	function limit() {                                                          /* keep at least a corner of the map on screen */
		var m = 0.2 * Math.min(bw, bh);
		tx = clamp(tx, m - map[2] * s, bw - m - map[0] * s);
		ty = clamp(ty, m - map[3] * s, bh - m - map[1] * s);
	}
	function apply() {
		world.setAttribute('transform', 'translate(' + tx.toFixed(2) + ' ' + ty.toFixed(2) + ') scale(' + s.toFixed(4) + ')');
		svg.classList.toggle('zoomed', s > fitS * 1.02);
		if (zin) { zin.disabled = s >= maxS * 0.999; }
		if (zout) { zout.disabled = s <= minS * 1.001; }
	}
	function showAll() {
		s = fitS; tx = (bw - mw * s) / 2 - map[0] * s; ty = (bh - mh * s) / 2 - map[1] * s; auto = true; apply();
	}
	function setView(ns, ntx, nty) { s = ns; tx = ntx; ty = nty; limit(); apply(); }
	function animate(ns, ntx, nty) {
		ns = clamp(ns, minS, maxS);
		if (reduce) { setView(ns, ntx, nty); return; }
		if (raf) { cancelAnimationFrame(raf); }
		var s0 = s, x0 = tx, y0 = ty, t0 = null;
		function step(t) {
			if (t0 === null) { t0 = t; }
			var k = Math.min(1, (t - t0) / 180), e = 1 - Math.pow(1 - k, 3);
			setView(s0 + (ns - s0) * e, x0 + (ntx - x0) * e, y0 + (nty - y0) * e);
			raf = k < 1 ? requestAnimationFrame(step) : null;
		}
		raf = requestAnimationFrame(step);
	}
	function zoomTarget(factor, px, py) {                                        /* the view after zooming about screen point (px, py) */
		var ns = clamp(s * factor, minS, maxS), k = ns / s;
		return [ns, px - (px - tx) * k, py - (py - ty) * k];
	}
	function zoomBy(factor, px, py, instant) {
		if (px === undefined) { px = bw / 2; py = bh / 2; }
		var v = zoomTarget(factor, px, py); auto = false; touched();
		if (instant) { setView(v[0], v[1], v[2]); } else { animate(v[0], v[1], v[2]); }
	}
	function touched() { if (hint) { hint.classList.add('gone'); } }
	function local(e) { var r = svg.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }

	function start() {                                                          /* the whole map, but on a phone start closer in (on the Backs) so names are readable */
		showAll();
		if (bw >= 700) { return; }
		var f = (svg.getAttribute('data-focus') || '').split(' ').map(Number);
		if (f.length === 2) { s = fitS * 1.9; tx = bw / 2 - f[0] * s; ty = bh / 2 - f[1] * s; auto = false; limit(); apply(); }
	}
	measure(); start();
	window.addEventListener('resize', function () {
		var cx = (bw / 2 - tx) / s, cy = (bh / 2 - ty) / s;                       /* the art-pixel point at the middle of the view */
		measure();
		if (auto) { showAll(); return; }
		s = clamp(s, minS, maxS); tx = bw / 2 - cx * s; ty = bh / 2 - cy * s; limit(); apply();
	});

	if (zin) { zin.addEventListener('click', function () { zoomBy(1.6); }); }
	if (zout) { zout.addEventListener('click', function () { zoomBy(1 / 1.6); }); }
	if (zfit) { zfit.addEventListener('click', function () { touched(); if (raf) { cancelAnimationFrame(raf); } var a = [fitS, (bw - mw * fitS) / 2 - map[0] * fitS, (bh - mh * fitS) / 2 - map[1] * fitS]; animate(a[0], a[1], a[2]); auto = true; }); }

	/* Ctrl / Cmd + scroll wheel (this is also how a trackpad pinch arrives), so that plain scrolling still scrolls the page */
	svg.addEventListener('wheel', function (e) {
		if (!(e.ctrlKey || e.metaKey)) { return; }
		e.preventDefault();
		var p = local(e), d = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
		zoomBy(Math.exp(-clamp(d, -120, 120) * (Math.abs(d) >= 50 ? 0.0018 : 0.012)), p[0], p[1], true);      /* a mouse-wheel notch is gentler than a pinch */
	}, { passive: false });
	/* Safari's own pinch events */
	var gBase = 1;
	svg.addEventListener('gesturestart', function (e) { e.preventDefault(); gBase = s; });
	svg.addEventListener('gesturechange', function (e) { e.preventDefault(); var p = local(e); zoomBy(gBase * e.scale / s, p[0], p[1], true); });
	svg.addEventListener('gestureend', function (e) { e.preventDefault(); });

	/* double-click zooms in on that spot (Shift: out) */
	svg.addEventListener('dblclick', function (e) {
		if (e.target.closest && e.target.closest('a')) { return; }
		var p = local(e); zoomBy(e.shiftKey ? 1 / 2 : 2, p[0], p[1]);
	});

	/* drag to move; two fingers to pinch. A drag that starts on a college must not open it. */
	var ptrs = {}, count = 0, drag = null, pinch = null, wasDrag = false;
	function dist(a, b) { return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)); }
	function two() { var k = Object.keys(ptrs); return [ptrs[k[0]], ptrs[k[1]]]; }
	svg.addEventListener('pointerdown', function (e) {
		if (e.pointerType === 'mouse' && e.button !== 0) { return; }
		var p = local(e);
		if (!ptrs[e.pointerId]) { count++; }
		ptrs[e.pointerId] = { x: p[0], y: p[1] };
		if (raf) { cancelAnimationFrame(raf); raf = null; }
		if (count === 1) { drag = { x: p[0], y: p[1], tx: tx, ty: ty, on: false }; }
		if (count === 2) {
			var q = two(); pinch = { d: dist(q[0], q[1]) || 1, s: s, mx: (q[0].x + q[1].x) / 2, my: (q[0].y + q[1].y) / 2, tx: tx, ty: ty };
			drag = null; wasDrag = true;
		}
	});
	svg.addEventListener('pointermove', function (e) {
		var cur = ptrs[e.pointerId]; if (!cur) { return; }
		var p = local(e); cur.x = p[0]; cur.y = p[1];
		if (pinch && count >= 2) {
			var q = two(), d = dist(q[0], q[1]) || 1, mx = (q[0].x + q[1].x) / 2, my = (q[0].y + q[1].y) / 2;
			var ns = clamp(pinch.s * d / pinch.d, minS, maxS), k = ns / pinch.s;
			s = ns; tx = mx - (pinch.mx - pinch.tx) * k; ty = my - (pinch.my - pinch.ty) * k;
			auto = false; touched(); limit(); apply(); e.preventDefault(); return;
		}
		if (!drag) { return; }
		var dx = p[0] - drag.x, dy = p[1] - drag.y;
		if (!drag.on) {
			if (dx * dx + dy * dy < 25) { return; }
			if (e.pointerType === 'touch' && !svg.classList.contains('zoomed')) { drag = null; return; }   /* not zoomed in: a finger scrolls the page */
			drag.on = true; wasDrag = true; svg.classList.add('dragging');
			try { svg.setPointerCapture(e.pointerId); } catch (err) { /* fine */ }
		}
		auto = false; touched(); tx = drag.tx + dx; ty = drag.ty + dy; limit(); apply();
	});
	function release(e) {
		if (!ptrs[e.pointerId]) { return; }
		delete ptrs[e.pointerId]; count = Math.max(0, count - 1);
		if (count < 2) { pinch = null; }
		if (count === 1) { var k = Object.keys(ptrs)[0]; drag = { x: ptrs[k].x, y: ptrs[k].y, tx: tx, ty: ty, on: false }; }
		if (count === 0) { drag = null; svg.classList.remove('dragging'); setTimeout(function () { wasDrag = false; }, 0); }
	}
	svg.addEventListener('pointerup', release);
	svg.addEventListener('pointercancel', release);
	svg.addEventListener('click', function (e) { if (wasDrag) { e.preventDefault(); e.stopPropagation(); } }, true);

	/* keyboard: + - 0 and the arrow keys while focus is anywhere in the map; Tab to a college scrolls it into view */
	wrap.addEventListener('keydown', function (e) {
		if (e.ctrlKey || e.metaKey || e.altKey) { return; }
		var k = e.key, step = Math.min(bw, bh) * 0.22;
		if (k === '+' || k === '=') { zoomBy(1.6); }
		else if (k === '-' || k === '_') { zoomBy(1 / 1.6); }
		else if (k === '0') { if (zfit) { zfit.click(); } }
		else if (k === 'ArrowLeft') { animate(s, tx + step, ty); auto = false; }
		else if (k === 'ArrowRight') { animate(s, tx - step, ty); auto = false; }
		else if (k === 'ArrowUp') { animate(s, tx, ty + step); auto = false; }
		else if (k === 'ArrowDown') { animate(s, tx, ty - step); auto = false; }
		else { return; }
		touched(); e.preventDefault();
	});
	wrap.addEventListener('focusin', function (e) {
		var a = e.target.closest ? e.target.closest('a.campus') : null; if (!a) { return; }
		var r = a.getBoundingClientRect(), b = svg.getBoundingClientRect(), m = 28, dx = 0, dy = 0;
		if (r.left < b.left + m) { dx = b.left + m - r.left; } else if (r.right > b.right - m) { dx = b.right - m - r.right; }
		if (r.top < b.top + m) { dy = b.top + m - r.top; } else if (r.bottom > b.bottom - m) { dy = b.bottom - m - r.bottom; }
		if (dx || dy) { auto = false; setView(s, tx + dx, ty + dy); }
	});

	/* ---------- the boat: whole-pixel steps along the first stretch of the river ---------- */
	var boat = document.getElementById('boat');
	if (!boat || reduce) { return; }
	var arm = (svg.getAttribute('data-arm') || '').split(',').map(Number), x0 = Number(svg.getAttribute('data-arm-x0') || 0);
	if (arm.length < 2) { return; }
	function riverY(x) {
		var f = Math.max(0, (x - x0) / 4), i = Math.min(arm.length - 2, Math.floor(f));
		var a = arm[i], b = arm[i + 1], t = Math.min(1, f - i);
		return Math.round(a + (b - a) * t);
	}
	var START = x0, END = x0 + (arm.length - 1) * 4, SPEED = 11;                /* art pixels per second */
	var t0 = null, last = null;
	function frame(t) {
		if (t0 === null) { t0 = t; }
		var x = START + Math.floor(((t - t0) / 1000 * SPEED) % (END - START));
		if (x !== last) {
			last = x;
			boat.setAttribute('transform', 'translate(' + x + ' ' + riverY(x) + ')');
		}
		requestAnimationFrame(frame);
	}
	requestAnimationFrame(frame);
})();
