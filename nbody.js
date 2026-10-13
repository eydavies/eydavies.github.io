/* A small toy for the home page: click on empty space to drop a particle.
   Particles attract each other (softened gravity), are pulled towards the
   mouse (a softened point mass, so they orbit it) and bounce off the edges of
   the window. At most 20 particles. Desktop only: nothing is created on
   phones/tablets (no hover or coarse pointer, or a narrow window) or when the
   visitor prefers reduced motion. */
(function () {
	'use strict';

	if (!document.body.classList.contains('page-home')) { return; }

	/* ---------- tunables (pixels and seconds) ---------- */
	var MAX = 20;                // maximum number of particles
	var GM_MOUSE = 8.8e6;        // strength of the mouse's pull
	var EPS_MOUSE = 40;          // softening length of the mouse potential
	var GM_PART = 5e5;           // strength of each particle's pull on the others
	var EPS_PART = 30;           // softening length between particles
	var DT = 1 / 120;            // fixed integration step
	var DRAG = 0.03;             // gentle velocity damping, 1/s
	var RESTITUTION = 0.9;       // energy kept on a wall bounce
	var VMAX = 1400;             // speed limit, just a safety net
	var TRAIL = 26;              // length of the fading tails
	var PALETTE = [[255, 180, 84], [143, 184, 255], [255, 143, 163], [158, 240, 200], [236, 226, 255]];

	var desktopQuery = window.matchMedia('(hover: hover) and (pointer: fine) and (min-width: 768px)');
	var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

	var hint = document.querySelector('.nbody-hint');
	var countEl = hint && hint.querySelector('.nbody-count');
	var clearBtn = hint && hint.querySelector('.nbody-clear');

	var active = false;
	var canvas = null, ctx = null, W = 0, H = 0;
	var parts = [], rings = [];
	var mouse = { x: 0, y: 0, tx: 0, ty: 0, seen: false };
	var raf = 0, last = 0, acc = 0;

	if (window.NBODY_DEBUG) {   // test hook, only present when a test sets the flag first
		window.__nbody = function () { return { parts: parts, mouse: mouse, width: W, height: H }; };
	}

	/* ---------- physics ---------- */
	function computeAccel() {
		var i, j, p, q, dx, dy, d2, inv;
		var e2m = EPS_MOUSE * EPS_MOUSE, e2p = EPS_PART * EPS_PART;
		for (i = 0; i < parts.length; i++) {
			p = parts[i];
			dx = mouse.x - p.x;
			dy = mouse.y - p.y;
			d2 = dx * dx + dy * dy + e2m;
			inv = GM_MOUSE / (d2 * Math.sqrt(d2));
			p.ax = dx * inv;
			p.ay = dy * inv;
		}
		for (i = 0; i < parts.length; i++) {
			p = parts[i];
			for (j = i + 1; j < parts.length; j++) {
				q = parts[j];
				dx = q.x - p.x;
				dy = q.y - p.y;
				d2 = dx * dx + dy * dy + e2p;
				inv = GM_PART / (d2 * Math.sqrt(d2));
				p.ax += dx * inv; p.ay += dy * inv;
				q.ax -= dx * inv; q.ay -= dy * inv;
			}
		}
	}

	function step(dt) {
		var k = 1 - Math.exp(-25 * dt);        // the pulling mass eases towards the cursor
		mouse.x += (mouse.tx - mouse.x) * k;
		mouse.y += (mouse.ty - mouse.y) * k;
		var damp = Math.exp(-DRAG * dt);
		var i, p, v;
		for (i = 0; i < parts.length; i++) {   // kick-drift-kick leapfrog
			p = parts[i];
			p.vx += 0.5 * dt * p.ax;
			p.vy += 0.5 * dt * p.ay;
			p.x += p.vx * dt;
			p.y += p.vy * dt;
			if (p.x < p.r) { p.x = p.r; if (p.vx < 0) { p.vx = -p.vx * RESTITUTION; } }
			else if (p.x > W - p.r) { p.x = W - p.r; if (p.vx > 0) { p.vx = -p.vx * RESTITUTION; } }
			if (p.y < p.r) { p.y = p.r; if (p.vy < 0) { p.vy = -p.vy * RESTITUTION; } }
			else if (p.y > H - p.r) { p.y = H - p.r; if (p.vy > 0) { p.vy = -p.vy * RESTITUTION; } }
		}
		computeAccel();
		for (i = 0; i < parts.length; i++) {
			p = parts[i];
			p.vx = (p.vx + 0.5 * dt * p.ax) * damp;
			p.vy = (p.vy + 0.5 * dt * p.ay) * damp;
			v = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
			if (v > VMAX) { p.vx *= VMAX / v; p.vy *= VMAX / v; }
		}
	}

	/* ---------- drawing ---------- */
	function rgba(c, a) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }

	function draw(dt) {
		var i, j, p, g, a, t;
		ctx.clearRect(0, 0, W, H);

		if (parts.length) {                     // faint glow marking the pulling mass
			g = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 110);
			g.addColorStop(0, 'rgba(255,180,84,0.10)');
			g.addColorStop(1, 'rgba(255,180,84,0)');
			ctx.fillStyle = g;
			ctx.fillRect(mouse.x - 110, mouse.y - 110, 220, 220);
		}

		for (i = rings.length - 1; i >= 0; i--) {   // little ripple where you clicked
			t = rings[i];
			t.age += dt;
			if (t.age > 0.6) { rings.splice(i, 1); continue; }
			ctx.beginPath();
			ctx.arc(t.x, t.y, 6 + t.age * 90, 0, 6.2832);
			ctx.strokeStyle = rgba([255, 180, 84], (1 - t.age / 0.6) * 0.7);
			ctx.lineWidth = 2;
			ctx.stroke();
		}

		ctx.lineCap = 'round';
		for (i = 0; i < parts.length; i++) {
			p = parts[i];
			p.trail.push(p.x, p.y);
			if (p.trail.length > TRAIL * 2) { p.trail.splice(0, 2); }
			for (j = 2; j < p.trail.length; j += 2) {
				a = j / p.trail.length;
				ctx.beginPath();
				ctx.moveTo(p.trail[j - 2], p.trail[j - 1]);
				ctx.lineTo(p.trail[j], p.trail[j + 1]);
				ctx.strokeStyle = rgba(p.c, a * 0.5);
				ctx.lineWidth = p.r * 1.3 * a;
				ctx.stroke();
			}
		}
		for (i = 0; i < parts.length; i++) {
			p = parts[i];
			g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
			g.addColorStop(0, rgba(p.c, 0.55));
			g.addColorStop(1, rgba(p.c, 0));
			ctx.fillStyle = g;
			ctx.beginPath();
			ctx.arc(p.x, p.y, p.r * 4, 0, 6.2832);
			ctx.fill();
			ctx.fillStyle = rgba([255, 255, 255], 0.95);
			ctx.beginPath();
			ctx.arc(p.x, p.y, p.r * 0.8, 0, 6.2832);
			ctx.fill();
			ctx.strokeStyle = rgba(p.c, 1);
			ctx.lineWidth = 1.5;
			ctx.stroke();
		}
	}

	function frame(ts) {
		raf = window.requestAnimationFrame(frame);
		var dt = Math.min((ts - last) / 1000, 0.05);
		last = ts;
		acc += dt;
		while (acc >= DT) { step(DT); acc -= DT; }
		draw(dt);
		if (!parts.length && !rings.length) {   // nothing left to animate: stop until the next click
			window.cancelAnimationFrame(raf);
			raf = 0;
			ctx.clearRect(0, 0, W, H);
		}
	}

	function ensureRunning() {
		if (raf) { return; }
		last = window.performance.now();
		acc = 0;
		raf = window.requestAnimationFrame(frame);
	}

	/* ---------- canvas / state ---------- */
	function sizeCanvas() {
		var dpr = Math.min(window.devicePixelRatio || 1, 2);
		W = window.innerWidth;
		H = window.innerHeight;
		canvas.width = Math.round(W * dpr);
		canvas.height = Math.round(H * dpr);
		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		parts.forEach(function (p) {
			p.x = Math.min(Math.max(p.x, p.r), W - p.r);
			p.y = Math.min(Math.max(p.y, p.r), H - p.r);
		});
	}

	function updateHud() {
		if (!hint) { return; }
		var n = parts.length;
		countEl.textContent = n >= MAX
			? MAX + ' / ' + MAX + ' – a full N-body system!'
			: n + ' / ' + MAX;
		clearBtn.hidden = n === 0;
	}

	function enable() {
		if (active) { return; }
		active = true;
		canvas = document.createElement('canvas');
		canvas.className = 'nbody-canvas';
		canvas.setAttribute('aria-hidden', 'true');
		document.body.appendChild(canvas);
		ctx = canvas.getContext('2d');
		sizeCanvas();
		document.documentElement.classList.add('nbody-on');
		updateHud();
	}

	function disable() {
		if (!active) { return; }
		active = false;
		if (raf) { window.cancelAnimationFrame(raf); raf = 0; }
		parts = [];
		rings = [];
		if (canvas && canvas.parentNode) { canvas.parentNode.removeChild(canvas); }
		canvas = ctx = null;
		document.documentElement.classList.remove('nbody-on');
	}

	function clearAll() {
		parts = [];
		rings = [];
		if (ctx) { ctx.clearRect(0, 0, W, H); }
		updateHud();
	}

	function spawn(x, y) {
		if (parts.length >= MAX) { return; }
		var angle = Math.random() * 6.2832;
		var speed = 140 + Math.random() * 160;
		if (!mouse.seen) { mouse.x = mouse.tx = x; mouse.y = mouse.ty = y; mouse.seen = true; }
		parts.push({
			x: x, y: y,
			vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
			ax: 0, ay: 0,
			r: 3.5 + Math.random() * 2.5,
			c: PALETTE[parts.length % PALETTE.length],
			trail: []
		});
		rings.push({ x: x, y: y, age: 0 });
		computeAccel();
		updateHud();
		ensureRunning();
	}

	/* ---------- events ---------- */
	var INTERACTIVE = 'a, button, input, textarea, select, summary, label, [role="button"]';

	document.addEventListener('click', function (e) {
		if (!active || e.button !== 0) { return; }
		if (e.target.closest && e.target.closest(INTERACTIVE)) { return; }
		var selection = window.getSelection && window.getSelection().toString();
		if (selection) { return; }
		spawn(e.clientX, e.clientY);
	});

	document.addEventListener('mousemove', function (e) {
		mouse.tx = e.clientX;
		mouse.ty = e.clientY;
		if (!mouse.seen) { mouse.x = mouse.tx; mouse.y = mouse.ty; mouse.seen = true; }
	});

	window.addEventListener('resize', function () { if (active) { sizeCanvas(); } });

	if (clearBtn) { clearBtn.addEventListener('click', clearAll); }

	function evaluate() {
		if (desktopQuery.matches && !motionQuery.matches) { enable(); } else { disable(); }
	}
	[desktopQuery, motionQuery].forEach(function (q) {
		if (q.addEventListener) { q.addEventListener('change', evaluate); } else if (q.addListener) { q.addListener(evaluate); }
	});
	evaluate();
}());
