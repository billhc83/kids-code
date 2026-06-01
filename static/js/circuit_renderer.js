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
 * Returns the id so it can be used in fill="url(#id)".
 */
function _defOnce(renderer, id, builderFn) {
  const defs = _ensureDefs(renderer);
  if (!defs.querySelector('#' + id)) builderFn(renderer, defs, id);
  return id;
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
    const bw = 1.8,  bh = 1.0;

    // 4 legs drawn from body-edge attachment points to actual pin holes
    [pins.TL, pins.TR, pins.BL, pins.BR].forEach(function(pin) {
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: pin.x, y1: pin.y, x2: pin.x, y2: pin.y + (pin.y < y ? -0.5 : 0.5),
        stroke: '#DDDDDD', 'stroke-width': 0.1, 'stroke-linecap': 'round'
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
 
    // Cap stem (connects base to dome)
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - 0.3, y: y - bh / 2 - 0.38,
      width: 0.6, height: 0.42, rx: 0.07,
      fill: capColor,
      stroke: '#881111', 'stroke-width': 0.04
    }));
 
    // Cap dome
    renderer.svgEl.appendChild(renderer._el('circle', {
      cx: x, cy: y - bh / 2 - 0.38,
      r: 0.42,
      fill: 'url(#' + capGradId + ')',
      stroke: '#881111', 'stroke-width': 0.04
    }));
 
    // Cap specular
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.13, cy: y - bh / 2 - 0.52,
      rx: 0.14, ry: 0.09,
      fill: '#FFFFFF', 'fill-opacity': 0.58,
      transform: 'rotate(-22,' + (x - 0.13) + ',' + (y - bh / 2 - 0.52) + ')'
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
    const r = 0.85;
 
    // Shadow
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x + 0.07, cy: y + 0.1, rx: r + 0.05, ry: r + 0.05,
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
    [[-0.12, -0.12], [0.12, -0.12], [0, 0.15],
     [-0.12, 0.12],  [0.12, 0.12]].forEach(function(d) {
      renderer.svgEl.appendChild(renderer._el('circle', {
        cx: x + d[0], cy: y + d[1], r: 0.055,
        fill: '#111'
      }));
    });
 
    // Top sheen
    renderer.svgEl.appendChild(renderer._el('ellipse', {
      cx: x - 0.28, cy: y - 0.33, rx: 0.32, ry: 0.18,
      fill: '#FFFFFF', 'fill-opacity': 0.09,
      transform: 'rotate(-28,' + (x - 0.28) + ',' + (y - 0.33) + ')'
    }));
 
    // + polarity marker
    const plusEl = renderer._el('text', {
      x: x - 0.28, y: y + 0.12,
      'text-anchor': 'middle', 'font-size': 0.4,
      fill: '#FFCC00', 'font-family': 'monospace', 'font-weight': 'bold'
    });
    plusEl.textContent = '+';
    renderer.svgEl.appendChild(plusEl);
 
    // PCB mount rim at base
    renderer.svgEl.appendChild(renderer._el('rect', {
      x: x - r, y: y + r - 0.05, width: r * 2, height: 0.18,
      rx: 0.04, fill: '#333', stroke: '#222', 'stroke-width': 0.03
    }));
 
    // Positive lead
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x - 0.3, y1: y + r + 0.1, x2: pins.positive.x, y2: pins.positive.y,
      stroke: '#CCCCCC', 'stroke-width': 0.1, 'stroke-linecap': 'round'
    }));

    // Negative lead
    renderer.svgEl.appendChild(renderer._el('line', {
      x1: x + 0.3, y1: y + r + 0.1, x2: pins.negative.x, y2: pins.negative.y,
      stroke: '#CCCCCC', 'stroke-width': 0.1, 'stroke-linecap': 'round'
    }));
 
    // Sound arc (kept — it's a nice schematic hint)
    renderer.svgEl.appendChild(renderer._el('path', {
      d: 'M ' + (x - 0.38) + ' ' + (y - r - 0.08) +
         ' Q ' + x + ' ' + (y - r - 0.52) +
         ' ' + (x + 0.38) + ' ' + (y - r - 0.08),
      fill: 'none', stroke: '#888', 'stroke-width': 0.1,
      'stroke-linecap': 'round'
    }));
    renderer.svgEl.appendChild(renderer._el('path', {
      d: 'M ' + (x - 0.55) + ' ' + (y - r - 0.22) +
         ' Q ' + x + ' ' + (y - r - 0.82) +
         ' ' + (x + 0.55) + ' ' + (y - r - 0.22),
      fill: 'none', stroke: '#666', 'stroke-width': 0.08,
      'stroke-linecap': 'round'
    }));
  },
 
 
  // ── SERVO ──────────────────────────────────────────────────────────────────
  // Off-breadboard component. pins.body positions the centre of the servo body
  // using any convenient breadboard hole as a visual anchor.
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
 
    const x = pins.body.x, y = pins.body.y;
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
 
    // 3-wire connector block
    const wireBaseX = x + bw * 0.18;
    const wireBaseY = y + bh / 2;
    const wires = [
      { dx: 0,    color: '#FF8800', label: 'S' },
      { dx: 0.55, color: '#CC2222', label: '+' },
      { dx: 1.1,  color: '#4444BB', label: '−' },
    ];
    wires.forEach(function(w) {
      const wx = wireBaseX + w.dx;
      // Connector pin housing
      renderer.svgEl.appendChild(renderer._el('rect', {
        x: wx - 0.18, y: wireBaseY,
        width: 0.36, height: 0.28, rx: 0.04,
        fill: '#333', stroke: '#222', 'stroke-width': 0.03
      }));
      // Wire lead
      renderer.svgEl.appendChild(renderer._el('line', {
        x1: wx, y1: wireBaseY + 0.28, x2: wx, y2: wireBaseY + 0.9,
        stroke: w.color, 'stroke-width': 0.13, 'stroke-linecap': 'round'
      }));
    });
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
  return { x0: cx - 1.6, y0: cy - 1.5, x1: cx + 1.6, y1: cy + 1.4 };
};

