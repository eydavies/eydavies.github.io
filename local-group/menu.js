/* Progressive enhancement for the Local Group map. Without this file the
   buildings are plain links, the boat sits still, and everything still works. */
(function () {
	'use strict';

	var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ---------- the moon / sun button: day <-> night (season.js applies the saved choice before first paint) ---------- */
	var tod = document.getElementById('tod'), root = document.documentElement;
	function syncTod() {
		if (!tod) { return; }
		var night = root.getAttribute('data-time') === 'night';
		tod.setAttribute('aria-pressed', night ? 'true' : 'false');
		tod.setAttribute('aria-label', night ? 'Switch to day mode' : 'Switch to night mode');
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
		var free = Math.max(0, vh - (Number(svg.getAttribute('data-cbot')) + 10 - top));
		var drop = 10 + Math.min(free * 0.6, 40);
		var bubble = svg.querySelector('.bot .bscale'), riverEl = svg.querySelector('.rv > g');
		if (bubble && riverEl) {
			/* BU is hosting: put it as high as it goes, so its speech bubble sits just under the river (a small gap) */
			svg.style.setProperty('--drop', '0');
			var gap = 7;                                                                  /* art pixels between river and bubble */
			drop = (riverEl.getBoundingClientRect().bottom - bubble.getBoundingClientRect().top) / scale + gap;
			drop = Math.max(0, Math.min(drop, 60));
		}
		svg.style.setProperty('--drop', drop.toFixed(1));
	}
	fit();
	window.addEventListener('resize', fit);

	/* ---------- easter egg (desktop only): click anywhere that is not a link and a little figure appears (up to two) ----------
	   Click on land: it walks around and follows your mouse. Click in the river: it bobs along the river (in winter it
	   slides along the ice). With two out, another click sends the older one to the new spot. */
	(function () {
		var walkL = document.getElementById('egg-walk'), swimL = document.getElementById('egg-swim');
		if (!svg || !walkL || !swimL) { return; }
		var desk = window.matchMedia ? window.matchMedia('(min-width: 900px) and (hover: hover) and (pointer: fine)') : null;
		var NS = 'http://www.w3.org/2000/svg', XL = 'http://www.w3.org/1999/xlink';
		var W = Number(svg.getAttribute('data-w') || 380), H = 226;
		var rv = (svg.getAttribute('data-river') || '113,4,64,10').split(',').map(Number), HALF = rv[3] || 10;
		var bridgeX = Number(svg.getAttribute('data-bridge') || 148);
		var obst = (svg.getAttribute('data-obst') || '').split(';').filter(Boolean).map(function (s) {
			var a = s.split(',').map(Number); return { x0: a[0] - a[3], x1: a[0] + a[3], y0: a[1], y1: a[2] };
		});
		var figs = [], mouse = { x: 0, y: 0, on: false };

		function ry(x) { return rv[0] + Math.floor(rv[1] * Math.sin(2 * Math.PI * x / rv[2]) + 0.5); }
		function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
		function toSvg(cx, cy) {
			var m = svg.getScreenCTM(); if (!m) { return null; }
			var pt = svg.createSVGPoint(); pt.x = cx; pt.y = cy;
			return pt.matrixTransform(m.inverse());
		}
		function isFree(x, y) {                           /* land a walker may stand on: not a building, not the river (except on the bridge) */
			if (x < 6 || x > W - 6 || y < 14 || y > H - 4) { return false; }
			for (var i = 0; i < obst.length; i++) {
				var o = obst[i]; if (x >= o.x0 - 3 && x <= o.x1 + 3 && y >= o.y0 && y <= o.y1) { return false; }
			}
			return !(Math.abs(y - ry(x)) <= HALF + 1 && Math.abs(x - bridgeX) > 7);
		}
		function nearest(x, y) {
			if (isFree(x, y)) { return { x: x, y: y }; }
			for (var r = 2; r <= 70; r += 2) {
				for (var a = 0; a < 360; a += 20) {
					var px = x + r * Math.cos(a * Math.PI / 180), py = y + r * Math.sin(a * Math.PI / 180);
					if (isFree(px, py)) { return { x: px, y: py }; }
				}
			}
			return { x: x, y: y };
		}

		document.addEventListener('mousemove', function (e) {
			var p = toSvg(e.clientX, e.clientY);
			mouse.on = !!p && svg.contains(e.target);
			if (p) { mouse.x = p.x; mouse.y = p.y; }
		});
		document.addEventListener('mouseleave', function () { mouse.on = false; });

		var raf = null, last = null;
		function ensureLoop() {
			if (reduce || raf) { return; }
			last = null; raf = requestAnimationFrame(tick);
		}

		function spawn(p) {
			var inRiver = Math.abs(p.y - ry(p.x)) <= HALF;
			var kind;
			if (figs.length >= 2) {
				var old = figs.shift(); kind = old.kind; old.el.parentNode && old.el.parentNode.removeChild(old.el);
			} else {
				kind = figs.length && figs[0].kind === 'A' ? 'B' : 'A';
			}
			var winter = document.documentElement.getAttribute('data-season') === 'winter';
			var f = { kind: kind, river: inRiver, winter: winter, dir: p.x < W / 2 ? 1 : -1, frame: 1, phase: Math.random() * 4, t: 0, wp: null, wpUntil: 0 };
			if (inRiver) { f.x = clamp(p.x, 14, W - 14); f.y = ry(f.x); }
			else { var q = nearest(clamp(p.x, 8, W - 8), clamp(p.y, 14, H - 4)); f.x = q.x; f.y = q.y; }
			f.el = document.createElementNS(NS, 'g');
			f.use = document.createElementNS(NS, 'use');
			f.el.appendChild(f.use);
			(inRiver ? swimL : walkL).appendChild(f.el);
			figs.push(f);
			draw(f, 0);
			var pop = document.createElementNS(NS, 'g');                        /* a little puff where they appear */
			pop.setAttribute('class', 'egg-pop'); pop.setAttribute('transform', 'translate(' + Math.round(f.x) + ' ' + Math.round(f.y - 6) + ')');
			pop.innerHTML = '<rect x="-1" y="-5" width="2" height="2" fill="#fff"/><rect x="-1" y="3" width="2" height="2" fill="#fff"/><rect x="-6" y="-1" width="2" height="2" fill="#fff"/><rect x="4" y="-1" width="2" height="2" fill="#fff"/>';
			(inRiver ? swimL : walkL).appendChild(pop);
			setTimeout(function () { pop.parentNode && pop.parentNode.removeChild(pop); }, 450);
			ensureLoop();
		}

		document.addEventListener('click', function (e) {
			if (e.defaultPrevented || e.button) { return; }
			if (!desk || !desk.matches || svg.classList.contains('compact')) { return; }
			if (e.target.closest && e.target.closest('a, button, [role="button"], summary, select, input, textarea, label')) { return; }
			var p = toSvg(e.clientX, e.clientY); if (!p) { return; }
			spawn({ x: clamp(p.x, 0, W), y: clamp(p.y, 0, H) });
		});

		function draw(f, now) {
			var swim = f.river && !f.winter;
			var href = '#egg-' + f.kind + '-' + (swim ? 's' : 'w') + f.frame;
			f.use.setAttribute('href', href); f.use.setAttributeNS(XL, 'xlink:href', href);
			var y = f.y;
			if (swim) { y = ry(Math.round(f.x)) + 3 + (Math.floor(now / 1000 * 1.4 + f.phase) % 2 ? -1 : 0); }   /* a gentle bob, in whole pixels */
			else if (f.river) { y = ry(Math.round(f.x)) + 4; }                                                 /* standing on the ice */
			f.el.setAttribute('transform', 'translate(' + Math.round(f.x) + ' ' + Math.round(y) + ')' + (f.dir < 0 ? ' scale(-1 1)' : ''));
		}

		function stepLand(f, dt, now) {
			var follow = mouse.on, tx, ty;
			if (follow) {
				var q = nearest(clamp(mouse.x + (f.kind === 'A' ? -9 : 9), 8, W - 8), clamp(mouse.y + 2, 14, H - 4));
				tx = q.x; ty = q.y;
			} else {
				if (!f.wp || now > f.wpUntil) {
					f.wp = null; f.wpUntil = now + 2000 + Math.random() * 3000;
					if (Math.random() < 0.7) {
						for (var i = 0; i < 12; i++) {
							var p = nearest(f.x + Math.random() * 90 - 45, f.y + Math.random() * 50 - 25);
							if ((p.y < ry(p.x)) === (f.y < ry(f.x))) { f.wp = p; break; }
						}
					}
				}
				if (!f.wp) { return false; }
				tx = f.wp.x; ty = f.wp.y;
			}
			var d0 = f.y - ry(f.x), sideP = d0 < -(HALF + 1) ? -1 : (d0 > HALF + 1 ? 1 : 0);   /* -1 north bank, +1 south bank, 0 in the river band (on the bridge) */
			var sideT = ty < ry(tx) ? -1 : 1;
			var crossing = sideP === 0 || sideP !== sideT;
			if (crossing) {                                  /* other side of the river: use the bridge */
				var ap = function (s) { return ry(bridgeX) + s * (HALF + 3); };
				var inStrip = sideP === 0 || (Math.abs(f.x - bridgeX) <= 8 && Math.abs(f.y - ry(f.x)) <= HALF + 6);   /* at the entrance or on it: cross */
				tx = bridgeX; ty = inStrip ? ap(sideT) : ap(sideP);
			}
			var dx = tx - f.x, dy = ty - f.y, dist = Math.sqrt(dx * dx + dy * dy);
			var arrive = crossing ? 1.5 : (follow ? 6 : 2);
			if (dist <= arrive) { if (follow) { f.dir = (mouse.x >= f.x) ? 1 : -1; } return false; }
			var step = Math.min(dist, 20 * dt), base = Math.atan2(dy, dx), offs = [0, 0.6, -0.6, 1.2, -1.2, 1.9, -1.9], moved = false;
			for (var k = 0; k < offs.length; k++) {
				var nx = f.x + step * Math.cos(base + offs[k]), ny = f.y + step * Math.sin(base + offs[k]);
				if (isFree(nx, ny)) {
					if (Math.abs(nx - f.x) > 0.01) { f.dir = nx > f.x ? 1 : -1; }
					f.x = nx; f.y = ny; moved = true; break;
				}
			}
			if (!moved) { f.wp = null; }
			return moved;
		}

		function stepRiver(f, dt, now) {
			var follow = mouse.on && Math.abs(mouse.y - ry(mouse.x)) <= HALF + 10, sp = 9;
			if (follow) {
				var d = (mouse.x + (f.kind === 'A' ? -10 : 10)) - f.x;
				if (Math.abs(d) <= 3) { return false; }
				f.dir = d > 0 ? 1 : -1; f.x += f.dir * Math.min(Math.abs(d), sp * dt); return true;
			}
			f.x += f.dir * 7 * dt;
			if (f.x > W - 14) { f.dir = -1; } else if (f.x < 14) { f.dir = 1; }
			return true;
		}

		function tick(t) {
			raf = null; if (!figs.length) { return; }
			var dt = last === null ? 0 : Math.min(0.1, (t - last) / 1000); last = t;
			figs.forEach(function (f) {
				var moving = f.river ? stepRiver(f, dt, t) : stepLand(f, dt, t);
				f.t += moving ? dt : 0;
				f.frame = moving ? (Math.floor(f.t / 0.2) % 2) : 1;
				draw(f, t);
			});
			figs.filter(function (f) { return !f.river; }).sort(function (a, b) { return a.y - b.y; })
				.forEach(function (f) { walkL.appendChild(f.el); });                   /* the one further down the map is drawn in front */
			raf = requestAnimationFrame(tick);
		}
	})();

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
