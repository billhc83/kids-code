let _rendererUidCounter = 0;

function _ensureDefs(renderer) {
  let defs = renderer.svgEl.querySelector('defs');
  if (!defs) {
    defs = renderer._el('defs', {});
    renderer.svgEl.insertBefore(defs, renderer.svgEl.firstChild);
  }
  return defs;
}

/**
 * Register a gradient/filter only once per SVG render pass.
 * IDs are prefixed with the renderer's UID so multiple renderers on the
 * same page don't share gradient elements — sharing breaks in Chrome when
 * the first SVG is hidden (display:none) and url(#id) can't resolve it.
 * Returns the scoped id for use in fill="url(#id)".
 */
function _defOnce(renderer, id, builderFn) {
  const localId = renderer._uid + '_' + id;
  const defs = _ensureDefs(renderer);
  if (!defs.querySelector('#' + localId)) builderFn(renderer, defs, localId);
  return localId;
}
 
/** Shorthand: create element via renderer and append to defs. */
function _d(renderer, tag, attrs) {
  const e = renderer._el(tag, attrs);
  return e;
}
 
// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT RENDERERS
// ─────────────────────────────────────────────────────────────────────────────
 
const SYMBOL_RENDERERS = {
 
  // ── LED ────────────────────────────────────────────────────────────────────
  // pins.anode   — breadboard hole where the anode (long leg) inserts.
  // pins.cathode — breadboard hole where the cathode (short leg) inserts.
  // Rotation is derived from the anode→cathode direction so orientation is exact.
  LED: function(renderer, pins, props) {
    const c = props && props.color;
 
    const palettes = {
      red:    { body: '#FF3333', dark: '#AA1111', glow: '#FF000044', rim: '#CC2222' },
      green:  { body: '#33DD55', dark: '#118833', glow: '#00FF4433', rim: '#22AA44' },
      yellow: { body: '#FFEE22', dark: '#AAAA00', glow: '#FFFF0033', rim: '#CCBB00' },
      blue:   { body: '#3399FF', dark: '#1144BB', glow: '#0066FF33', rim: '#2266CC' },
      white:  { body: '#EEEEFF', dark: '#9999BB', glow: '#FFFFFF33', rim: '#AAAACC' },
    };
    const pal = palettes[c] || palettes.red;
 
    // ── Defs ──
    const domeGradId = _defOnce(renderer, 'ledDomeGrad_' + (c || 'red'), function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '36%', cy: '30%', r: '65%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#FFFFFF', 'stop-opacity': '0.75' }));
      rg.appendChild(r._el('stop', { offset: '45%',  'stop-color': pal.body }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': pal.dark }));
      defs.appendChild(rg);
    });
 
    const bodyGradId = _defOnce(renderer, 'ledBodyGrad_' + (c || 'red'), function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '100%', y2: '0%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': pal.dark }));
      lg.appendChild(r._el('stop', { offset: '35%',  'stop-color': pal.body, 'stop-opacity': '0.65' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': pal.dark }));
      defs.appendChild(lg);
    });
 
    const glowFiltId = _defOnce(renderer, 'ledGlowFilt', function(r, defs, id) {
      const f = r._el('filter', { id, x: '-80%', y: '-80%', width: '260%', height: '260%' });
      f.appendChild(r._el('feGaussianBlur', { stdDeviation: '0.25', result: 'blur' }));
      const fm = r._el('feMerge', {});
      fm.appendChild(r._el('feMergeNode', { in: 'blur' }));
      fm.appendChild(r._el('feMergeNode', { in: 'SourceGraphic' }));
      f.appendChild(fm);
      defs.appendChild(f);
    });
 
    const x  = pins.anode.x;
    const y  = pins.anode.y;
    const angle = -Math.atan2(pins.cathode.x - x, pins.cathode.y - y) * 180 / Math.PI;
    const cy = y + 0.45;   // dome centre Y

    const _origAppendLED = renderer.svgEl.appendChild.bind(renderer.svgEl);
    const _grpLED = renderer._el('g', { transform: 'rotate(' + angle + ',' + x + ',' + y + ')' });
    renderer.svgEl.appendChild = function(el) { return _grpLED.appendChild(el); };

    // Soft ambient glow (behind everything)
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: cy, r: 0.55,
      fill: pal.glow,
      filter: 'url(#' + glowFiltId + ')'
    }));
 
    // Cylindrical body
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - 0.33, y: cy + 0.08, width: 0.66, height: 0.35,
      rx: 0.06,
      fill: 'url(#' + bodyGradId + ')',
      stroke: '#333', 'stroke-width': 0.05
    }));
 
    // Left-edge body sheen
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - 0.33, y: cy + 0.08, width: 0.11, height: 0.35,
      rx: 0.06,
      fill: '#FFFFFF', 'fill-opacity': 0.12
    }));
 
    // Flat rim / flange
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - 0.36, y: cy + 0.41, width: 0.72, height: 0.08,
      rx: 0.04,
      fill: '#555', stroke: '#333', 'stroke-width': 0.04
    }));
 
    // Cathode flat marker (internal stripe, shorter side)
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x + 0.08, y1: cy + 0.12, x2: x + 0.08, y2: cy + 0.41,
      stroke: pal.dark, 'stroke-width': 0.16, 'stroke-opacity': 0.6
    }));
 
    // Anode lead — longer, left of centre
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: cy - 0.35, x2: x, y2: y,
      stroke: '#BBBBBB', 'stroke-width': 0.1, 'stroke-linecap': 'round'
    }));
 
    // Cathode lead — shorter, right of centre
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: cy + 0.49, x2: x, y2: y + 1,
      stroke: '#BBBBBB', 'stroke-width': 0.1, 'stroke-linecap': 'round'
    }));
 
    // Dome (drawn on top of body)
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: cy, r: 0.35,
      fill: 'url(#' + domeGradId + ')',
      stroke: '#333', 'stroke-width': 0.05
    }));
 
    // Primary specular highlight
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.11, cy: cy - 0.11, rx: 0.11, ry: 0.075,
      fill: '#FFFFFF', 'fill-opacity': 0.78,
      transform: 'rotate(-30,' + (x - 0.11) + ',' + (cy - 0.11) + ')'
    }));
 
    // Secondary soft highlight
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.03, cy: cy + 0.08, rx: 0.05, ry: 0.035,
      fill: '#FFFFFF', 'fill-opacity': 0.25
    }));

    renderer.svgEl.appendChild = _origAppendLED;
    _origAppendLED(_grpLED);
  },


  // ── RESISTOR ───────────────────────────────────────────────────────────────
  // pins.pin1 — one lead hole (either end).
  // pins.pin2 — other lead hole.
  // Center, rotation, and lead length are all derived from the two pin positions.
  RESISTOR: function(renderer, pins, props) {
    const ohms = (props && props.ohms) || 220;
 
    // Standard 4-band colour code lookup
    const bandTable = {
      100:   ['#8B4513', '#000000', '#8B4513', '#FFD700'],
      220:   ['#FF2222', '#FF2222', '#8B4513', '#FFD700'],
      330:   ['#FF8C00', '#FF8C00', '#8B4513', '#FFD700'],
      470:   ['#FFFF00', '#9400D3', '#8B4513', '#FFD700'],
      1000:  ['#8B4513', '#000000', '#FF2222', '#FFD700'],
      4700:  ['#FFFF00', '#9400D3', '#FF2222', '#FFD700'],
      10000: ['#8B4513', '#000000', '#FF8C00', '#FFD700'],
    };
    const bands = bandTable[ohms] || bandTable[220];
    const label = ohms >= 1000 ? (ohms / 1000) + 'k' : ohms + '';
 
    const bodyGradId = _defOnce(renderer, 'resBodyGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '100%', y2: '0%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#8B7355' }));
      lg.appendChild(r._el('stop', { offset: '20%',  'stop-color': '#C8A96E' }));
      lg.appendChild(r._el('stop', { offset: '50%',  'stop-color': '#D4B483' }));
      lg.appendChild(r._el('stop', { offset: '80%',  'stop-color': '#C8A96E' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#8B7355' }));
      defs.appendChild(lg);
    });
 
    const p1 = pins.pin1;
    const p2 = pins.pin2;
    const x = (p1.x + p2.x) / 2;
    const y = (p1.y + p2.y) / 2;
    const halfDist = Math.sqrt((p2.x - p1.x) * (p2.x - p1.x) + (p2.y - p1.y) * (p2.y - p1.y)) / 2;
    const angle = -Math.atan2(p2.x - x, p2.y - y) * 180 / Math.PI;
    const bodyH = 1.6;
    const bodyW = 0.75;
    const bodyTop = y - bodyH / 2;

    const _origAppendRES = renderer.svgEl.appendChild.bind(renderer.svgEl);
    const _grpRES = renderer._el('g', { transform: 'rotate(' + angle + ',' + x + ',' + y + ')' });
    renderer.svgEl.appendChild = function(el) { return _grpRES.appendChild(el); };

    // Lead to pin1 (pre-rotation: upward from body top to y - halfDist)
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: y - halfDist, x2: x, y2: bodyTop,
      stroke: '#CCCCCC', 'stroke-width': 0.09, 'stroke-linecap': 'round'
    }));

    // Lead to pin2 (pre-rotation: downward from body bottom to y + halfDist)
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: bodyTop + bodyH, x2: x, y2: y + halfDist,
      stroke: '#CCCCCC', 'stroke-width': 0.09, 'stroke-linecap': 'round'
    }));

    // Body drop shadow
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bodyW / 2 + 0.04, y: bodyTop + 0.05,
      width: bodyW, height: bodyH, rx: 0.22,
      fill: '#00000033'
    }));

    // Body
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bodyW / 2, y: bodyTop,
      width: bodyW, height: bodyH, rx: 0.22,
      fill: 'url(#' + bodyGradId + ')',
      stroke: '#665533', 'stroke-width': 0.045
    }));

    // Top sheen
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bodyW / 2 + 0.06, y: bodyTop + 0.07,
      width: bodyW - 0.12, height: bodyH * 0.32, rx: 0.16,
      fill: '#FFFFFF', 'fill-opacity': 0.14
    }));

    // Colour bands — 3 value bands at 25%, 44%, 63% + tolerance at 82%
    const bandFracs = [0.25, 0.44, 0.63, 0.82];
    bands.forEach(function(color, i) {
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: x - bodyW / 2 + 0.045, y: bodyTop + bodyH * bandFracs[i] - 0.06,
        width: bodyW - 0.09, height: 0.13,
        fill: color, 'fill-opacity': 0.92,
        stroke: '#00000022', 'stroke-width': 0.3
      }));
    });

    renderer.svgEl.appendChild = _origAppendRES;
    _origAppendRES(_grpRES);
  },
 
 
  // ── BUTTON ─────────────────────────────────────────────────────────────────
  // pins.TL / pins.TR / pins.BL / pins.BR — the four leg holes.
  // Center is derived as the average of all four pin positions.
  BUTTON: function(renderer, pins, props) {
    const capColor = (props && props.color) || '#CC2222';

    const capGradId = _defOnce(renderer, 'btnCapGrad_' + capColor.replace('#',''), function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '36%', cy: '30%', r: '66%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#FFFFFF', 'stop-opacity': '0.55' }));
      rg.appendChild(r._el('stop', { offset: '50%',  'stop-color': capColor }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#661111' }));
      defs.appendChild(rg);
    });

    const baseGradId = _defOnce(renderer, 'btnBaseGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#4a4a4a' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#1a1a1a' }));
      defs.appendChild(lg);
    });

    const x  = (pins.TL.x + pins.TR.x + pins.BL.x + pins.BR.x) / 4;
    const y  = (pins.TL.y + pins.TR.y + pins.BL.y + pins.BR.y) / 4;
    // 6×6 mm body — spans the E/F gap (2 SVG units) in both axes
    const bw = 1.8,  bh = 1.8;

    // Legs: real tactile-button legs exit the bottom corners of the housing
    // and bend outward into the breadboard holes.  Each leg runs from the
    // body base-corner (same left/right side as the pin) down to the pin hole.
    [pins.TL, pins.TR, pins.BL, pins.BR].forEach(function(pin) {
      const bx = x + (pin.x >= x ? bw / 2 : -bw / 2);  // left or right side
      const by = y + bh / 2;                             // always the base of the body
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: bx, y1: by, x2: pin.x, y2: pin.y,
        stroke: '#CCCCCC', 'stroke-width': 0.12, 'stroke-linecap': 'round'
      }));
    });
 
    // Base body shadow
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2 + 0.07, y: y - bh / 2 + 0.09,
      width: bw, height: bh, rx: 0.1,
      fill: '#00000055'
    }));
 
    // Base body
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2, y: y - bh / 2,
      width: bw, height: bh, rx: 0.1,
      fill: 'url(#' + baseGradId + ')',
      stroke: '#222', 'stroke-width': 0.06
    }));
 
    // Base sheen
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2 + 0.1, y: y - bh / 2 + 0.09,
      width: bw - 0.2, height: bh * 0.28, rx: 0.08,
      fill: '#FFFFFF', 'fill-opacity': 0.07
    }));

    // Diagonal continuity marks — TL↔BR and TR↔BL are internally shorted on this SPST switch
    const _hw = bw / 2 - 0.18, _hh = bh / 2 - 0.18;
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x - _hw, y1: y - _hh, x2: x + _hw, y2: y + _hh,
      stroke: '#FFFFFF', 'stroke-width': 0.07, 'stroke-opacity': 0.22,
      'stroke-dasharray': '0.18 0.1'
    }));
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x + _hw, y1: y - _hh, x2: x - _hw, y2: y + _hh,
      stroke: '#FFFFFF', 'stroke-width': 0.07, 'stroke-opacity': 0.22,
      'stroke-dasharray': '0.18 0.1'
    }));

    // Cap — top-down view: a round dome centered on the body (what you see from above).
    // No stem needed — we're looking straight down at the button.
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: y,
      r: 0.55,
      fill: 'url(#' + capGradId + ')',
      stroke: '#881111', 'stroke-width': 0.05
    }));

    // Cap specular highlight (top-left glint)
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.18, cy: y - 0.18,
      rx: 0.16, ry: 0.10,
      fill: '#FFFFFF', 'fill-opacity': 0.60,
      transform: 'rotate(-30,' + (x - 0.18) + ',' + (y - 0.18) + ')'
    }));
  },
 
 
  // ── BUZZER ─────────────────────────────────────────────────────────────────
  // pins.positive — breadboard hole for the positive (+) lead.
  // pins.negative — breadboard hole for the negative (−) lead.
  // Center is the midpoint; leads are drawn to the actual pin positions.
  BUZZER: function(renderer, pins, props) {
    const bodyGradId = _defOnce(renderer, 'buzzBodyGrad', function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '38%', cy: '33%', r: '66%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#555555' }));
      rg.appendChild(r._el('stop', { offset: '55%',  'stop-color': '#2a2a2a' }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#111111' }));
      defs.appendChild(rg);
    });
 
    const x = (pins.positive.x + pins.negative.x) / 2;
    const y = (pins.positive.y + pins.negative.y) / 2;
    const r = 2.0;
 
    // Shadow
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x + 0.16, cy: y + 0.22, rx: r + 0.1, ry: r + 0.1,
      fill: '#00000055'
    }));
 
    // Main disc body
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: y, r: r,
      fill: 'url(#' + bodyGradId + ')',
      stroke: '#111', 'stroke-width': 0.06
    }));
 
    // Concentric membrane rings
    [0.55, 0.68, 0.81].forEach(function(rf) {
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: x, cy: y, r: r * rf,
        fill: 'none', stroke: '#444', 'stroke-width': 0.04
      }));
    });
 
    // Centre vent holes
    [[-0.28, -0.28], [0.28, -0.28], [0, 0.35],
     [-0.28, 0.28],  [0.28, 0.28]].forEach(function(d) {
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: x + d[0], cy: y + d[1], r: 0.13,
        fill: '#111'
      }));
    });
 
    // Top sheen
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.66, cy: y - 0.78, rx: 0.75, ry: 0.42,
      fill: '#FFFFFF', 'fill-opacity': 0.09,
      transform: 'rotate(-28,' + (x - 0.66) + ',' + (y - 0.78) + ')'
    }));
 
    
    // Leads — exit body edge toward each pin, then continue to the breadboard hole
    [
      { pin: pins.positive, color: '#FFDD88' },
      { pin: pins.negative, color: '#CCCCCC' },
    ].forEach(function(leg) {
      const dx = leg.pin.x - x;
      const dy = leg.pin.y - y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
      const ex = x + r * (dx / dist);
      const ey = y + r * (dy / dist);
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: ex, y1: ey, x2: leg.pin.x, y2: leg.pin.y,
        stroke: leg.color, 'stroke-width': 0.1, 'stroke-linecap': 'round'
      }));
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: leg.pin.x, cy: leg.pin.y, r: 0.09,
        fill: leg.color
      }));
    });
 
    // Sound arc (kept — it's a nice schematic hint)
    renderer.svgEl.appendChild(renderer._el('path', {
      d: 'M ' + (x - 0.89) + ' ' + (y - r - 0.18) +
         ' Q ' + x + ' ' + (y - r - 1.22) +
         ' ' + (x + 0.89) + ' ' + (y - r - 0.18),
      fill: 'none', stroke: '#888', 'stroke-width': 0.1,
      'stroke-linecap': 'round'
    }));
    renderer.svgEl.appendChild(renderer._el('path', {
      d: 'M ' + (x - 1.29) + ' ' + (y - r - 0.52) +
         ' Q ' + x + ' ' + (y - r - 1.93) +
         ' ' + (x + 1.29) + ' ' + (y - r - 0.52),
      fill: 'none', stroke: '#666', 'stroke-width': 0.08,
      'stroke-linecap': 'round'
    }));
  },
 
 
  // ── SERVO ──────────────────────────────────────────────────────────────────
  // Off-breadboard component. pins.body positions the centre of the servo body
  // using any convenient breadboard hole as a visual anchor.
  // Falls back to computing the body centre from signal/power/ground pins when
  // pins.body is absent (circuit engine auto-placement path).
  SERVO: function(renderer, pins, props) {
    const bodyGradId = _defOnce(renderer, 'servoBodyGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#4a90d9' }));
      lg.appendChild(r._el('stop', { offset: '45%',  'stop-color': '#2266AA' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#114477' }));
      defs.appendChild(lg);
    });

    const hornGradId = _defOnce(renderer, 'servoHornGrad', function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '38%', cy: '32%', r: '66%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#EEEEEE' }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#888888' }));
      defs.appendChild(rg);
    });

    let x, y;
    if (pins.body) {
      x = pins.body.x; y = pins.body.y;
    } else {
      // Derive body centre from wiring pins: average row position, offset above connector
      const wPins = [pins.signal, pins.power, pins.ground].filter(Boolean);
      x = wPins.reduce(function(s, p) { return s + p.x; }, 0) / wPins.length;
      y = (pins.power || wPins[0]).y - 3.2;
    }
    const bw = 2.8, bh = 1.8;
 
    // Body shadow
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2 + 0.08, y: y - bh / 2 + 0.1,
      width: bw, height: bh, rx: 0.2, fill: '#00000055'
    }));
 
    // Main body
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2, y: y - bh / 2,
      width: bw, height: bh, rx: 0.18,
      fill: 'url(#' + bodyGradId + ')',
      stroke: '#112255', 'stroke-width': 0.07
    }));
 
    // Body sheen
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - bw / 2 + 0.12, y: y - bh / 2 + 0.1,
      width: bw - 0.24, height: bh * 0.3, rx: 0.12,
      fill: '#FFFFFF', 'fill-opacity': 0.11
    }));
 
    // Mounting ears (left and right tabs)
    [x - bw / 2 - 0.3, x + bw / 2].forEach(function(ex) {
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: ex, y: y - bh * 0.28,
        width: 0.3, height: bh * 0.56, rx: 0.06,
        fill: '#1A4477', stroke: '#112255', 'stroke-width': 0.04
      }));
      // Ear mounting hole
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: ex + 0.15, cy: y, r: 0.09, fill: '#0a2244'
      }));
    });
 
    // Output shaft housing (on top)
    const shaftCX = x - bw * 0.12;
    const shaftCY = y - bh / 2 + 0.02;
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: shaftCX, cy: shaftCY, r: 0.42,
      fill: '#1A4477', stroke: '#112255', 'stroke-width': 0.06
    }));
 
    // Horn arm
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: shaftCX - 0.12, y: shaftCY - 0.78,
      width: 0.24, height: 0.82, rx: 0.1,
      fill: 'url(#' + hornGradId + ')',
      stroke: '#888', 'stroke-width': 0.04
    }));
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: shaftCX, cy: shaftCY - 0.78, r: 0.15,
      fill: 'url(#' + hornGradId + ')',
      stroke: '#888', 'stroke-width': 0.04
    }));
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: shaftCX, cy: shaftCY, r: 0.14,
      fill: '#2266AA', stroke: '#112255', 'stroke-width': 0.04
    }));
 
    // 3-wire connector block — each wire lands on its actual breadboard pin hole.
    // Rows are 1 SVG unit apart on the x-axis, so we use pin coords directly
    // instead of fixed dx offsets (which were wrong in both position and order).
    const wireBaseY = y + bh / 2;
    const wires = [
      { pin: pins.signal, fallback: x + 0.5,  color: '#FF8800', label: 'S' },
      { pin: pins.power,  fallback: x - 0.5,  color: '#CC2222', label: '+' },
      { pin: pins.ground, fallback: x - 1.5,  color: '#7B3F00', label: '−' },
    ];
    wires.forEach(function(w) {
      const wx    = w.pin ? w.pin.x : w.fallback;
      const wyEnd = w.pin ? w.pin.y : wireBaseY + 1.5;
      // Connector pin housing
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: wx - 0.18, y: wireBaseY,
        width: 0.36, height: 0.28, rx: 0.04,
        fill: '#333', stroke: '#222', 'stroke-width': 0.03
      }));
      // Wire lead — extends all the way to the breadboard pin hole
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: wx, y1: wireBaseY + 0.28, x2: wx, y2: wyEnd,
        stroke: w.color, 'stroke-width': 0.13, 'stroke-linecap': 'round'
      }));
      // Terminal dot at pin hole
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: wx, cy: wyEnd, r: 0.09, fill: w.color
      }));
    });
  },


  // ── LDR (Light Dependent Resistor / Photoresistor) ─────────────────────────
  // Analog sensor — no polarity, legs are interchangeable.
  // Wiring rules for Arduino:
  //   • Must use a voltage divider: LDR in series with a 10kΩ pull-down resistor.
  //   • One LDR leg → 5V; other LDR leg → analog pin (A0–A5) AND resistor lead.
  //   • Resistor's other lead → GND.
  //   • Read with analogRead(pin) — returns 0–1023 (brighter = lower resistance = higher reading).
  //   • Never connect directly between 5V and GND without the series resistor.
  // pins.pin1 — breadboard hole for one leg (either end).
  // pins.pin2 — breadboard hole for the other leg.
  LDR: function(renderer, pins, props) {
    const p1 = pins.pin1;
    const p2 = pins.pin2;
    const x = (p1.x + p2.x) / 2;
    const y = (p1.y + p2.y) / 2;
    const halfDist = Math.sqrt((p2.x - p1.x) * (p2.x - p1.x) + (p2.y - p1.y) * (p2.y - p1.y)) / 2;
    const angle = -Math.atan2(p2.x - x, p2.y - y) * 180 / Math.PI;
    const bodyR = 0.72;

    const domeGradId = _defOnce(renderer, 'ldrDomeGrad', function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '38%', cy: '32%', r: '66%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#FFFFFF', 'stop-opacity': '0.82' }));
      rg.appendChild(r._el('stop', { offset: '45%',  'stop-color': '#E8E2BE' }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#A89A68' }));
      defs.appendChild(rg);
    });

    const _origAppendLDR = renderer.svgEl.appendChild.bind(renderer.svgEl);
    const _grpLDR = renderer._el('g', { transform: 'rotate(' + angle + ',' + x + ',' + y + ')' });
    renderer.svgEl.appendChild = function(el) { return _grpLDR.appendChild(el); };

    // Leads
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: y - halfDist, x2: x, y2: y - bodyR,
      stroke: '#BBBBBB', 'stroke-width': 0.09, 'stroke-linecap': 'round'
    }));
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x, y1: y + bodyR, x2: x, y2: y + halfDist,
      stroke: '#BBBBBB', 'stroke-width': 0.09, 'stroke-linecap': 'round'
    }));

    // Drop shadow
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x + 0.06, cy: y + 0.08, r: bodyR + 0.05,
      fill: '#00000033'
    }));

    // Body disc
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: y, r: bodyR,
      fill: 'url(#' + domeGradId + ')',
      stroke: '#7A7050', 'stroke-width': 0.06
    }));

    // CdS serpentine track — 4-pass zigzag (the characteristic LDR pattern)
    const tw = 0.44, th = 0.44;
    const passes = 4;
    const rowH = (th * 2) / passes;
    let trackD = 'M ' + (x - tw) + ' ' + (y - th);
    for (let i = 0; i < passes; i++) {
      const yy = y - th + i * rowH;
      trackD += (i % 2 === 0) ? (' H ' + (x + tw)) : (' H ' + (x - tw));
      if (i < passes - 1) trackD += ' V ' + (yy + rowH);
    }
    renderer.svgEl.appendChild(renderer._el('path', {
      d: trackD,
      fill: 'none',
      stroke: '#6B4E1E',
      'stroke-width': 0.105,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round'
    }));

    // Light-arrow indicators (diagonal arrows in upper-right, pointing at body)
    [
      [x + 0.90, y - 0.90, x + 0.66, y - 0.66],
      [x + 1.06, y - 0.66, x + 0.82, y - 0.42],
    ].forEach(function(arr) {
      const ax1 = arr[0], ay1 = arr[1], ax2 = arr[2], ay2 = arr[3];
      const ddx = ax2 - ax1, ddy = ay2 - ay1;
      const len = Math.sqrt(ddx * ddx + ddy * ddy) || 0.001;
      const nx = ddx / len, ny = ddy / len;
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: ax1, y1: ay1, x2: ax2, y2: ay2,
        stroke: '#FFDD44', 'stroke-width': 0.075, 'stroke-linecap': 'round'
      }));
      const hs = 0.13;
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: ax2, y1: ay2,
        x2: ax2 - hs * (nx - ny), y2: ay2 - hs * (ny + nx),
        stroke: '#FFDD44', 'stroke-width': 0.075, 'stroke-linecap': 'round'
      }));
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: ax2, y1: ay2,
        x2: ax2 - hs * (nx + ny), y2: ay2 - hs * (ny - nx),
        stroke: '#FFDD44', 'stroke-width': 0.075, 'stroke-linecap': 'round'
      }));
    });

    // Glass sheen highlight
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.25, cy: y - 0.27,
      rx: 0.22, ry: 0.13,
      fill: '#FFFFFF', 'fill-opacity': 0.65,
      transform: 'rotate(-30,' + (x - 0.25) + ',' + (y - 0.27) + ')'
    }));

    renderer.svgEl.appendChild = _origAppendLDR;
    _origAppendLDR(_grpLDR);
  },


  // ── HC-SR04 (Ultrasonic Distance Sensor) ──────────────────────────────────
  // pins always in col J (bottommost breadboard column).
  // Side-on view: PCB edge at col J (py), cylinders extend DOWNWARD off the
  // board edge so the sensor faces outward — away from the breadboard.
  // x-axis (rows): 18 wide, cylinders left & right with pin gap in centre.
  HC_SR04: function(renderer, pins, props) {
    const pVcc  = pins.vcc;
    const pTrig = pins.trig;
    const pEcho = pins.echo;
    const pGnd  = pins.gnd;

    const cx = (pVcc.x + pGnd.x) / 2;  // horizontal centre of 4-pin group
    const py = pVcc.y;                   // col J y — all pins share this

    const bw     = 18;    // total board width (x)
    const pcbH   = 0.48;  // PCB edge thickness
    const cylRx  = 3.0;   // cylinder half-width (x)
    const cylBH  = 3.4;   // cylinder body height (y)
    const cylCap = 0.70;  // cylinder rounded-end cap height (y)
    const cylOff = 5.0;   // x-offset of each cylinder centre from cx

    // Cylinders grow DOWNWARD: PCB at py, cylinders start just below it.
    const cylTop = py + pcbH;

    // ── Gradients ──
    const pcbGradId = _defOnce(renderer, 'hcsrPcbGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#3A5A3A' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#1A3A1A' }));
      defs.appendChild(lg);
    });

    const cylGradId = _defOnce(renderer, 'hcsrCylGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '100%', y2: '0%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#383838' }));
      lg.appendChild(r._el('stop', { offset: '18%',  'stop-color': '#9C9C9C' }));
      lg.appendChild(r._el('stop', { offset: '44%',  'stop-color': '#E2E2E2' }));
      lg.appendChild(r._el('stop', { offset: '56%',  'stop-color': '#E2E2E2' }));
      lg.appendChild(r._el('stop', { offset: '82%',  'stop-color': '#9C9C9C' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#383838' }));
      defs.appendChild(lg);
    });

    const bodyX = cx - bw / 2;

    // Drop shadow
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: bodyX + 0.18, y: py + 0.18,
      width: bw, height: pcbH + cylBH + cylCap + 0.25, rx: 0.35,
      fill: '#00000045'
    }));

    // ── PCB edge (thin dark-green strip at col J) ──
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: bodyX, y: py,
      width: bw, height: pcbH, rx: 0.10,
      fill: 'url(#' + pcbGradId + ')',
      stroke: '#0A180A', 'stroke-width': 0.09
    }));

    // ── Two cylinders — grow downward, caps face outward off the board ──
    [-1, 1].forEach(function(side) {
      const txCtr = cx + side * cylOff;
      const txL   = txCtr - cylRx;

      // Cylinder rectangular body
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: txL, y: cylTop,
        width: cylRx * 2, height: cylBH,
        fill: 'url(#' + cylGradId + ')',
        stroke: '#282828', 'stroke-width': 0.12
      }));

      // Rounded far-end cap at BOTTOM (faces outward off board)
      renderer.svgEl.appendChild(renderer._el('ellipse', {
        cx: txCtr, cy: cylTop + cylBH,
        rx: cylRx, ry: cylCap,
        fill: 'url(#' + cylGradId + ')',
        stroke: '#282828', 'stroke-width': 0.12
      }));

      // PCB-end mounting collar (dark rim at top of cylinder where it meets PCB)
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: txL, y: cylTop,
        width: cylRx * 2, height: 0.28,
        fill: '#1C1C1C', stroke: 'none'
      }));

      // Emitting-face aperture at far (bottom) end
      const apRx = cylRx * 0.60;
      const apRy = cylCap * 0.50;
      const apCy = cylTop + cylBH + cylCap * 0.30;
      renderer.svgEl.appendChild(renderer._el('ellipse', {
        cx: txCtr, cy: apCy,
        rx: apRx, ry: apRy,
        fill: '#242424', stroke: '#444', 'stroke-width': 0.09
      }));
      renderer.svgEl.appendChild(renderer._el('ellipse', {
        cx: txCtr, cy: apCy,
        rx: apRx * 0.58, ry: apRy * 0.58,
        fill: 'none', stroke: '#585858', 'stroke-width': 0.08
      }));
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: txCtr, cy: apCy, r: 0.15, fill: '#686868'
      }));

      // Specular highlight strip along cylinder spine
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: txCtr - cylRx * 0.11, y: cylTop + 0.38,
        width: cylRx * 0.22, height: cylBH - 0.60,
        rx: 0.10, fill: '#FFFFFF', 'fill-opacity': 0.38
      }));
    });

    // ── Label — rotated vertically in gap between cylinders ──
    const midY = cylTop + (cylBH + cylCap) / 2;
    const lblEl = renderer._el('text', {
      x: cx, y: midY,
      'text-anchor': 'middle', 'dominant-baseline': 'central',
      'font-size': 0.52, fill: '#7EC87E',
      'font-family': 'monospace', 'font-weight': 'bold',
      transform: 'rotate(-90,' + cx + ',' + midY + ')'
    });
    lblEl.textContent = 'HC-SR04';
    renderer.svgEl.appendChild(lblEl);

    // ── Pins — gold pads at PCB edge; labels just inside the gap ──
    [
      { pin: pVcc,  label: 'V' },
      { pin: pTrig, label: 'T' },
      { pin: pEcho, label: 'E' },
      { pin: pGnd,  label: 'G' },
    ].forEach(function(pc) {
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: pc.pin.x, cy: py,
        r: 0.22, fill: '#FFD700', stroke: '#AA8800', 'stroke-width': 0.05
      }));
      const pt = renderer._el('text', {
        x: pc.pin.x, y: cylTop + 0.50,
        'text-anchor': 'middle',
        'font-size': 0.36, fill: '#B0C8B0',
        'font-family': 'monospace'
      });
      pt.textContent = pc.label;
      renderer.svgEl.appendChild(pt);
    });
  },


  // ── SLIDE SWITCH ───────────────────────────────────────────────────────────
  // pins.pin1 — unused throw terminal (away from Arduino).
  // pins.com  — common/wiper → Arduino signal wire.
  // pins.pin2 — active throw → GND.
  // All 3 pins share the same column (same y); body is centered on the pin row.
  // Actuator drawn at the pin1 end (switch in OFF position).
  SLIDE_SWITCH: function(renderer, pins, props) {
    const p1 = pins.pin1;
    const pC = pins.com;
    const p2 = pins.pin2;

    const cx = pC.x;
    const cy = pC.y;  // all pins same y (same breadboard column)

    const bw = 3.0;   // body width along x (row axis)
    const bh = 1.5;   // body depth along y (col axis)

    const bodyGradId = _defOnce(renderer, 'swBodyGrad', function(r, defs, id) {
      const lg = r._el('linearGradient', { id, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
      lg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#C8A870' }));
      lg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#8A6830' }));
      defs.appendChild(lg);
    });

    const actuatorGradId = _defOnce(renderer, 'swActuatorGrad', function(r, defs, id) {
      const rg = r._el('radialGradient', { id, cx: '36%', cy: '30%', r: '65%' });
      rg.appendChild(r._el('stop', { offset: '0%',   'stop-color': '#444444' }));
      rg.appendChild(r._el('stop', { offset: '100%', 'stop-color': '#111111' }));
      defs.appendChild(rg);
    });

    // Body shadow
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: cx - bw / 2 + 0.07, y: cy - bh / 2 + 0.09,
      width: bw, height: bh, rx: 0.15,
      fill: '#00000050'
    }));

    // Body (phenolic resin — warm tan)
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: cx - bw / 2, y: cy - bh / 2,
      width: bw, height: bh, rx: 0.15,
      fill: 'url(#' + bodyGradId + ')',
      stroke: '#6A5020', 'stroke-width': 0.07
    }));

    // Body top sheen
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: cx - bw / 2 + 0.12, y: cy - bh / 2 + 0.08,
      width: bw - 0.24, height: bh * 0.25, rx: 0.10,
      fill: '#FFFFFF', 'fill-opacity': 0.09
    }));

    // Gold pin pads at bottom edge of body
    [p1, pC, p2].forEach(function(pin) {
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: pin.x, cy: cy + bh / 2 - 0.12,
        r: 0.14, fill: '#D4AF37', stroke: '#9A7A00', 'stroke-width': 0.04
      }));
    });

    // Actuator slot (recessed track)
    const slotW = bw - 0.70;
    const slotH = bh * 0.42;
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: cx - slotW / 2, y: cy - slotH / 2,
      width: slotW, height: slotH, rx: 0.08,
      fill: '#1a1a1a', stroke: '#0a0a0a', 'stroke-width': 0.05
    }));

    // Actuator knob — shown at pin1 end (switch OFF)
    const knobW  = 0.62;
    const knobH  = slotH + 0.22;
    const knobCX = p1.x;
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: knobCX - knobW / 2, y: cy - knobH / 2,
      width: knobW, height: knobH, rx: 0.10,
      fill: 'url(#' + actuatorGradId + ')',
      stroke: '#2a2a2a', 'stroke-width': 0.05
    }));

    // Knob specular highlight
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: knobCX - knobW / 2 + 0.09, y: cy - knobH / 2 + 0.07,
      width: knobW - 0.18, height: knobH * 0.28, rx: 0.05,
      fill: '#FFFFFF', 'fill-opacity': 0.20
    }));
  }

};
SYMBOL_RENDERERS.LED.bbox = function(pins, props) {
  const domeCY = pins.anode.y + 0.45;
  const xMin = Math.min(pins.anode.x, pins.cathode.x) - 0.45;
  const xMax = Math.max(pins.anode.x, pins.cathode.x) + 0.45;
  const yMin = domeCY - 0.55;
  const yMax = Math.max(pins.cathode.y, pins.anode.y) + 0.1;
  return { x0: xMin - 0.5, y0: yMin - 0.5, x1: xMax + 0.5, y1: yMax + 0.5 };
};