SYMBOL_RENDERERS.BUZZER.bbox = function(pins, props) {
  const cx = (pins.positive.x + pins.negative.x) / 2;
  const cy = (pins.positive.y + pins.negative.y) / 2;
  return { x0: cx - 1.4, y0: cy - 2.0, x1: cx + 1.4, y1: cy + 1.4 };
};

SYMBOL_RENDERERS.SERVO.bbox = function(pins, props) {
  const bx = pins.body.x, by = pins.body.y;
  return { x0: bx - 1.9, y0: by - 2.2, x1: bx + 1.9, y1: by + 2.8 };
};

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
  }

  holeToSVG(col, row) {
    return { x: this.BB_ANCHOR.x + (30 - row), y: this.BB_ANCHOR.y + this.COL_OFFSETS[col] };
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

    // Power rail: "+1.5" or "-2.10"
    const railMatch = /^([+\-][12])\.(\d+)$/.exec(ref);
    if (railMatch) return this.holeToSVG(railMatch[1], parseInt(railMatch[2]));

    // Standard bus hole: "A10" or "E7"
    const holeMatch = /^([A-Ja-j]+)(\d+)$/.exec(ref);
    if (holeMatch) return this.holeToSVG(holeMatch[1].toUpperCase(), parseInt(holeMatch[2]));

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

  drawBreadboard() {
    const a = this.BB_ANCHOR;
    this._track(a.x - 2, a.y - 1.0);
    this._track(a.x + 31, a.y + 18);

    // White board body
    this.svgEl.appendChild(this._el('rect', {
      x: a.x - 0.5, y: a.y - 1.0, width: 30.5, height: 18.0,
      rx: 0.5, fill: '#FAFAFA', stroke: '#BBB', 'stroke-width': 0.1
    }));

    // Power rail tints
    this.svgEl.appendChild(this._el('rect', { x: a.x - 0.4, y: a.y + 0 - 0.4,  width: 29.8, height: 0.8, fill: '#FFD5D5' }));
    this.svgEl.appendChild(this._el('rect', { x: a.x - 0.4, y: a.y + 1 - 0.4,  width: 29.8, height: 0.8, fill: '#D5D5FF' }));
    this.svgEl.appendChild(this._el('rect', { x: a.x - 0.4, y: a.y + 15 - 0.4, width: 29.8, height: 0.8, fill: '#FFD5D5' }));
    this.svgEl.appendChild(this._el('rect', { x: a.x - 0.4, y: a.y + 16 - 0.4, width: 29.8, height: 0.8, fill: '#D5D5FF' }));

    // Centre DIP gap
    this.svgEl.appendChild(this._el('line', {
      x1: a.x - 0.5, y1: a.y + 8, x2: a.x + 29.5, y2: a.y + 8,
      stroke: '#C8C8C8', 'stroke-width': 0.25, 'stroke-dasharray': '0.6 0.4'
    }));

    // All holes
    const allCols = ['+1','-1','A','B','C','D','E','F','G','H','I','J','+2','-2'];
    for (let ci = 0; ci < allCols.length; ci++) {
      for (let row = 1; row <= 30; row++) {
        const p = this.holeToSVG(allCols[ci], row);
        this.svgEl.appendChild(this._el('circle', { cx: p.x, cy: p.y, r: 0.3, fill: '#555' }));
      }
    }

    // Column letter labels (A-J) above board
    ['A','B','C','D','E','F','G','H','I','J'].forEach(function(col) {
      const y = a.y + this.COL_OFFSETS[col];
      this._txt(col, { x: a.x - 1.2, y: y + 0.25, 'text-anchor': 'end',
        'font-size': 0.65, fill: '#555', 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // Power rail + / - labels above board
    [['+1', '+', '#B00000'], ['-1', '−', '#0000B0'],
     ['+2', '+', '#B00000'], ['-2', '−', '#0000B0']].forEach(function(e) {
      const y = a.y + this.COL_OFFSETS[e[0]];
      this._txt(e[1], { x: a.x - 1.2, y: y + 0.25, 'text-anchor': 'end',
        'font-size': 0.7, fill: e[2], 'font-family': 'monospace', 'font-weight': 'bold' });
    }, this);

    // Row numbers on the right side — every 5th + row 1
    [1, 5, 10, 15, 20, 25, 30].forEach(function(row) {
      this._txt(String(row), { x: a.x + (30 - row), y: a.y + 17.5,
        'text-anchor': 'middle', 'font-size': 0.6, fill: '#888', 'font-family': 'monospace' });
    }, this);
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
    let cx = 0, cy = 0, n = 0;
    for (const name in pinsRaw) {
      const h = pinsRaw[name];
      pinsSVG[name] = this.holeToSVG(h.col, h.row);
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

  drawWire(connection) {
    const start = this._resolveEndpoint(connection.from);
    const end   = this._resolveEndpoint(connection.to);
    const fromBB  = this._isInBreadboard(start), fromARD = this._isInArduino(start);
    const toBB    = this._isInBreadboard(end),   toARD   = this._isInArduino(end);

    // 2.3 Rail preference: bias toward horizontal-first for rail-row endpoints
    const bb = this.BB_ANCHOR;
    const ard = this.ARD_ANCHOR;
    const RAIL_OFFSETS = [0, 1, 15, 16];
    const startInRail = fromBB && RAIL_OFFSETS.indexOf(start.y - bb.y) !== -1;
    const endInRail   = toBB   && RAIL_OFFSETS.indexOf(end.y   - bb.y) !== -1;

    const candidates = [];
    const hFirst = { x: end.x, y: start.y };
    const vFirst = { x: start.x, y: end.y };

    if (fromARD) {
      // Horizontal-first from a vertical header edge leaves the board immediately.
      candidates.push(hFirst);
      candidates.push(vFirst);
    } else if (toARD) {
      // Vertical-first results in horizontal entry into the Arduino header.
      candidates.push(vFirst);
      candidates.push(hFirst);
    } else {
      if ((fromBB && toARD) || (fromARD && toBB)) {
        const bbPt  = fromBB ? start : end;
        const ardPt = fromARD ? start : end;
        candidates.push({ x: bbPt.x, y: ardPt.y });
      }
      if (startInRail) candidates.unshift(hFirst);
      else if (endInRail) candidates.unshift(vFirst);
      candidates.push(hFirst);
      candidates.push(vFirst);
    }

    let chosenMid = null;
    for (let i = 0; i < candidates.length; i++) {
      const mid = candidates[i];
      const s1 = this._normSeg(start.x, start.y, mid.x, mid.y);
      const s2 = this._normSeg(mid.x, mid.y, end.x, end.y);
      if (this._segmentClear(s1) && this._segmentClear(s2)) { chosenMid = mid; break; }
    }
    // 2.1 Z-shape candidates: 3-segment paths tried before detour fallback
    if (!chosenMid) {
      const snap = function(v) { return Math.round(v * 2) / 2; };
      const dx = end.x - start.x, dy = end.y - start.y;
      const zCands = [];

      // Preferred Z-shapes for Arduino breakout (leave board immediately)
      if (fromARD) {
        const outX = (start.x <= ard.x + 1) ? start.x - 2 : start.x + 2;
        zCands.push([{ x: outX, y: start.y }, { x: outX, y: end.y }]);
      }
      if (toARD) {
        const outX = (end.x <= ard.x + 1) ? end.x - 2 : end.x + 2;
        zCands.push([{ x: outX, y: start.y }, { x: outX, y: end.y }]);
      }

      zCands.push([{ x: snap(start.x + dx * 0.25), y: start.y }, { x: snap(start.x + dx * 0.25), y: end.y }]);
      zCands.push([{ x: start.x, y: snap(start.y + dy * 0.25) }, { x: end.x,   y: snap(start.y + dy * 0.25) }]);

      for (let z = 0; z < zCands.length; z++) {
        const m1 = zCands[z][0], m2 = zCands[z][1];
        const s1 = this._normSeg(start.x, start.y, m1.x, m1.y);
        const s2 = this._normSeg(m1.x, m1.y, m2.x, m2.y);
        const s3 = this._normSeg(m2.x, m2.y, end.x, end.y);
        if (this._segmentClear(s1) && this._segmentClear(s2) && this._segmentClear(s3)) {
          this._segments.push(s1); this._segments.push(s2); this._segments.push(s3);
          const color = connection.color || '#555';
          this.svgEl.appendChild(this._el('path', {
            d: 'M '+start.x+' '+start.y+' L '+m1.x+' '+m1.y+' L '+m2.x+' '+m2.y+' L '+end.x+' '+end.y,
            stroke: color, 'stroke-width': 0.4, fill: 'none',
            'stroke-linecap': 'round', 'stroke-linejoin': 'round'
          }));
          if (this._isInBreadboard(start))
            this.svgEl.appendChild(this._el('circle', { cx: start.x, cy: start.y, r: 0.22, fill: color }));
          if (this._isInBreadboard(end))
            this.svgEl.appendChild(this._el('circle', { cx: end.x, cy: end.y, r: 0.22, fill: color }));
          
          this._allWires.push({
            fromRaw: connection.from,
            toRaw: connection.to,
            pathData: 'M '+start.x+' '+start.y+' L '+m1.x+' '+m1.y+' L '+m2.x+' '+m2.y+' L '+end.x+' '+end.y,
            start: start,
            end: end
          });
          return;
        }
      }
    }

    if (!chosenMid) {
      const base = candidates[candidates.length - 1];
      const snap = function(v) { return Math.round(v * 2) / 2; };
      const detourDeltas = [
        {dx:  0.5, dy: 0}, {dx: -0.5, dy: 0},
        {dx: 0, dy:  0.5}, {dx: 0, dy: -0.5},
        {dx:  1.0, dy: 0}, {dx: -1.0, dy: 0},
        {dx: 0, dy:  1.0}, {dx: 0, dy: -1.0},
        {dx:  1.5, dy: 0}, {dx: -1.5, dy: 0},
        {dx: 0, dy:  1.5}, {dx: 0, dy: -1.5},
      ];
      for (let d = 0; d < detourDeltas.length; d++) {
        const mid = { x: snap(base.x + detourDeltas[d].dx), y: snap(base.y + detourDeltas[d].dy) };
        const s1 = this._normSeg(start.x, start.y, mid.x, mid.y);
        const s2 = this._normSeg(mid.x, mid.y, end.x, end.y);
        if (this._segmentClear(s1) && this._segmentClear(s2)) { chosenMid = mid; break; }
      }
    }

    if (!chosenMid) {
      if (fromARD) chosenMid = hFirst;
      else if (toARD) chosenMid = vFirst;
      else chosenMid = hFirst;
    }

    const m = chosenMid;
    this._segments.push(this._normSeg(start.x, start.y, m.x, m.y));
    this._segments.push(this._normSeg(m.x, m.y, end.x, end.y));

    this._wirePaths.push({ start, mid: m, end, color: connection.color || '#555', fromRaw: connection.from, toRaw: connection.to });
    
    this._allWires.push({
        fromRaw: connection.from,
        toRaw: connection.to,
        pathData: 'M '+start.x+' '+start.y+' L '+m.x+' '+m.y+' L '+end.x+' '+end.y,
        start: start,
        end: end
    });
  }

  _isInBreadboard(pt) {
    const a = this.BB_ANCHOR;
    return pt.x >= a.x - 1 && pt.x <= a.x + 31 && pt.y >= a.y - 1 && pt.y <= a.y + 18;
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
    this._bbox = null;
    this._debugOverlay = null;
    this._debugInfoBar = null;
    this.svgEl = this._el('svg', { xmlns: this.svgNS, style: 'width:100%;height:auto;display:block;' });
    this.drawBreadboard();
    this.drawArduino();
    this._segments = [];
    this._wirePaths = [];
    this._allWires = [];
    this._drawnSegs = [];
    this._buildObstacleRegistry();
    const self = this;
    const _powerKw = ['GND', '5V', 'VIN', '3V3', '+1', '-1', '+2', '-2'];
    function _isPow(ep) { return _powerKw.some(function(k) { return ep.indexOf(k) !== -1; }); }
    function _len(conn) {
      try {
        const s = self._resolveEndpoint(conn.from), e = self._resolveEndpoint(conn.to);
        return Math.sqrt((e.x-s.x)*(e.x-s.x)+(e.y-s.y)*(e.y-s.y));
      } catch(ex) { return 999; }
    }
    const connections = (this.def.connections || []).slice().sort(function(a, b) {
      const pa = (_isPow(a.from)||_isPow(a.to)) ? 0 : 1;
      const pb = (_isPow(b.from)||_isPow(b.to)) ? 0 : 1;
      if (pa !== pb) return pa - pb;
      return _len(a) - _len(b);
    });
    for (let i = 0; i < connections.length; i++) this.drawWire(connections[i]);
    this._drawBundledWires();
    this._drawHopArcs();
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

    const maskId = 'greyout-mask';
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
                for (const name in pinsRaw) {
                    pinsSVG[name] = this.holeToSVG(pinsRaw[name].col, pinsRaw[name].row);
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
CircuitRenderer.prototype._normSeg = function(ax, ay, bx, by) {
  return { x0: Math.min(ax,bx), y0: Math.min(ay,by), x1: Math.max(ax,bx), y1: Math.max(ay,by) };
};

CircuitRenderer.prototype._segHitsRect = function(seg, rect) {
  const isH = seg.y0 === seg.y1;
  const isV = seg.x0 === seg.x1;
  // Strict inequality in the travel direction ensures segments can touch/start on the edge
  // but not travel along it or cross through it.
  if (isH) return seg.y0 >= rect.y0 && seg.y0 <= rect.y1 && seg.x0 < rect.x1 && seg.x1 > rect.x0;
  if (isV) return seg.x0 >= rect.x0 && seg.x0 <= rect.x1 && seg.y0 < rect.y1 && seg.y1 > rect.y0;
  return false;
};

CircuitRenderer.prototype._segsOverlap = function(a, b) {
  // 0.55 = ~half a grid unit; prevents parallel wires crowding each other.
  // Adjacent rows/cols are 1 unit apart so those are still routable.
  const NEAR = 0.55;
  const aH = a.y0 === a.y1, bH = b.y0 === b.y1;
  const aV = a.x0 === a.x1, bV = b.x0 === b.x1;
  if (aH && bH && Math.abs(a.y0 - b.y0) < NEAR) return a.x0 < b.x1 && a.x1 > b.x0;
  if (aV && bV && Math.abs(a.x0 - b.x0) < NEAR) return a.y0 < b.y1 && a.y1 > b.y0;
  return false;
};

CircuitRenderer.prototype._segmentClear = function(seg) {
  for (let i = 0; i < this._obstacles.length; i++) {
    if (this._segHitsRect(seg, this._obstacles[i])) return false;
  }
  for (let i = 0; i < this._segments.length; i++) {
    if (this._segsOverlap(seg, this._segments[i])) return false;
  }
  return true;
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
    for (const name in pinsRaw) {
      const h = pinsRaw[name];
      pinsSVG[name] = this.holeToSVG(h.col, h.row);
    }
    this._obstacles.push(renderer.bbox(pinsSVG, component.properties || {}));
  }
};

CircuitRenderer.prototype._drawBundledWires = function() {
  if (!this._wirePaths || !this._wirePaths.length) return;

  const segs = [];
  for (let i = 0; i < this._wirePaths.length; i++) {
    const p = this._wirePaths[i];
    segs.push(Object.assign(this._normSeg(p.start.x, p.start.y, p.mid.x, p.mid.y), { wi: i, si: 0 }));
    segs.push(Object.assign(this._normSeg(p.mid.x, p.mid.y, p.end.x, p.end.y),     { wi: i, si: 1 }));
  }

  function collinear(a, b) {
    if (a.y0 === a.y1 && b.y0 === b.y1 && Math.abs(a.y0 - b.y0) < 0.01)
      return a.x0 < b.x1 && a.x1 > b.x0;
    if (a.x0 === a.x1 && b.x0 === b.x1 && Math.abs(a.x0 - b.x0) < 0.01)
      return a.y0 < b.y1 && a.y1 > b.y0;
    return false;
  }

  function bundleOffsets(n) {
    if (n === 2) return [-0.25, 0.25];
    if (n === 3) return [-0.3, 0, 0.3];
    const half = 0.25 * (n - 1);
    return Array.from({ length: n }, function(_, k) { return -half + k * 0.5; });
  }

  const offsets = new Array(segs.length).fill(0);
  const bundled = new Array(segs.length).fill(false);
  for (let i = 0; i < segs.length; i++) {
    if (bundled[i]) continue;
    const bundle = [i];
    for (let j = i + 1; j < segs.length; j++) {
      if (!bundled[j] && collinear(segs[i], segs[j])) bundle.push(j);
    }
    if (bundle.length >= 2) {
      const boff = bundleOffsets(bundle.length);
      for (let k = 0; k < bundle.length; k++) {
        offsets[bundle[k]] = boff[k];
        bundled[bundle[k]] = true;
      }
    }
  }

  for (let i = 0; i < this._wirePaths.length; i++) {
    const p = this._wirePaths[i];
    const seg0 = segs[i * 2], seg1 = segs[i * 2 + 1];
    const off0 = offsets[i * 2], off1 = offsets[i * 2 + 1];
    const isH0 = seg0.y0 === seg0.y1, isH1 = seg1.y0 === seg1.y1;

    let sx = p.start.x, sy = p.start.y;
    let mx = p.mid.x,   my = p.mid.y;
    let ex = p.end.x,   ey = p.end.y;

    if (off0 !== 0) { if (isH0) { sy += off0; my += off0; } else { sx += off0; mx += off0; } }
    if (off1 !== 0) { if (isH1) { my += off1; ey += off1; } else { mx += off1; ex += off1; } }

    this.svgEl.appendChild(this._el('path', {
      d: 'M '+sx+' '+sy+' L '+mx+' '+my+' L '+ex+' '+ey,
      stroke: p.color, 'stroke-width': 0.4, fill: 'none',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round'
    }));
    this._drawnSegs.push(this._normSeg(sx, sy, mx, my));
    this._drawnSegs.push(this._normSeg(mx, my, ex, ey));
    if (this._isInBreadboard({ x: sx, y: sy }))
      this.svgEl.appendChild(this._el('circle', { cx: sx, cy: sy, r: 0.22, fill: p.color }));
    if (this._isInBreadboard({ x: ex, y: ey }))
      this.svgEl.appendChild(this._el('circle', { cx: ex, cy: ey, r: 0.22, fill: p.color }));
  }
};

CircuitRenderer.prototype._drawHopArcs = function() {
  if (!this._drawnSegs || this._drawnSegs.length < 2) return;

  const r = 0.18;
  const segs = this._drawnSegs;

  for (let i = 0; i < segs.length - 1; i++) {
    for (let j = i + 1; j < segs.length; j++) {
      const a = segs[i];
      const b = segs[j];

      if (a.y0 === a.y1 && b.x0 === b.x1) {
        const cx = b.x0, cy = a.y0;
        if (cx > a.x0 && cx < a.x1 && cy > b.y0 && cy < b.y1) {
          this.svgEl.appendChild(this._el('path', {
            d: 'M '+cx+' '+(cy-r)+' A '+r+' '+r+' 0 0 1 '+cx+' '+(cy+r),
            stroke: '#FFFFFF', 'stroke-width': 0.5, fill: 'none', 'stroke-linecap': 'round'
          }));
        }
      } else if (a.x0 === a.x1 && b.y0 === b.y1) {
        const cx = a.x0, cy = b.y0;
        if (cy > a.y0 && cy < a.y1 && cx > b.x0 && cx < b.x1) {
          this.svgEl.appendChild(this._el('path', {
            d: 'M '+(cx-r)+' '+cy+' A '+r+' '+r+' 0 0 0 '+(cx+r)+' '+cy,
            stroke: '#FFFFFF', 'stroke-width': 0.5, fill: 'none', 'stroke-linecap': 'round'
          }));
        }
      }
    }
  }
};