SYMBOL_RENDERERS.RESISTOR.bbox = function(pins, props) {
  const xMin = Math.min(pins.pin1.x, pins.pin2.x) - 0.45;
  const xMax = Math.max(pins.pin1.x, pins.pin2.x) + 0.45;
  const yMin = Math.min(pins.pin1.y, pins.pin2.y) - 0.45;
  const yMax = Math.max(pins.pin1.y, pins.pin2.y) + 0.45;
  return { x0: xMin - 0.5, y0: yMin - 0.5, x1: xMax + 0.5, y1: yMax + 0.5 };
};

SYMBOL_RENDERERS.BUTTON.bbox = function(pins, props) {
  const cx = (pins.TL.x + pins.TR.x + pins.BL.x + pins.BR.x) / 4;
  const cy = (pins.TL.y + pins.TR.y + pins.BL.y + pins.BR.y) / 4;
  // y0 must clear cap dome: cy - bh/2(0.9) - stem(0.38) - dome_r(0.42) ≈ cy - 1.7
  return { x0: cx - 1.6, y0: cy - 2.2, x1: cx + 1.6, y1: cy + 1.4 };
};

SYMBOL_RENDERERS.BUZZER.bbox = function(pins, props) {
  const cx = (pins.positive.x + pins.negative.x) / 2;
  const cy = (pins.positive.y + pins.negative.y) / 2;
  return { x0: cx - 2.6, y0: cy - 2.6, x1: cx + 2.6, y1: cy + 2.6 };
};

SYMBOL_RENDERERS.SERVO.bbox = function(pins, props) {
  let bx, by;
  if (pins.body) {
    bx = pins.body.x; by = pins.body.y;
  } else {
    const wPins = [pins.signal, pins.power, pins.ground].filter(Boolean);
    bx = wPins.reduce(function(s, p) { return s + p.x; }, 0) / wPins.length;
    by = (pins.power || wPins[0]).y - 3.2;
  }
  // y1 must reach the pin holes: by = pinY - 3.2, so pinY = by + 3.2;
  // add 0.4 clearance below pin holes.
  return { x0: bx - 2.1, y0: by - 2.2, x1: bx + 2.1, y1: by + 3.6 };
};

SYMBOL_RENDERERS.LDR.bbox = function(pins, props) {
  const cx = (pins.pin1.x + pins.pin2.x) / 2;
  const cy = (pins.pin1.y + pins.pin2.y) / 2;
  // Extra clearance on upper-right for the light-arrow indicators
  return { x0: cx - 1.1, y0: cy - 1.4, x1: cx + 1.4, y1: cy + 1.1 };
};

SYMBOL_RENDERERS.HC_SR04.bbox = function(pins, props) {
  const cx    = (pins.vcc.x + pins.gnd.x) / 2;
  const py    = pins.vcc.y;   // col J — bottom of sensor (pin row)
  const bw    = 18;
  const totalH = 0.48 + 3.4 + 0.70;  // pcbH + cylBH + cylCap
  // Body grows DOWNWARD past col J; bbox covers the full physical area.
  return { x0: cx - bw / 2 - 0.5, y0: py - 0.5, x1: cx + bw / 2 + 0.5, y1: py + totalH + 0.5 };
};

SYMBOL_RENDERERS.SLIDE_SWITCH.bbox = function(pins, props) {
  const cx = pins.com.x;
  const cy = pins.com.y;
  const bw = 3.0, bh = 1.5;
  return { x0: cx - bw / 2 - 0.4, y0: cy - bh / 2 - 0.4, x1: cx + bw / 2 + 0.4, y1: cy + bh / 2 + 0.4 };
};

// ─────────────────────────────────────────────────────────────────────────────
// MIN-HEAP — used as the A* open set
// ─────────────────────────────────────────────────────────────────────────────
class MinHeap {
  constructor() { this._data = []; }

  get size() { return this._data.length; }

  push(item) {
    this._data.push(item);
    this._bubbleUp(this._data.length - 1);
  }

  pop() {
    const top = this._data[0];
    const last = this._data.pop();
    if (this._data.length > 0) {
      this._data[0] = last;
      this._siftDown(0);
    }
    return top;
  }

  _bubbleUp(i) {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this._data[p].f <= this._data[i].f) break;
      const tmp = this._data[p]; this._data[p] = this._data[i]; this._data[i] = tmp;
      i = p;
    }
  }

  _siftDown(i) {
    const n = this._data.length;
    while (true) {
      let min = i;
      const l = 2 * i + 1, r = 2 * i + 2;
      if (l < n && this._data[l].f < this._data[min].f) min = l;
      if (r < n && this._data[r].f < this._data[min].f) min = r;
      if (min === i) break;
      const tmp = this._data[min]; this._data[min] = this._data[i]; this._data[i] = tmp;
      i = min;
    }
  }
}

class CircuitRenderer {
  constructor(circuitDef, containerId) {
    this.def = circuitDef;
    this.container = document.getElementById(containerId);
    this.svgNS = 'http://www.w3.org/2000/svg';
    this.ARD_ANCHOR = { x: 4, y: 4 };
    this.BB_ANCHOR  = { x: 30, y: 4 };
    this.COL_OFFSETS = {
      '+1': 0, '-1': 1,
      'A': 3, 'B': 4, 'C': 5, 'D': 6, 'E': 7,
      'F': 9, 'G': 10, 'H': 11, 'I': 12, 'J': 13,
      '+2': 15, '-2': 16
    };
    this.PIN_DEFS = {};

    // Right edge (x:20) = physical "DIGITAL (PWM~)" header.
    // Board shown rotated 90° CW vs landscape photo (USB ends up at bottom).
    // After rotation, the top header becomes the right edge, reading top→bottom:
    //   AREF, GND, D13–D8  [physical gap between two 8-pin sub-headers]  D7–D0
    [
      ['AREF', 1], ['GND', 2],
      ['D13', 3], ['D12', 4], ['D11', 5], ['D10', 6], ['D9', 7], ['D8', 8],
      // physical gap at y_offset 9
      ['D7', 10], ['D6', 11], ['D5', 12], ['D4', 13],
      ['D3', 14], ['D2', 15], ['D1', 16], ['D0', 17]
    ].forEach(function(p) { this.PIN_DEFS[p[0]] = { x: 20, y: p[1] }; }, this);

    // Left edge (x:0) = physical "ANALOG IN" + "POWER" headers.
    // After rotation, the bottom header becomes the left edge, reading top→bottom:
    //   A5–A0  [gap]  VIN, 5V, 3V3, RST, IOREF
    [
      ['A5', 1], ['A4', 2], ['A3', 3], ['A2', 4], ['A1', 5], ['A0', 6],
      // physical gap at y_offset 7
      ['VIN', 8], ['5V', 9], ['3V3', 10], ['RST', 11], ['IOREF', 12]
    ].forEach(function(p) { this.PIN_DEFS[p[0]] = { x: 0, y: p[1] }; }, this);

    this._bbox = null;
    this.svgEl = null;
    this.BOARD2_X_OFFSET = 36;
    this._isDualBoard = false;
  }

  holeToSVG(col, row, board) {
    const xOff = (board === 2) ? this.BOARD2_X_OFFSET : 0;
    return { x: this.BB_ANCHOR.x + (30 - row) + xOff, y: this.BB_ANCHOR.y + this.COL_OFFSETS[col] };
  }

  pinToSVG(pin) {
    const off = this.PIN_DEFS[pin];
    if (!off) throw new Error('Unknown pin: ' + pin);
    return { x: this.ARD_ANCHOR.x + off.x, y: this.ARD_ANCHOR.y + off.y };
  }

  _resolveEndpoint(endpoint) {
    const dot  = endpoint.indexOf('.');
    const type = endpoint.slice(0, dot);
    const ref  = endpoint.slice(dot + 1);

    if (type === 'arduino') return this.pinToSVG(ref);

    // Determine board from type prefix: "breadboard2" → 2, everything else → 1
    const board = (type === 'breadboard2') ? 2 : 1;

    // Power rail: "+1.5" or "-2.10"
    const railMatch = /^([+\-][12])\.(\d+)$/.exec(ref);
    if (railMatch) return this.holeToSVG(railMatch[1], parseInt(railMatch[2]), board);

    // Standard bus hole: "A10" or "E7"
    const holeMatch = /^([A-Ja-j]+)(\d+)$/.exec(ref);
    if (holeMatch) return this.holeToSVG(holeMatch[1].toUpperCase(), parseInt(holeMatch[2]), board);

    throw new Error('Unrecognised endpoint: ' + endpoint);
  }

  _el(tag, attrs) {
    const el = document.createElementNS(this.svgNS, tag);
    for (const k in attrs) el.setAttribute(k, String(attrs[k]));
    return el;
  }

  _txt(content, attrs) {
    const t = this._el('text', attrs);
    t.textContent = content;
    this.svgEl.appendChild(t);
  }

  _track(x, y) {
    if (!this._bbox) this._bbox = { x0: x, y0: y, x1: x, y1: y };
    if (x < this._bbox.x0) this._bbox.x0 = x;
    if (y < this._bbox.y0) this._bbox.y0 = y;
    if (x > this._bbox.x1) this._bbox.x1 = x;
    if (y > this._bbox.y1) this._bbox.y1 = y;
  }

  _drawSingleBoard(xOffset, board) {
    const a = this.BB_ANCHOR;
    const ax = a.x + xOffset;

    this._track(ax - 2, a.y - 1.0);
    this._track(ax + 31, a.y + 18);

    // White board body
    this.svgEl.appendChild(this._el('rect', {
      x: ax - 0.5, y: a.y - 1.0, width: 30.5, height: 18.0,
      rx: 0.5, fill: '#FAFAFA', stroke: '#BBB', 'stroke-width': 0.1
    }));

    // Power rail tints
    this.svgEl.appendChild(this._el('rect', { x: ax - 0.4, y: a.y + 0 - 0.4,  width: 29.8, height: 0.8, fill: '#FFD5D5' }));
    this.svgEl.appendChild(this._el('rect', { x: ax - 0.4, y: a.y + 1 - 0.4,  width: 29.8, height: 0.8, fill: '#D5D5FF' }));
    this.svgEl.appendChild(this._el('rect', { x: ax - 0.4, y: a.y + 15 - 0.4, width: 29.8, height: 0.8, fill: '#FFD5D5' }));
    this.svgEl.appendChild(this._el('rect', { x: ax - 0.4, y: a.y + 16 - 0.4, width: 29.8, height: 0.8, fill: '#D5D5FF' }));

    // Centre DIP gap
    this.svgEl.appendChild(this._el('line', {
      x1: ax - 0.5, y1: a.y + 8, x2: ax + 29.5, y2: a.y + 8,
      stroke: '#C8C8C8', 'stroke-width': 0.25, 'stroke-dasharray': '0.6 0.4'
    }));

    // All holes
    const allCols = ['+1','-1','A','B','C','D','E','F','G','H','I','J','+2','-2'];
    for (let ci = 0; ci < allCols.length; ci++) {
      for (let row = 1; row <= 30; row++) {
        const p = this.holeToSVG(allCols[ci], row, board);
        this.svgEl.appendChild(this._el('circle', { cx: p.x, cy: p.y, r: 0.3, fill: '#555' }));
      }
    }

    // Column letter labels (A-J) above board
    ['A','B','C','D','E','F','G','H','I','J'].forEach(function(col) {
      const y = a.y + this.COL_OFFSETS[col];
      this._txt(col, { x: ax - 1.2, y: y + 0.25, 'text-anchor': 'end',
        'font-size': 0.65, fill: '#555', 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // Power rail + / - labels above board
    [['+1', '+', '#B00000'], ['-1', '−', '#0000B0'],
     ['+2', '+', '#B00000'], ['-2', '−', '#0000B0']].forEach(function(e) {
      const y = a.y + this.COL_OFFSETS[e[0]];
      this._txt(e[1], { x: ax - 1.2, y: y + 0.25, 'text-anchor': 'end',
        'font-size': 0.7, fill: e[2], 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // Row numbers on the right side — every 5th + row 1
    [1, 5, 10, 15, 20, 25, 30].forEach(function(row) {
      this._txt(String(row), { x: ax + (30 - row), y: a.y + 17.5,
        'text-anchor': 'middle', 'font-size': 0.6, fill: '#888', 'font-family': 'monospace' });
    }, this);
  }

  drawBreadboard() {
    this._drawSingleBoard(0, 1);
    if (this._isDualBoard) this._drawSingleBoard(this.BOARD2_X_OFFSET, 2);
  }

  drawArduino() {
    const a = this.ARD_ANCHOR;
    const W = 20, H = 20;

    // Board shadow
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.3, y: a.y - 0.3, width: W + 2.5, height: H + 1,
      rx: 1, fill: '#000000', opacity: 0.3
    }));

    // Board body
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.5, y: a.y - 0.5, width: W + 2.5, height: H + 1,
      rx: 1, fill: '#00979C', stroke: '#005f63', 'stroke-width': 0.2
    }));
    
    // Add mounting holes
    const mHoles = [
      {x: a.x + 0.5, y: a.y + 0.5},
      {x: a.x + W + 1, y: a.y + 0.5},
      {x: a.x + 0.5, y: a.y + H - 0.5},
      {x: a.x + W + 1, y: a.y + H - 0.5}
    ];
    mHoles.forEach(h => {
      this.svgEl.appendChild(this._el('circle', { cx: h.x, cy: h.y, r: 0.6, fill: '#E5E5E5', stroke: '#CCC', 'stroke-width': 0.1 }));
      this.svgEl.appendChild(this._el('circle', { cx: h.x, cy: h.y, r: 0.35, fill: '#222' }));
    });

    this._track(a.x - 2.5, a.y - 0.5);
    this._track(a.x + W + 1.5, a.y + H + 3);

    // USB-B connector at bottom (was the "left" side in landscape orientation)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 1.5, y: a.y + H + 0.5, width: 4.5, height: 2,
      rx: 0.3, fill: '#CCCCCC', stroke: '#888', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 2.0, y: a.y + H + 0.8, width: 3.5, height: 1.4,
      fill: '#BBBBBB', stroke: '#999', 'stroke-width': 0.05
    }));
    this._txt('USB', { x: a.x + 3.75, y: a.y + H + 1.8, 'text-anchor': 'middle',
      'font-size': 0.6, fill: '#555', 'font-family': 'monospace' });

    // DC power jack (top-left corner — was top of board in landscape)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 2.5, y: a.y + 0.5, width: 2.3, height: 3.0,
      rx: 0.2, fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.7, y: a.y + 1.0, width: 0.5, height: 2.0,
      fill: '#555'
    }));

    // Voltage Regulator (near power jack)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 1.0, y: a.y + 1.5, width: 1.5, height: 1.0,
      fill: '#222', stroke: '#111', 'stroke-width': 0.05
    }));
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 1.25, y: a.y + 1.3, width: 1.0, height: 0.2, fill: '#AAA'
    }));

    // USB-to-Serial chip (ATmega16U2)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 3.0, y: a.y + H - 3.5, width: 2.5, height: 2.5,
      rx: 0.1, fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));

    // Crystal Oscillator (silver oval) near USB chip
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 6.0, y: a.y + H - 2.5, width: 1.0, height: 2.0,
      rx: 0.5, fill: '#E0E0E0', stroke: '#999', 'stroke-width': 0.1
    }));

    // Reset Button (top right-ish)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 16, y: a.y + 1, width: 1.5, height: 1.5,
      fill: '#E0E0E0', stroke: '#999', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('circle', {
      cx: a.x + 16.75, cy: a.y + 1.75, r: 0.4, fill: '#DAA520'
    }));

    // ATmega chip (Main MCU)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 4.5, y: a.y + 6.5, width: 9, height: 7,
      rx: 0.3, fill: '#1a1a1a', stroke: '#333', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('circle', {
      cx: a.x + 5.2, cy: a.y + 7.2, r: 0.3, fill: '#333'
    }));
    this._txt('ATmega328P', { x: a.x + 9, y: a.y + 10.3, 'text-anchor': 'middle',
      'font-size': 0.65, fill: '#888', 'font-family': 'monospace' });

    // Board name/logo
    this._txt('Arduino', { x: a.x + 10, y: a.y + 3.5, 'text-anchor': 'middle',
      'font-size': 1.1, fill: '#FFF', 'font-weight': 'bold', 'font-family': 'sans-serif' });
    this._txt('UNO', { x: a.x + 10, y: a.y + 5.0, 'text-anchor': 'middle',
      'font-size': 0.9, fill: '#FFF', 'font-weight': 'bold', 'font-family': 'sans-serif' });
    this._txt('MADE IN ITALY', { x: a.x + 10, y: a.y + 16, 'text-anchor': 'middle',
      'font-size': 0.5, fill: '#FFF', 'font-family': 'sans-serif' });

    // Headers - Right edge (D0-D13, GND, AREF)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 19.5, y: a.y + 0.5, width: 1.0, height: 8.0,
      fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 19.5, y: a.y + 9.5, width: 1.0, height: 8.0,
      fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));

    // Right edge pins: AREF, GND, D13–D8, D7–D0
    [
      'AREF','GND','D13','D12','D11','D10','D9','D8',
      null,
      'D7','D6','D5','D4','D3','D2','D1','D0'
    ].forEach(function(p) {
      if (!p) return;
      const pin = this.pinToSVG(p);
      this.svgEl.appendChild(this._el('circle', { cx: pin.x, cy: pin.y, r: 0.25, fill: '#444' }));
      this.svgEl.appendChild(this._el('circle', { cx: pin.x, cy: pin.y, r: 0.15, fill: '#888' }));
      this._txt(p, { x: pin.x - 1.0, y: pin.y + 0.25, 'text-anchor': 'end',
        'font-size': 0.55, fill: '#FFF', 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // Headers - Left edge (A0-A5, Power)
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.5, y: a.y + 0.5, width: 1.0, height: 6.0,
      fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.5, y: a.y + 7.5, width: 1.0, height: 5.0,
      fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));

    // Left edge pins: A5–A0, VIN, 5V, 3V3, RST, IOREF
    [
      'A5','A4','A3','A2','A1','A0',
      null,
      'VIN','5V','3V3','RST','IOREF'
    ].forEach(function(p) {
      if (!p) return;
      const pin = this.pinToSVG(p);
      this.svgEl.appendChild(this._el('circle', { cx: pin.x, cy: pin.y, r: 0.25, fill: '#444' }));
      this.svgEl.appendChild(this._el('circle', { cx: pin.x, cy: pin.y, r: 0.15, fill: '#888' }));
      this._txt(p, { x: pin.x + 1.0, y: pin.y + 0.25, 'text-anchor': 'start',
        'font-size': 0.55, fill: '#FFF', 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // TX/RX LEDs
    this.svgEl.appendChild(this._el('rect', { x: a.x + 16, y: a.y + 11.5, width: 0.6, height: 0.6, fill: '#FFD700' }));
    this._txt('TX', { x: a.x + 17, y: a.y + 12, 'text-anchor': 'start', 'font-size': 0.4, fill: '#FFF', 'font-family': 'monospace' });
    this.svgEl.appendChild(this._el('rect', { x: a.x + 16, y: a.y + 12.5, width: 0.6, height: 0.6, fill: '#FFD700' }));
    this._txt('RX', { x: a.x + 17, y: a.y + 13, 'text-anchor': 'start', 'font-size': 0.4, fill: '#FFF', 'font-family': 'monospace' });

    // Built-in LED (L)
    this.svgEl.appendChild(this._el('rect', { x: a.x + 16, y: a.y + 9, width: 0.6, height: 0.6, fill: '#FFD700' }));
    this._txt('L', { x: a.x + 17, y: a.y + 9.5, 'text-anchor': 'start', 'font-size': 0.4, fill: '#FFF', 'font-family': 'monospace' });

    // ON LED
    this.svgEl.appendChild(this._el('rect', { x: a.x + 16, y: a.y + 15, width: 0.6, height: 0.6, fill: '#00FF00' }));
    this._txt('ON', { x: a.x + 17, y: a.y + 15.5, 'text-anchor': 'start', 'font-size': 0.4, fill: '#FFF', 'font-family': 'monospace' });

    // ICSP Header (2x3 pins) near ATmega
    this.svgEl.appendChild(this._el('rect', {
      x: a.x + 14, y: a.y + 4.5, width: 1.8, height: 2.8,
      fill: '#222', stroke: '#111', 'stroke-width': 0.1
    }));
    [0.5, 1.3].forEach(hx => {
      [0.5, 1.4, 2.3].forEach(hy => {
        this.svgEl.appendChild(this._el('circle', {
          cx: a.x + 14 + hx, cy: a.y + 4.5 + hy, r: 0.15, fill: '#FFD700'
        }));
      });
    });
  }

  placeComponent(component) {
    const pinsRaw = component.pins || {};
    const pinsSVG = {};
    const board = component.board || 1;
    let cx = 0, cy = 0, n = 0;
    for (const name in pinsRaw) {
      const h = pinsRaw[name];
      pinsSVG[name] = this.holeToSVG(h.col, h.row, board);
      cx += pinsSVG[name].x;
      cy += pinsSVG[name].y;
      n++;
    }
    if (n > 0) { cx /= n; cy /= n; }

    const symRenderer = SYMBOL_RENDERERS[component.type];
    if (symRenderer) {
      symRenderer(this, pinsSVG, component.properties || {});
    } else {
      const colorMap = { LED: '#FF8C00', RESISTOR: '#888888', BUTTON: '#00AA00' };
      const fill = colorMap[component.type] || '#888888';
      this.svgEl.appendChild(this._el('circle', {
        cx: cx, cy: cy, r: 1.0,
        fill: fill, stroke: '#FFF', 'stroke-width': 0.2, opacity: 0.9
      }));
    }
  }

  drawWire(connection, wireIndex) {
    const start = this._resolveEndpoint(connection.from);
    const end   = this._resolveEndpoint(connection.to);
    const color = connection.color || '#555';

    const waypoints = this._astar(start, end);
    this._markWireCells(waypoints);

    let d = 'M ' + waypoints[0].x + ' ' + waypoints[0].y;
    for (let i = 1; i < waypoints.length; i++) d += ' L ' + waypoints[i].x + ' ' + waypoints[i].y;

    this.svgEl.appendChild(this._el('path', {
      d: d,
      stroke: color, 'stroke-width': 0.4, fill: 'none',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round'
    }));

    if (this._isInBreadboard(start))
      this.svgEl.appendChild(this._el('circle', { cx: start.x, cy: start.y, r: 0.22, fill: color }));
    if (this._isInBreadboard(end))
      this.svgEl.appendChild(this._el('circle', { cx: end.x, cy: end.y, r: 0.22, fill: color }));

    this._allWires.push({ fromRaw: connection._origFrom || connection.from, toRaw: connection._origTo || connection.to, pathData: d, start, end, waypoints });
  }

  _isInBreadboard(pt) {
    const a = this.BB_ANCHOR;
    const inB1 = pt.x >= a.x - 1 && pt.x <= a.x + 31 && pt.y >= a.y - 1 && pt.y <= a.y + 18;
    if (!this._isDualBoard) return inB1;
    const b2x = a.x + this.BOARD2_X_OFFSET;
    const inB2 = pt.x >= b2x - 1 && pt.x <= b2x + 31 && pt.y >= a.y - 1 && pt.y <= a.y + 18;
    return inB1 || inB2;
  }

  _isInArduino(pt) {
    const a = this.ARD_ANCHOR;
    return pt.x >= a.x - 1 && pt.x <= a.x + 22 && pt.y >= a.y - 1 && pt.y <= a.y + 22;
  }

  getHighlights() {
    return (this.def.connections || []).map(function(conn, i) {
      const from = this._resolveEndpoint(conn.from);
      const to   = this._resolveEndpoint(conn.to);
      return {
        step:  i + 1,
        label: conn.label || (conn.from + ' -> ' + conn.to),
        from:  from,
        to:    to,
        color: conn.color || '#FF8800',
        cx: (from.x + to.x) / 2,
        cy: (from.y + to.y) / 2,
      };
    }, this);
  }

  render() {
    this._uid = 'cr' + (++_rendererUidCounter);
    this._bbox = null;
    this._debugOverlay = null;
    this._debugInfoBar = null;
    this._isDualBoard = (this.def.layout === 'dual_board');
    this.svgEl = this._el('svg', { xmlns: this.svgNS, style: 'width:100%;height:auto;display:block;' });
    this.drawBreadboard();
    this.drawArduino();
    this._allWires = [];
    this._buildObstacleRegistry();
    this._initGrid();
    const self = this;
    const _powerKw = ['GND', '5V', 'VIN', '3V3', '+1', '-1', '+2', '-2'];
    function _isPow(ep) { return _powerKw.some(function(k) { return ep.indexOf(k) !== -1; }); }
    function _len(conn) {
      try {
        const s = self._resolveEndpoint(conn.from), e = self._resolveEndpoint(conn.to);
        return Math.sqrt((e.x-s.x)*(e.x-s.x)+(e.y-s.y)*(e.y-s.y));
      } catch(ex) { return 999; }
    }
    const connections = this._assignWireColors(
      this._normalizeGroundConnections((this.def.connections || []).slice())
    ).sort(function(a, b) {
      const pa = (_isPow(a.from)||_isPow(a.to)) ? 0 : 1;
      const pb = (_isPow(b.from)||_isPow(b.to)) ? 0 : 1;
      if (pa !== pb) return pa - pb;
      return _len(a) - _len(b);
    });
    for (let i = 0; i < connections.length; i++) this.drawWire(connections[i], i);
    const components = this.def.components || [];
    for (let i = 0; i < components.length; i++) this.placeComponent(components[i]);
    const pad = 3;
    const b = this._bbox || { x0: 0, y0: 0, x1: 50, y1: 60 };
    this.svgEl.setAttribute('viewBox',
      (b.x0 - pad) + ' ' + (b.y0 - pad) + ' ' +
      (b.x1 - b.x0 + pad * 2) + ' ' + (b.y1 - b.y0 + pad * 2)
    );
    this.container.innerHTML = '';
    this.container.appendChild(this.svgEl);
  }

  // ── HIGHLIGHTING ──────────────────────────────────────────────────────────

  applyHighlight(highlights) {
    const existingLayer = this.svgEl.querySelector('#highlight-layer');
    if (existingLayer) existingLayer.remove();

    if (!highlights || highlights.length === 0) return;

    const layer = this._el('g', { id: 'highlight-layer' });
    const defs = _ensureDefs(this);

    const maskId = this._uid + '_greyout-mask';
    const existingMask = defs.querySelector('#' + maskId);
    if (existingMask) existingMask.remove();
    const mask = this._el('mask', { id: maskId });
    
    const b = this._bbox || { x0: -5, y0: -5, x1: 50, y1: 60 };
    const pad = 10;
    
    // Background of mask is white (fully opaque overlay)
    mask.appendChild(this._el('rect', {
      x: b.x0 - pad, y: b.y0 - pad,
      width: (b.x1 - b.x0) + pad * 2, height: (b.y1 - b.y0) + pad * 2,
      fill: 'white'
    }));

    for (let i = 0; i < highlights.length; i++) {
      const h = highlights[i];
      if (h.type === 'component') {
        const comp = this.def.components.find(c => c.id === h.id);
        if (comp) {
            const symRenderer = SYMBOL_RENDERERS[comp.type];
            if (symRenderer && symRenderer.bbox) {
                const pinsRaw = comp.pins || {};
                const pinsSVG = {};
                const compBoard = comp.board || 1;
                for (const name in pinsRaw) {
                    pinsSVG[name] = this.holeToSVG(pinsRaw[name].col, pinsRaw[name].row, compBoard);
                }
                const bbox = symRenderer.bbox(pinsSVG, comp.properties || {});
                // Punch hole (black)
                mask.appendChild(this._el('rect', {
                    x: bbox.x0 - 0.3, y: bbox.y0 - 0.3,
                    width: (bbox.x1 - bbox.x0) + 0.6,
                    height: (bbox.y1 - bbox.y0) + 0.6,
                    rx: 0.5,
                    fill: 'black'
                }));
            }
        }
      } else if (h.type === 'wire') {
        const wp = this._allWires.find(w => 
          (w.fromRaw === h.from && w.toRaw === h.to) || 
          (w.fromRaw === h.to && w.toRaw === h.from)
        );
        if (wp) {
            // Thick black line for mask cutout
            mask.appendChild(this._el('path', {
                d: wp.pathData,
                stroke: 'black', 'stroke-width': 1.6, fill: 'none',
                'stroke-linecap': 'round', 'stroke-linejoin': 'round'
            }));
            
            // Add circles for the connection points if they are in the breadboard
            if (this._isInBreadboard(wp.start)) {
                mask.appendChild(this._el('circle', { cx: wp.start.x, cy: wp.start.y, r: 0.5, fill: 'black' }));
            }
            if (this._isInBreadboard(wp.end)) {
                mask.appendChild(this._el('circle', { cx: wp.end.x, cy: wp.end.y, r: 0.5, fill: 'black' }));
            }
        }
      }
    }

    defs.appendChild(mask);

    const overlayRect = this._el('rect', {
      x: b.x0 - pad, y: b.y0 - pad,
      width: (b.x1 - b.x0) + pad * 2, height: (b.y1 - b.y0) + pad * 2,
      fill: 'black',
      opacity: '0.6',
      mask: 'url(#' + maskId + ')',
      style: 'pointer-events: none;'
    });

    layer.appendChild(overlayRect);
    this.svgEl.appendChild(layer);
  }

  // ── DEBUG TOOLS ───────────────────────────────────────────────────────────

  describe() {
    function padR(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }

    var lines = [];
    lines.push('=== CIRCUIT DEBUG ===');
    lines.push('Formula: holeToSVG(col,row)  x = ' + this.BB_ANCHOR.x + ' + (30 - row)   y = ' + this.BB_ANCHOR.y + ' + COL[col]');
    var colLine = 'COL: ';
    for (var ck in this.COL_OFFSETS) { colLine += ck + ':' + this.COL_OFFSETS[ck] + '  '; }
    lines.push(colLine.replace(/\s+$/, ''));
    lines.push('');

    lines.push('COMPONENTS  (id | type | pin | hole | SVG | props)');
    var comps = this.def.components || [];
    for (var i = 0; i < comps.length; i++) {
      var c = comps[i];
      var props = '';
      for (var k in (c.properties || {})) { props += k + '=' + c.properties[k] + ' '; }
      var pinsRaw = c.pins || {};
      var firstPin = true;
      for (var pinName in pinsRaw) {
        var h = pinsRaw[pinName];
        var p = this.holeToSVG(h.col, h.row);
        var prefix = firstPin
          ? ('  ' + padR(c.id, 8) + padR(c.type, 12))
          : ('  ' + padR('', 20));
        lines.push(
          prefix + padR(pinName, 12) + padR(h.col + h.row, 6) +
          'SVG(' + p.x + ',' + p.y + ')' +
          (firstPin && props ? '  [' + props.replace(/\s+$/, '') + ']' : '')
        );
        firstPin = false;
      }
      if (firstPin) lines.push('  ' + padR(c.id, 8) + padR(c.type, 12) + '(no pins defined)');
    }

    lines.push('');
    lines.push('WIRES  (from | SVG | to | SVG | color | label)');
    var conns = this.def.connections || [];
    for (var j = 0; j < conns.length; j++) {
      var conn = conns[j];
      try {
        var f = this._resolveEndpoint(conn.from);
        var t = this._resolveEndpoint(conn.to);
        lines.push(
          '  ' + padR(conn.from, 24) + 'SVG(' + f.x + ',' + f.y + ')' +
          '  ->  ' + padR(conn.to, 24) + 'SVG(' + t.x + ',' + t.y + ')' +
          '  ' + padR(conn.color || '#555', 10) + (conn.label ? '  "' + conn.label + '"' : '')
        );
      } catch (e) {
        lines.push('  [ERR: ' + conn.from + ' -> ' + conn.to + ' : ' + e.message + ']');
      }
    }

    return lines.join('\n');
  }

  toggleDebugOverlay() {
    if (this._debugOverlay) {
      this._debugOverlay.remove();
      if (this._debugInfoBar) this._debugInfoBar.remove();
      this._debugOverlay = null;
      this._debugInfoBar = null;
      return false;
    }

    var self = this;

    var bar = document.createElement('div');
    bar.style.cssText = 'font-family:monospace;font-size:13px;padding:6px 12px;' +
      'background:#1a1a2e;color:#00FF88;border-radius:4px;margin-top:6px;min-height:1.8em;';
    bar.textContent = 'Hover a breadboard hole to see its reference and SVG coords';
    this.container.parentNode.insertBefore(bar, this.container.nextSibling);
    this._debugInfoBar = bar;

    var g = this._el('g', { id: '_dbg_overlay' });

    var allCols = ['+1','-1','A','B','C','D','E','F','G','H','I','J','+2','-2'];
    for (var ci = 0; ci < allCols.length; ci++) {
      for (var row = 1; row <= 30; row++) {
        (function(col, r) {
          var p   = self.holeToSVG(col, r);
          var ref = col + r;
          var hit = self._el('rect', {
            x: p.x - 0.45, y: p.y - 0.45, width: 0.9, height: 0.9,
            fill: 'transparent', style: 'cursor:crosshair'
          });
          hit.addEventListener('mouseenter', function() {
            bar.textContent = ref + '   ->   SVG(' + p.x + ', ' + p.y + ')';
            hit.setAttribute('fill', 'rgba(255,255,0,0.35)');
          });
          hit.addEventListener('mouseleave', function() {
            hit.setAttribute('fill', 'transparent');
          });
          g.appendChild(hit);
        })(allCols[ci], row);
      }
    }

    var comps = this.def.components || [];
    for (var ci2 = 0; ci2 < comps.length; ci2++) {
      var comp = comps[ci2];
      var pinsRaw = comp.pins || {};
      var compCX = 0, compCY = 0, pinCount = 0;

      for (var pinName in pinsRaw) {
        var ph = pinsRaw[pinName];
        var pp = self.holeToSVG(ph.col, ph.row);
        compCX += pp.x; compCY += pp.y; pinCount++;

        g.appendChild(self._el('circle', {
          cx: pp.x, cy: pp.y, r: 0.22,
          fill: '#FF44FF', opacity: 0.95, style: 'pointer-events:none'
        }));
        var plbl = self._el('text', {
          x: pp.x, y: pp.y - 0.38,
          'font-size': 0.44, fill: '#FF44FF', 'font-family': 'monospace',
          'text-anchor': 'middle', 'font-weight': 'bold', style: 'pointer-events:none'
        });
        plbl.textContent = pinName + ' @' + ph.col + ph.row;
        g.appendChild(plbl);
      }

      if (pinCount > 0) {
        compCX /= pinCount; compCY /= pinCount;
        var cidlbl = self._el('text', {
          x: compCX, y: compCY - 1.8,
          'font-size': 0.52, fill: '#FF44FF', 'font-family': 'monospace',
          'text-anchor': 'middle', 'font-weight': 'bold', style: 'pointer-events:none'
        });
        cidlbl.textContent = comp.id + ' (' + comp.type + ')';
        g.appendChild(cidlbl);
      }
    }

    this.svgEl.appendChild(g);
    this._debugOverlay = g;
    return true;
  }
}
// Assign colors to wires by type:
//   ground (GND / -1 / -2 rail)  → black
//   power  (5V / VIN / +1 / +2)  → red
//   signal                        → cycle through SIGNAL_COLORS palette
// Overrides any color already set on the connection so the rendered circuit
// always uses high-contrast, varied wiring regardless of definition order.
CircuitRenderer.prototype._assignWireColors = function(connections) {
  const SIGNAL_COLORS = [
    '#E74C3C', // red
    '#3498DB', // blue
    '#9B59B6', // purple
    '#E67E22', // orange
    '#1ABC9C', // teal
    '#F1C40F', // yellow
    '#E91E63', // pink
    '#00BCD4', // cyan
    '#FF5722', // deep orange
    '#8BC34A', // lime green
    '#673AB7', // deep purple
    '#FF9800', // amber
    '#2196F3', // light blue
    '#4CAF50', // medium green
    '#F06292', // rose
    '#26C6DA', // light cyan
    '#7E57C2', // medium purple
    '#FF7043', // coral
    '#66BB6A', // soft green
    '#AB47BC', // orchid
  ];

  const GND_KW = ['GND', '-1', '-2'];
  const PWR_KW = ['5V', 'VIN', '3V3', '+1', '+2'];
  function isGnd(ep) { return GND_KW.some(function(k) { return ep.indexOf(k) !== -1; }); }
  function isPwr(ep) { return PWR_KW.some(function(k) { return ep.indexOf(k) !== -1; }); }

  let sigIdx = 0;
  return connections.map(function(conn) {
    if (isGnd(conn.from) || isGnd(conn.to)) return Object.assign({}, conn, { color: '#000000' });
    if (isPwr(conn.from) || isPwr(conn.to)) return Object.assign({}, conn, { color: '#CC0000' });
    if (conn.color) return conn;  // respect explicitly-set signal wire colors
    const color = SIGNAL_COLORS[sigIdx % SIGNAL_COLORS.length];
    sigIdx++;
    return Object.assign({}, conn, { color: color });
  });
};

// When multiple wires all target arduino.GND, route them via the negative rails instead
// so each component's GND drops to the rail and only one canonical wire runs to Arduino.
//
// Rail assignment strategy:
//   AE-side (A-E) holes → rail -1 at the same row (top rail, above the AE columns).
//   FJ-side (F-J) holes → rail -2 at the same row (bottom rail, below the FJ columns),
//     UNLESS that -2 slot is inside a component obstacle (e.g. HC-SR04 PCB covers -2 at
//     rows 1-20).  In that case, fall back to rail -1 at the nearest *unused* row so the
//     wire avoids both the obstacle and any already-assigned -1 slot.
//
// Canonical wires at the Arduino end:
//   • Only -1 in use → arduino.GND → breadboard.-1.30
//   • Only -2 in use → arduino.GND → breadboard.-2.30
//   • Both in use    → arduino.GND → breadboard.-1.30  +  -2.30 → -1.30 (bridge)
CircuitRenderer.prototype._normalizeGroundConnections = function(connections) {
  const self = this;
  const isDual = this._isDualBoard;
  // Match existing rail endpoints (breadboard., breadboard1., breadboard2.)
  const railRe = /^breadboard[12]?\.[+\-][12]\.\d+$/;
  // Match hole endpoints — capture optional board number, col, row
  const holeRe = /^breadboard([12]?)\.([A-Ja-j]+)(\d+)$/;
  const aeHalf = new Set(['A','B','C','D','E']);

  function _boardPrefix(boardNum) {
    return isDual ? ('breadboard' + boardNum) : 'breadboard';
  }

  function _slotBlocked(boardNum, rail, row) {
    const pos = self.holeToSVG(rail, row, isDual ? boardNum : 1);
    const obs = self._obstacles || [];
    for (let i = 0; i < obs.length; i++) {
      const o = obs[i];
      if (pos.x >= o.x0 && pos.x <= o.x1 && pos.y >= o.y0 && pos.y <= o.y1) return true;
    }
    return false;
  }

  // Find the nearest unoccupied, unblocked -1 slot to `preferRow` on `boardNum`.
  // usedSlots keys are "boardNum:row" strings to avoid cross-board conflicts.
  function _findFreeTopSlot(boardNum, preferRow, usedSlots) {
    for (let delta = 0; delta <= 10; delta++) {
      const candidates = delta === 0 ? [preferRow] : [preferRow + delta, preferRow - delta];
      for (let ci = 0; ci < candidates.length; ci++) {
        const r = candidates[ci];
        if (r < 1 || r > 30) continue;
        if (usedSlots.has(boardNum + ':' + r)) continue;
        if (_slotBlocked(boardNum, '-1', r)) continue;
        return r;
      }
    }
    return null;
  }

  const gndIndices = [];
  for (let i = 0; i < connections.length; i++) {
    if (connections[i].from === 'arduino.GND' || connections[i].to === 'arduino.GND') {
      gndIndices.push(i);
    }
  }
  if (gndIndices.length === 0) return connections;

  // Separate non-GND connections through immediately.
  const result = [];
  for (let i = 0; i < connections.length; i++) {
    if (gndIndices.indexOf(i) === -1) result.push(connections[i]);
  }

  let hasRailGndWire = false;
  // Per-board rail state
  const boardState = {
    1: { hasTopRail: false, hasBotRail: false },
    2: { hasTopRail: false, hasBotRail: false },
  };
  let gndColor = '#000000';

  // usedTopSlots keyed as "boardNum:row"
  const usedTopSlots = new Set();
  const fjPending = [];

  // Pass 1 — assign AE-side GND holes to -1 rail.
  for (let gi = 0; gi < gndIndices.length; gi++) {
    const conn = connections[gndIndices[gi]];
    const other = conn.from === 'arduino.GND' ? conn.to : conn.from;
    if (conn.color) gndColor = conn.color;

    if (railRe.test(other)) {
      result.push(conn);
      hasRailGndWire = true;
      continue;
    }

    const hm = holeRe.exec(other);
    if (!hm) { result.push(conn); continue; }

    const boardNum = hm[1] ? parseInt(hm[1]) : 1;
    const col = hm[2].toUpperCase()[0];
    const row = parseInt(hm[3]);
    const bp = _boardPrefix(boardNum);

    if (aeHalf.has(col)) {
      usedTopSlots.add(boardNum + ':' + row);
      boardState[boardNum].hasTopRail = true;
      result.push({
        from: other, to: bp + '.-1.' + row,
        color: conn.color || '#000000', label: conn.label,
        _origFrom: conn.from, _origTo: conn.to,
      });
    } else {
      fjPending.push({ conn, other, row, boardNum, bp });
    }
  }

  // Pass 2 — assign FJ-side GND holes.
  for (let fi = 0; fi < fjPending.length; fi++) {
    const { conn, other, row, boardNum, bp } = fjPending[fi];

    if (!_slotBlocked(boardNum, '-2', row)) {
      boardState[boardNum].hasBotRail = true;
      result.push({
        from: other, to: bp + '.-2.' + row,
        color: conn.color || '#000000', label: conn.label,
        _origFrom: conn.from, _origTo: conn.to,
      });
    } else {
      // -2 blocked (e.g. HC-SR04 PCB): fall back to nearest free -1 slot on same board.
      const slot = _findFreeTopSlot(boardNum, row, usedTopSlots);
      if (slot !== null) {
        usedTopSlots.add(boardNum + ':' + slot);
        boardState[boardNum].hasTopRail = true;
        result.push({
          from: other, to: bp + '.-1.' + slot,
          color: conn.color || '#000000', label: conn.label,
          _origFrom: conn.from, _origTo: conn.to,
        });
      } else {
        result.push(conn);
      }
    }
  }

  // Add canonical wire(s) connecting rails to Arduino GND.
  if (!hasRailGndWire) {
    if (!isDual) {
      // Single-board legacy behavior — use un-prefixed "breadboard."
      const bs = boardState[1];
      if (bs.hasTopRail && !bs.hasBotRail) {
        result.push({ from: 'arduino.GND', to: 'breadboard.-1.30', color: gndColor });
      } else if (!bs.hasTopRail && bs.hasBotRail) {
        result.push({ from: 'arduino.GND', to: 'breadboard.-2.30', color: gndColor });
      } else if (bs.hasTopRail && bs.hasBotRail) {
        result.push({ from: 'arduino.GND', to: 'breadboard.-1.30', color: gndColor });
        result.push({ from: 'breadboard.-2.30', to: 'breadboard.-1.30', color: gndColor });
      }
    } else {
      // Dual-board: canonical goes to board 1; board 2 bridges to board 1.
      const bs1 = boardState[1];
      const bs2 = boardState[2];

      if (bs1.hasTopRail || bs1.hasBotRail) {
        if (bs1.hasTopRail && !bs1.hasBotRail) {
          result.push({ from: 'arduino.GND', to: 'breadboard1.-1.30', color: gndColor });
        } else if (!bs1.hasTopRail && bs1.hasBotRail) {
          result.push({ from: 'arduino.GND', to: 'breadboard1.-2.30', color: gndColor });
        } else {
          result.push({ from: 'arduino.GND', to: 'breadboard1.-1.30', color: gndColor });
          result.push({ from: 'breadboard1.-2.30', to: 'breadboard1.-1.30', color: gndColor });
        }
        if (bs2.hasTopRail || bs2.hasBotRail) {
          result.push({ from: 'breadboard2.-1.30', to: 'breadboard1.-1.30', color: gndColor });
        }
      } else if (bs2.hasTopRail || bs2.hasBotRail) {
        // Only board 2 has GND — route directly to Arduino.
        result.push({ from: 'arduino.GND', to: 'breadboard2.-1.30', color: gndColor });
      }
    }
  }

  return result;
};


// ── GRID ROUTING ─────────────────────────────────────────────────────────────

const GRID_STEP = 0.5;
const GRID_COST_FREE    = 1.0;
const GRID_COST_NEAR    = 3.0;
const GRID_COST_WIRE    = 15.0;
const GRID_COST_BLOCKED = Infinity;
const TURN_PENALTY      = 0.5;
const DX = [1, 0, -1, 0];   // East, South, West, North
const DY = [0, 1, 0, -1];

CircuitRenderer.prototype._initGrid = function() {
  const STEP = GRID_STEP;
  const ard  = this.ARD_ANCHOR, bb = this.BB_ANCHOR;
  const bbRightEdge = this._isDualBoard ? bb.x + this.BOARD2_X_OFFSET + 32 : bb.x + 32;

  this._gxMin = Math.floor((ard.x - 4) / STEP);
  this._gxMax = Math.ceil( bbRightEdge  / STEP);
  this._gyMin = Math.floor((ard.y - 4) / STEP);
  this._gyMax = Math.ceil( (bb.y  + 20) / STEP);

  const W = this._gxMax - this._gxMin + 1;
  const H = this._gyMax - this._gyMin + 1;
  this._gridW = W;
  this._gridH = H;

  // One flat Float32Array in row-major order (gx-major)
  this._grid = new Float32Array(W * H).fill(GRID_COST_FREE);

  for (let i = 0; i < this._obstacles.length; i++) {
    const r = this._obstacles[i];
    const gx0 = Math.floor(r.x0 / STEP) - this._gxMin;
    const gx1 = Math.ceil( r.x1 / STEP) - this._gxMin;
    const gy0 = Math.floor(r.y0 / STEP) - this._gyMin;
    const gy1 = Math.ceil( r.y1 / STEP) - this._gyMin;
    for (let gx = Math.max(0, gx0); gx <= Math.min(W - 1, gx1); gx++) {
      for (let gy = Math.max(0, gy0); gy <= Math.min(H - 1, gy1); gy++) {
        this._grid[gx * H + gy] = GRID_COST_BLOCKED;
      }
    }
  }
};

CircuitRenderer.prototype._gridGet = function(gx, gy) {
  const lx = gx - this._gxMin, ly = gy - this._gyMin;
  if (lx < 0 || lx >= this._gridW || ly < 0 || ly >= this._gridH) return GRID_COST_BLOCKED;
  return this._grid[lx * this._gridH + ly];
};

CircuitRenderer.prototype._gridSet = function(gx, gy, val) {
  const lx = gx - this._gxMin, ly = gy - this._gyMin;
  if (lx < 0 || lx >= this._gridW || ly < 0 || ly >= this._gridH) return;
  this._grid[lx * this._gridH + ly] = val;
};

CircuitRenderer.prototype._astar = function(startSVG, endSVG) {
  const STEP = GRID_STEP;
  const sgx = Math.round(startSVG.x / STEP), sgy = Math.round(startSVG.y / STEP);
  const egx = Math.round(endSVG.x   / STEP), egy = Math.round(endSVG.y   / STEP);

  if (sgx === egx && sgy === egy) return [startSVG, endSVG];

  function key(gx, gy, dir) { return (gx << 16) | (gy << 8) | dir; }
  function h(gx, gy) { return Math.abs(gx - egx) + Math.abs(gy - egy); }

  const open  = new MinHeap();
  const dist  = new Map();
  const parent = new Map();

  for (let d = 0; d < 4; d++) {
    const k = key(sgx, sgy, d);
    dist.set(k, 0);
    open.push({ f: h(sgx, sgy), g: 0, gx: sgx, gy: sgy, dir: d });
  }

  while (open.size > 0) {
    const cur = open.pop();
    const ck  = key(cur.gx, cur.gy, cur.dir);
    if (cur.g > (dist.get(ck) !== undefined ? dist.get(ck) : Infinity)) continue;

    if (cur.gx === egx && cur.gy === egy) {
      return this._reconstructAndSimplify(parent, cur, sgx, sgy, key);
    }

    for (let nd = 0; nd < 4; nd++) {
      const ngx = cur.gx + DX[nd], ngy = cur.gy + DY[nd];
      const isGoal = (ngx === egx && ngy === egy);
      const cellCost = isGoal ? GRID_COST_FREE : this._gridGet(ngx, ngy);
      if (cellCost === GRID_COST_BLOCKED) continue;

      const turnCost = (nd !== cur.dir) ? TURN_PENALTY : 0;
      const ng = cur.g + cellCost + turnCost;
      const nk = key(ngx, ngy, nd);
      const prev = dist.get(nk);
      if (prev === undefined || ng < prev) {
        dist.set(nk, ng);
        parent.set(nk, { gx: cur.gx, gy: cur.gy, dir: cur.dir });
        open.push({ f: ng + h(ngx, ngy), g: ng, gx: ngx, gy: ngy, dir: nd });
      }
    }
  }

  return [startSVG, endSVG];
};

CircuitRenderer.prototype._reconstructAndSimplify = function(parent, goalState, sgx, sgy, keyFn) {
  const STEP = GRID_STEP;
  const cells = [];
  let cur = { gx: goalState.gx, gy: goalState.gy, dir: goalState.dir };
  while (cur.gx !== sgx || cur.gy !== sgy) {
    cells.push({ x: cur.gx * STEP, y: cur.gy * STEP });
    const p = parent.get(keyFn(cur.gx, cur.gy, cur.dir));
    if (!p) break;
    cur = p;
  }
  cells.push({ x: sgx * STEP, y: sgy * STEP });
  cells.reverse();
  return this._simplifyWaypoints(cells);
};

CircuitRenderer.prototype._simplifyWaypoints = function(pts) {
  if (pts.length <= 2) return pts;
  function dirKey(a, b) { return Math.sign(b.x - a.x) + ',' + Math.sign(b.y - a.y); }
  const result = [pts[0]];
  let prevDir = dirKey(pts[0], pts[1]);
  for (let i = 1; i < pts.length - 1; i++) {
    const curDir = dirKey(pts[i], pts[i + 1]);
    if (curDir !== prevDir) { result.push(pts[i]); prevDir = curDir; }
  }
  result.push(pts[pts.length - 1]);
  return result;
};

CircuitRenderer.prototype._markWireCells = function(waypoints) {
  const STEP = GRID_STEP;
  for (let i = 0; i < waypoints.length - 1; i++) {
    const a = waypoints[i], b = waypoints[i + 1];
    const gxa = Math.round(a.x / STEP), gya = Math.round(a.y / STEP);
    const gxb = Math.round(b.x / STEP), gyb = Math.round(b.y / STEP);
    const cells = [];
    if (gxa === gxb) {
      const y0 = Math.min(gya, gyb), y1 = Math.max(gya, gyb);
      for (let gy = y0; gy <= y1; gy++) cells.push([gxa, gy]);
    } else {
      const x0 = Math.min(gxa, gxb), x1 = Math.max(gxa, gxb);
      for (let gx = x0; gx <= x1; gx++) cells.push([gx, gya]);
    }
    for (let c = 0; c < cells.length; c++) {
      const gx = cells[c][0], gy = cells[c][1];
      const v = this._gridGet(gx, gy);
      if (v !== GRID_COST_BLOCKED) this._gridSet(gx, gy, GRID_COST_WIRE);
      const ortho = [[gx+1,gy],[gx-1,gy],[gx,gy+1],[gx,gy-1]];
      for (let o = 0; o < ortho.length; o++) {
        const ax = ortho[o][0], ay = ortho[o][1];
        const av = this._gridGet(ax, ay);
        if (av > 0 && av < GRID_COST_WIRE) this._gridSet(ax, ay, Math.max(av, GRID_COST_NEAR));
      }
    }
  }
};

CircuitRenderer.prototype._buildObstacleRegistry = function() {
  this._obstacles = [];

  // Arduino board interior — prevents wires from routing through the body.
  // x bounds stop just inside each pin column so that segments terminating
  // We expand the x-bounds to include the pin headers (x=a.x and x=a.x+20).
  // Wires are now blocked from routing vertically along the pin headers.
  const a = this.ARD_ANCHOR;
  this._obstacles.push({
    x0: a.x,
    y0: a.y - 0.5,
    x1: a.x + 20,
    y1: a.y + 20.5
  });

  const comps = this.def.components || [];
  for (let i = 0; i < comps.length; i++) {
    const component = comps[i];
    const renderer = SYMBOL_RENDERERS[component.type];
    if (!renderer || !renderer.bbox) continue;
    const pinsRaw = component.pins || {};
    const pinsSVG = {};
    const board = component.board || 1;
    for (const name in pinsRaw) {
      const h = pinsRaw[name];
      pinsSVG[name] = this.holeToSVG(h.col, h.row, board);
    }
    this._obstacles.push(renderer.bbox(pinsSVG, component.properties || {}));
  }
};



