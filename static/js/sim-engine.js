/**
 * SimEngine — interactive Arduino circuit simulator for the drawer sim tab.
 * Usage: SimEngine.init(containerElement, simConfig)
 *
 * simConfig shape:
 *   components: [{type, id, color?, pin?, label}]
 *   behaviors:  [{when: {id: state, ...}, then: {id: state, ...}}]  — hand-authored,
 *               used only by init(). Not read by initInterpreted().
 *   mode:       "code_driven" → initCodeDriven (timeline replay of a regex-extracted
 *               sketch, no branching awareness)
 *               "interpreted" → initInterpreted (discrete request/response through the
 *               real Phase 0 interpreter, see SIM_ENGINE_ROLLOUT_SPEC.md)
 *               anything else → init() (client-only hand-authored `behaviors`)
 *   endpoint    (code_driven / interpreted only) — sim-run URL to POST to. Defaults to
 *               '/sim/run' when absent.
 *
 * Special then-keys:
 *   _sequence: ["id1","id2",...]  — starts a cyclic LED flash loop
 *   _interval: <ms>              — interval for _sequence (default 150)
 *   _stop_sequence: "yes"        — stops any running sequence
 *   _beep: "buzzerId"            — starts a pulsing on/off beep on a buzzer
 *   _beep_interval: <ms>         — half-period for _beep (default 400)
 *   _stop_beep: "yes"            — stops any running beep
 *
 * Special component types:
 *   timer  — shows a running millisecond counter; toggled via {timerId: "toggle"}
 *   sonar  — HC-SR04 ultrasonic sensor with a distance slider (0-100 cm).
 *            Under init(): state emitted is one of 3 hand-authored zones —
 *            "safe" (>50 cm), "warning" (20-50 cm), "danger" (<20 cm).
 *            Under initInterpreted(): no zones — the slider's raw pulse
 *            duration (debounced) is sent on the component's `pin_echo`, and
 *            whatever the sketch's own map()/if-chain does with it is what
 *            shows up (e.g. a continuous buzzer pitch via `pin_frequencies`
 *            — see SIM_ENGINE_ROLLOUT_SPEC.md item 5).
 *   servo  — output-only rotating dial (0-180°). Only meaningful under
 *            initInterpreted() (init()'s hand-authored `behaviors` has no
 *            way to describe an angle) — painted from the result's
 *            `servo_angles`/`servo_sequences` keys, never hand-authored.
 *            See SIM_ENGINE_ROLLOUT_SPEC.md item 6 / project_nineteen.
 */
window.SimEngine = (function () {
  'use strict';
  var activeRequestId = 0;

  /* ── LED colour palettes ─────────────────────────────────────────────────── */
  var PALETTES = {
    red:    { off:'#7a1010', collar:'#4d0a0a', on:'#ff1a1a', onCollar:'#cc0000', glow:'#ff2222' },
    yellow: { off:'#6e5500', collar:'#453400', on:'#ffe000', onCollar:'#ccaa00', glow:'#ffcc00' },
    green:  { off:'#0a4a0a', collar:'#063506', on:'#00dd44', onCollar:'#009900', glow:'#00ff44' },
    blue:   { off:'#0a1a5a', collar:'#060e3a', on:'#2299ff', onCollar:'#1177cc', glow:'#0088ff' },
    white:  { off:'#3a3a3a', collar:'#222222', on:'#f0f0f0', onCollar:'#aaaaaa', glow:'#ffffff' },
  };
  PALETTES.clear = PALETTES.white;

  /* ── SVG builders ────────────────────────────────────────────────────────── */
  function ledSVG(id, color) {
    var c = PALETTES[color] || PALETTES.red;
    return (
      '<svg data-id="' + id + '" width="56" height="82" viewBox="-28 -12 56 82"' +
      ' style="overflow:visible;display:block;cursor:default" tabindex="-1">' +
      '<circle id="' + id + '-gr3" cx="0" cy="21" r="34" fill="' + c.glow + '" opacity="0" pointer-events="none"/>' +
      '<circle id="' + id + '-gr2" cx="0" cy="21" r="24" fill="' + c.glow + '" opacity="0" pointer-events="none"/>' +
      '<circle id="' + id + '-gr1" cx="0" cy="21" r="16" fill="' + c.glow + '" opacity="0" pointer-events="none"/>' +
      '<line x1="-7" y1="47" x2="-7" y2="65" stroke="#666" stroke-width="2" stroke-linecap="round" pointer-events="none"/>' +
      '<line x1="7"  y1="47" x2="7"  y2="72" stroke="#666" stroke-width="2" stroke-linecap="round" pointer-events="none"/>' +
      '<path id="' + id + '-dome" d="M -16,21 A 16,16 0 0,0 16,21 Z" fill="' + c.off + '"/>' +
      '<rect id="' + id + '-body" x="-16" y="21" width="32" height="20" fill="' + c.off + '"/>' +
      '<rect id="' + id + '-coll" x="-16" y="38" width="32" height="8" rx="2" fill="' + c.collar + '"/>' +
      '<path d="M -6,10 A 16,16 0 0,0 6,10 L 4,21 L -4,21 Z" fill="white" opacity="0.22" pointer-events="none"/>' +
      '<rect x="-16" y="5" width="32" height="46" fill="transparent"/>' +
      '</svg>'
    );
  }

  function buttonSVG(id) {
    return (
      '<svg data-id="' + id + '" width="66" height="66" viewBox="-33 -33 66 66"' +
      ' style="overflow:visible;display:block;cursor:pointer;-webkit-user-select:none;user-select:none">' +
      '<rect x="-26" y="-26" width="52" height="52" rx="5" fill="#267326" stroke="#1a5c1a" stroke-width="1.5"/>' +
      '<line x1="-26" y1="-12" x2="-16" y2="-12" stroke="#48c248" stroke-width="1.2" opacity="0.55"/>' +
      '<line x1="16"  y1="-12" x2="26"  y2="-12" stroke="#48c248" stroke-width="1.2" opacity="0.55"/>' +
      '<line x1="-26" y1="12"  x2="-16" y2="12"  stroke="#48c248" stroke-width="1.2" opacity="0.55"/>' +
      '<line x1="16"  y1="12"  x2="26"  y2="12"  stroke="#48c248" stroke-width="1.2" opacity="0.55"/>' +
      '<rect x="-31" y="-16" width="7" height="5" rx="1.5" fill="#c9a000"/>' +
      '<rect x="24"  y="-16" width="7" height="5" rx="1.5" fill="#c9a000"/>' +
      '<rect x="-31" y="11"  width="7" height="5" rx="1.5" fill="#c9a000"/>' +
      '<rect x="24"  y="11"  width="7" height="5" rx="1.5" fill="#c9a000"/>' +
      '<circle cx="0" cy="0" r="19" fill="#5a5a5a"/>' +
      '<circle cx="0" cy="1.5" r="16" fill="#333"/>' +
      '<circle id="' + id + '-cap" cx="0" cy="-1.5" r="14.5" fill="#d2cac0"/>' +
      '<ellipse id="' + id + '-shine" cx="-3" cy="-6" rx="5" ry="3" fill="white" opacity="0.28" pointer-events="none"/>' +
      '</svg>'
    );
  }

  function switchSVG(id) {
    return (
      '<svg data-id="' + id + '" width="68" height="46" viewBox="-34 -18 68 46"' +
      ' style="overflow:visible;display:block;cursor:pointer;-webkit-user-select:none;user-select:none">' +
      '<rect x="-28" y="-12" width="56" height="24" rx="12" fill="#555" stroke="#333" stroke-width="1"/>' +
      '<circle id="' + id + '-knob" cx="-10" cy="0" r="11" fill="#bbb" stroke="#888" stroke-width="1.2"/>' +
      '<ellipse id="' + id + '-kshine" cx="-12" cy="-4" rx="4" ry="2.5" fill="white" opacity="0.22" pointer-events="none"/>' +
      '<line x1="-8" y1="12" x2="-8" y2="26" stroke="#666" stroke-width="1.5"/>' +
      '<line x1="8"  y1="12" x2="8"  y2="26" stroke="#666" stroke-width="1.5"/>' +
      '</svg>'
    );
  }

  function buzzerSVG(id) {
    return (
      '<svg data-id="' + id + '" width="56" height="66" viewBox="-28 -16 56 66"' +
      ' style="overflow:visible;display:block;cursor:default">' +
      '<circle id="' + id + '-body" cx="0" cy="0" r="22" fill="#2a2a2a" stroke="#444" stroke-width="1.5"/>' +
      '<circle cx="0" cy="0" r="15" fill="#1a1a1a"/>' +
      '<circle cx="0" cy="0" r="10" fill="none" stroke="#555" stroke-width="1.5"/>' +
      '<circle id="' + id + '-dot" cx="0" cy="0" r="4" fill="#444"/>' +
      '<line x1="-6" y1="22" x2="-6" y2="42" stroke="#666" stroke-width="1.5"/>' +
      '<line x1="6"  y1="22" x2="6"  y2="42" stroke="#666" stroke-width="1.5"/>' +
      '</svg>'
    );
  }

  function servoSVG(id) {
    return (
      '<svg data-id="' + id + '" width="80" height="72" viewBox="-40 -8 80 72"' +
      ' style="overflow:visible;display:block;cursor:default">' +
      /* Housing */
      '<rect x="-24" y="18" width="48" height="34" rx="4" fill="#2563eb" stroke="#1e40af" stroke-width="1.5"/>' +
      '<rect x="-24" y="18" width="48" height="9" fill="#1e40af"/>' +
      '<rect x="-30" y="24" width="6" height="10" rx="1.5" fill="#1e3a8a"/>' +
      '<rect x="24"  y="24" width="6" height="10" rx="1.5" fill="#1e3a8a"/>' +
      /* Output shaft */
      '<circle cx="0" cy="18" r="7" fill="#1e293b" stroke="#0f172a" stroke-width="1"/>' +
      /* Rotating arm — origin is the shaft center (0,18); applyServo() sets
         the rotate() transform's angle */
      '<g id="' + id + '-arm" transform="rotate(-90 0 18)">' +
      '<rect x="-3" y="-14" width="6" height="32" rx="3" fill="#f59e0b" stroke="#b45309" stroke-width="1"/>' +
      '<circle cx="0" cy="-14" r="3.5" fill="#fbbf24"/>' +
      '</g>' +
      '</svg>'
    );
  }

  function timerSVG(id) {
    return (
      '<svg data-id="' + id + '" width="140" height="56" viewBox="0 0 140 56"' +
      ' style="display:block;cursor:default">' +
      '<rect x="1" y="1" width="138" height="54" rx="8" fill="#111" stroke="#333" stroke-width="1.5"/>' +
      '<text id="' + id + '-display" x="70" y="37" text-anchor="middle"' +
      ' font-family="Courier New,monospace" font-size="22" font-weight="bold"' +
      ' fill="#00ff88" letter-spacing="1">0.000s</text>' +
      '</svg>'
    );
  }

  function sonarSVG(id) {
    return (
      '<svg data-id="' + id + '" width="100" height="80" viewBox="-50 -15 100 85"' +
      ' style="overflow:visible;display:block;cursor:default">' +
      /* Signal rings — expand upward, hidden by default */
      '<circle id="' + id + '-r3" cx="0" cy="-2" r="36" fill="none" stroke="#00ff88" stroke-width="0.8" opacity="0" pointer-events="none"/>' +
      '<circle id="' + id + '-r2" cx="0" cy="-2" r="24" fill="none" stroke="#00ff88" stroke-width="1.1" opacity="0" pointer-events="none"/>' +
      '<circle id="' + id + '-r1" cx="0" cy="-2" r="14" fill="none" stroke="#00ff88" stroke-width="1.5" opacity="0" pointer-events="none"/>' +
      /* PCB body */
      '<rect x="-42" y="5" width="84" height="52" rx="4" fill="#1a5c1a" stroke="#0d3d0d" stroke-width="1.5"/>' +
      /* Silkscreen label */
      '<text x="0" y="15" text-anchor="middle" font-family="Arial,sans-serif" font-size="7" font-weight="bold" fill="#2d8a2d" pointer-events="none">HC-SR04</text>' +
      /* Left transducer (TRIG) */
      '<circle cx="-20" cy="34" r="16" fill="#222" stroke="#555" stroke-width="1.5"/>' +
      '<circle cx="-20" cy="34" r="11" fill="#1a1a1a"/>' +
      '<circle cx="-20" cy="34" r="7"  fill="#333"/>' +
      '<circle cx="-20" cy="34" r="2.5" fill="#666"/>' +
      /* Right transducer (ECHO) */
      '<circle cx="20" cy="34" r="16" fill="#222" stroke="#555" stroke-width="1.5"/>' +
      '<circle cx="20" cy="34" r="11" fill="#1a1a1a"/>' +
      '<circle cx="20" cy="34" r="7"  fill="#333"/>' +
      '<circle cx="20" cy="34" r="2.5" fill="#666"/>' +
      /* Pins */
      '<line x1="-33" y1="57" x2="-33" y2="70" stroke="#aaa" stroke-width="2" stroke-linecap="round"/>' +
      '<line x1="-11" y1="57" x2="-11" y2="70" stroke="#aaa" stroke-width="2" stroke-linecap="round"/>' +
      '<line x1="11"  y1="57" x2="11"  y2="70" stroke="#aaa" stroke-width="2" stroke-linecap="round"/>' +
      '<line x1="33"  y1="57" x2="33"  y2="70" stroke="#aaa" stroke-width="2" stroke-linecap="round"/>' +
      /* Pin labels */
      '<text x="-33" y="76" text-anchor="middle" font-family="Arial" font-size="5.5" fill="#64748b">VCC</text>' +
      '<text x="-11" y="76" text-anchor="middle" font-family="Arial" font-size="5.5" fill="#64748b">GND</text>' +
      '<text x="11"  y="76" text-anchor="middle" font-family="Arial" font-size="5.5" fill="#64748b">TRIG</text>' +
      '<text x="33"  y="76" text-anchor="middle" font-family="Arial" font-size="5.5" fill="#64748b">ECHO</text>' +
      '</svg>'
    );
  }

  /* ── Visual state appliers ───────────────────────────────────────────────── */
  function applyLED(id, on, color) {
    var c = PALETTES[color] || PALETTES.red;
    var dome = document.getElementById(id + '-dome');
    var body = document.getElementById(id + '-body');
    var coll = document.getElementById(id + '-coll');
    if (dome) dome.setAttribute('fill', on ? c.on  : c.off);
    if (body) body.setAttribute('fill', on ? c.on  : c.off);
    if (coll) coll.setAttribute('fill', on ? c.onCollar : c.collar);
    [1, 2, 3].forEach(function (n) {
      var g = document.getElementById(id + '-gr' + n);
      if (g) g.setAttribute('opacity', on ? (n === 1 ? '0.65' : n === 2 ? '0.35' : '0.15') : '0');
    });
  }

  function applyBuzzer(id, on) {
    var body = document.getElementById(id + '-body');
    var dot  = document.getElementById(id + '-dot');
    if (body) body.setAttribute('fill', on ? '#0a4a2a' : '#2a2a2a');
    if (dot)  dot.setAttribute('fill',  on ? '#00ff88' : '#444');
  }

  /* freq is Hz or undefined/null — blanked when the buzzer isn't actively
     toning at a known frequency (see SIM_ENGINE_ROLLOUT_SPEC.md item 5). */
  function applyBuzzerFreq(id, freq) {
    var el = document.getElementById(id + '-hz');
    if (el) el.textContent = (freq === undefined || freq === null) ? '' : Math.round(freq) + ' Hz';
  }

  /* angle is Arduino servo.write()'s 0-180 degree argument. Rotation is
     offset -90deg so 90 (the SG90's natural rest/center position most
     projects write on startup) points the arm straight up rather than
     sideways. */
  function applyServo(id, angle) {
    var arm = document.getElementById(id + '-arm');
    if (arm) arm.setAttribute('transform', 'rotate(' + (angle - 90) + ' 0 18)');
    var readout = document.getElementById(id + '-readout');
    if (readout) readout.textContent = Math.round(angle) + '°';
  }

  function applySwitch(id, on) {
    var knob   = document.getElementById(id + '-knob');
    var kshine = document.getElementById(id + '-kshine');
    if (knob) {
      knob.setAttribute('cx',   on ? '10' : '-10');
      knob.setAttribute('fill', on ? '#22c55e' : '#bbb');
    }
    if (kshine) kshine.setAttribute('cx', on ? '8' : '-12');
  }

  function applyButton(id, pressed) {
    var cap   = document.getElementById(id + '-cap');
    var shine = document.getElementById(id + '-shine');
    if (cap) {
      cap.setAttribute('cy',   pressed ? '1.5'  : '-1.5');
      cap.setAttribute('fill', pressed ? '#a8a09a' : '#d2cac0');
    }
    if (shine) shine.setAttribute('opacity', pressed ? '0.1' : '0.28');
  }

  var SONAR_ZONE_COLORS  = { safe: '#00ff88', warning: '#ffcc00', danger: '#ff4444' };
  var SONAR_ZONE_LABELS  = { safe: '🟢 SAFE', warning: '🟡 WARNING', danger: '🔴 DANGER' };

  function applySonar(id, zone, customLabels) {
    var labels = customLabels || SONAR_ZONE_LABELS;
    var color = SONAR_ZONE_COLORS[zone] || '#00ff88';
    /* Recolour signal rings */
    [1, 2, 3].forEach(function (n) {
      var r = document.getElementById(id + '-r' + n);
      if (r) r.setAttribute('stroke', color);
    });
    /* Recolour readout badge */
    var readout = document.getElementById(id + '-readout');
    var zoneTag = document.getElementById(id + '-zone');
    if (readout) readout.style.color = color;
    if (zoneTag) { zoneTag.textContent = labels[zone] || zone; zoneTag.style.color = color; }
  }

  function sonarPingFlash(id) {
    var opacities = ['0.8', '0.5', '0.22'];
    [1, 2, 3].forEach(function (n, i) {
      var r = document.getElementById(id + '-r' + n);
      if (r) r.setAttribute('opacity', opacities[i]);
    });
    setTimeout(function () {
      [1, 2, 3].forEach(function (n) {
        var r = document.getElementById(id + '-r' + n);
        if (r) r.setAttribute('opacity', '0');
      });
    }, 700);
  }

  /* ── Build component column DOM element ─────────────────────────────────── */
  function makeLbl(comp) {
    var lbl = document.createElement('div');
    lbl.style.cssText = 'font-size:10px;font-weight:700;color:#94a3b8;text-align:center;line-height:1.5;';
    lbl.textContent = comp.label || comp.id;
    if (comp.pin !== undefined && comp.pin !== '') {
      var pinSpan = document.createElement('span');
      pinSpan.style.cssText = 'display:block;font-size:9px;font-weight:400;color:#64748b;';
      pinSpan.textContent = 'Pin ' + comp.pin;
      lbl.appendChild(pinSpan);
    }
    return lbl;
  }

  function buildCol(comp) {
    var col = document.createElement('div');
    col.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:6px;';

    var wrap = document.createElement('div');
    switch (comp.type) {
      case 'led':     wrap.innerHTML = ledSVG(comp.id, comp.color || 'red'); break;
      case 'button':  wrap.innerHTML = buttonSVG(comp.id); break;
      case 'switch':  wrap.innerHTML = switchSVG(comp.id); break;
      case 'timer':   wrap.innerHTML = timerSVG(comp.id);  break;
      case 'servo': {
        wrap.innerHTML = servoSVG(comp.id);
        /* Angle readout — populated only by initInterpreted() from
           servo_angles/servo_sequences (SIM_ENGINE_ROLLOUT_SPEC.md item 6).
           A servo is output-only, same as an LED/buzzer — no input state
           for it in buildInputPayload(). */
        var angleReadout = document.createElement('div');
        angleReadout.id = comp.id + '-readout';
        angleReadout.style.cssText =
          'font-size:11px;font-weight:700;font-family:"Courier New",monospace;color:#f59e0b;';
        angleReadout.textContent = '90°';
        col.appendChild(wrap);
        col.appendChild(angleReadout);
        col.appendChild(makeLbl(comp));
        return col;
      }
      case 'buzzer': {
        wrap.innerHTML = buzzerSVG(comp.id);
        /* Pitch (Hz) readout — populated only by initInterpreted() when a
           result carries pin_frequencies (a continuous tone() pitch, e.g.
           map()'d from a sonar distance — see SIM_ENGINE_ROLLOUT_SPEC.md
           item 5). Empty/blank for every other mode and for buzzers that
           only ever get a plain on/off tone(). */
        var hzReadout = document.createElement('div');
        hzReadout.id = comp.id + '-hz';
        hzReadout.style.cssText =
          'font-size:10px;font-weight:700;font-family:"Courier New",monospace;' +
          'color:#00ff88;min-height:12px;';
        col.appendChild(wrap);
        col.appendChild(hzReadout);
        col.appendChild(makeLbl(comp));
        return col;
      }
      case 'sonar': {
        wrap.innerHTML = sonarSVG(comp.id);
        /* Distance readout + zone badge */
        var readoutDiv = document.createElement('div');
        readoutDiv.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:1px;margin-top:2px;';
        var distReadout = document.createElement('div');
        distReadout.id = comp.id + '-readout';
        distReadout.style.cssText = 'font-size:14px;font-weight:700;font-family:"Courier New",monospace;color:#00ff88;';
        distReadout.textContent = '80 cm';
        var zoneTag = document.createElement('div');
        zoneTag.id = comp.id + '-zone';
        zoneTag.style.cssText = 'font-size:9px;font-weight:700;letter-spacing:1px;color:#00ff88;';
        zoneTag.textContent = '🟢 SAFE';
        readoutDiv.appendChild(distReadout);
        readoutDiv.appendChild(zoneTag);
        /* Slider */
        var sliderWrap = document.createElement('div');
        sliderWrap.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:2px;margin-top:5px;';
        var sliderEl = document.createElement('input');
        sliderEl.type = 'range';
        sliderEl.id = comp.id + '-slider';
        sliderEl.min = '0';
        sliderEl.max = '100';
        sliderEl.value = '80';
        sliderEl.style.cssText = 'width:110px;cursor:pointer;accent-color:#00ff88;';
        var sliderHints = document.createElement('div');
        sliderHints.style.cssText = 'display:flex;justify-content:space-between;width:110px;font-size:8px;color:#475569;';
        sliderHints.innerHTML = '<span>0 cm</span><span>50</span><span>100 cm</span>';
        sliderWrap.appendChild(sliderEl);
        sliderWrap.appendChild(sliderHints);
        col.appendChild(wrap);
        col.appendChild(readoutDiv);
        col.appendChild(sliderWrap);
        col.appendChild(makeLbl(comp));
        return col;
      }
      default: return col;
    }

    col.appendChild(wrap);
    col.appendChild(makeLbl(comp));
    return col;
  }

  /* ── Main init ───────────────────────────────────────────────────────────── */
  function init(container, config) {
    /* Clean up any previous sim instance in this container */
    if (container._simCleanup) { container._simCleanup(); }

    var components = config.components || [];
    var behaviors  = config.behaviors  || [];

    /* Per-component state */
    var state = {};
    var colorMap = {};
    components.forEach(function (c) {
      state[c.id] = (c.type === 'switch') ? 'off'
                  : (c.type === 'button') ? 'released'
                  : (c.type === 'sonar')  ? 'safe'
                  : 'off';
      if (c.type === 'led') colorMap[c.id] = c.color || 'red';
    });

    /* Sequence + timer + beep handles */
    var seqHandle = null;
    var seqIds    = [];
    var seqIdx    = 0;
    var timerHandle  = null;
    var timerRunning = false;
    var timerStart   = 0;
    var beepHandle = null;
    var beepId     = null;

    /* ── Build UI ────────────────────────────────────────────────────────── */
    container.innerHTML = '';
    container.style.cssText =
      'background:#1a1a2e;border-radius:10px;padding:14px 12px 10px;' +
      'display:flex;flex-direction:column;align-items:center;gap:8px;';

    var canvas = document.createElement('div');
    canvas.style.cssText =
      'display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:center;';
    components.forEach(function (c) { canvas.appendChild(buildCol(c)); });
    container.appendChild(canvas);

    var statusBar = document.createElement('div');
    statusBar.style.cssText =
      'padding:5px 14px;background:rgba(255,255,255,0.04);' +
      'border:1px solid rgba(255,255,255,0.08);border-radius:6px;' +
      'color:#7ab;font-size:10px;font-family:"Courier New",monospace;' +
      'text-align:center;min-width:160px;max-width:100%;';
    statusBar.textContent = 'Ready';
    container.appendChild(statusBar);

    function setStatus(msg) { statusBar.textContent = msg; }

    /* ── Beep helpers ────────────────────────────────────────────────────── */
    function stopBeep() {
      if (beepHandle) { clearInterval(beepHandle); beepHandle = null; }
      if (beepId)     { applyBuzzer(beepId, false); beepId = null; }
    }

    function startBeep(id, interval) {
      if (beepHandle && beepId === id) return; /* already beeping this buzzer */
      stopBeep();
      beepId = id;
      var on = true;
      beepHandle = setInterval(function () {
        applyBuzzer(id, on);
        on = !on;
      }, interval || 400);
    }

    /* ── Sequence helpers ────────────────────────────────────────────────── */
    function stopSequence() {
      if (seqHandle) { clearInterval(seqHandle); seqHandle = null; }
    }

    function startSequence(ids, interval) {
      stopSequence();
      seqIds = ids;
      seqIdx = 0;
      /* Turn all sequence LEDs off first */
      ids.forEach(function (id) { applyState(id, 'off', false); });

      seqHandle = setInterval(function () {
        /* Turn off previous */
        var prev = seqIds[(seqIdx - 1 + seqIds.length) % seqIds.length];
        applyState(prev, 'off', false);
        /* Turn on current */
        var cur = seqIds[seqIdx % seqIds.length];
        applyState(cur, 'on', false);
        var comp = compById(cur);
        setStatus((comp ? comp.label : cur) + '  ON');
        seqIdx++;
      }, interval || 150);
    }

    /* ── Timer helpers ───────────────────────────────────────────────────── */
    function handleTimerToggle(timerId) {
      if (!timerRunning) {
        timerRunning = true;
        timerStart   = Date.now();
        timerHandle  = setInterval(function () {
          var el = document.getElementById(timerId + '-display');
          if (el) el.textContent = ((Date.now() - timerStart) / 1000).toFixed(3) + 's';
        }, 50);
        setStatus('Timer running — press again to stop!');
      } else {
        timerRunning = false;
        clearInterval(timerHandle);
        timerHandle = null;
        var elapsed = ((Date.now() - timerStart) / 1000).toFixed(3);
        var el = document.getElementById(timerId + '-display');
        if (el) el.textContent = elapsed + 's';
        setStatus('Reaction time: ' + elapsed + 's  ·  press to restart');
      }
    }

    /* ── Lookup helper ───────────────────────────────────────────────────── */
    function compById(id) {
      return components.find(function (c) { return c.id === id; });
    }

    /* ── Visual applier (does not re-evaluate behaviors) ─────────────────── */
    function applyState(id, newState, evaluate) {
      var changed = state[id] !== newState;
      state[id] = newState;
      var comp = compById(id);
      if (!comp) return;
      switch (comp.type) {
        case 'led':    applyLED(id, newState === 'on', colorMap[id]); break;
        case 'buzzer': applyBuzzer(id, newState === 'on'); break;
        case 'switch': applySwitch(id, newState === 'on'); break;
        case 'button': applyButton(id, newState === 'pressed'); break;
        case 'sonar':  applySonar(id, newState, comp.labels); break;
      }
      if (evaluate !== false && changed) evalBehaviors();
    }

    /* ── Behavior evaluation ─────────────────────────────────────────────── */
    function evalBehaviors() {
      behaviors.forEach(function (beh) {
        var match = Object.keys(beh.when).every(function (id) {
          return state[id] === beh.when[id];
        });
        if (!match) return;

        var then = beh.then;
        /* Handle special keys — order matters: stop before start */
        if (then._stop_sequence) { stopSequence(); }
        if (then._stop_beep)     { stopBeep(); }
        if (then._sequence) { startSequence(then._sequence, then._interval || 150); }
        if (then._beep)     { startBeep(then._beep, then._beep_interval || 400); }

        Object.keys(then).forEach(function (id) {
          if (id === '_sequence' || id === '_stop_sequence' || id === '_interval' ||
              id === '_beep'     || id === '_stop_beep'     || id === '_beep_interval') return;

          var val  = then[id];
          var comp = compById(id);
          if (comp && comp.type === 'timer' && val === 'toggle') {
            handleTimerToggle(id);
          } else {
            applyState(id, val, false); /* false = don't recurse */
          }
        });
      });
    }

    /* ── Pin label helper for status bar ─────────────────────────────────── */
    function pinDesc(comp, st) {
      if (!comp.pin && comp.pin !== 0) return '';
      var sig = (comp.type === 'button') ? (st === 'pressed' ? 'LOW (0V)' : 'HIGH (5V)')
              : (comp.type === 'switch') ? (st === 'on'      ? 'LOW (0V)' : 'HIGH (5V)')
              : '';
      return sig ? '  ·  Pin ' + comp.pin + ' → ' + sig : '';
    }

    /* ── Event binding ───────────────────────────────────────────────────── */
    components.forEach(function (comp) {
      var el = container.querySelector('[data-id="' + comp.id + '"]');
      if (!el) return;

      if (comp.type === 'button') {
        function press(e) {
          if (e.preventDefault) e.preventDefault();
          applyState(comp.id, 'pressed');
          setStatus('Button PRESSED' + pinDesc(comp, 'pressed'));
        }
        function release() {
          applyState(comp.id, 'released');
          setStatus('Button RELEASED' + pinDesc(comp, 'released'));
        }
        el.addEventListener('mousedown',  press);
        el.addEventListener('mouseup',    release);
        el.addEventListener('mouseleave', function () {
          if (state[comp.id] === 'pressed') release();
        });
        el.addEventListener('touchstart', press,   { passive: false });
        el.addEventListener('touchend',   release, { passive: false });
      }

      if (comp.type === 'switch') {
        el.addEventListener('click', function () {
          var next = state[comp.id] === 'on' ? 'off' : 'on';
          applyState(comp.id, next);
          setStatus('Switch ' + (next === 'on' ? 'ON' : 'OFF') + pinDesc(comp, next));
        });
      }

      if (comp.type === 'sonar') {
        var sliderEl = document.getElementById(comp.id + '-slider');
        if (sliderEl) {
          sliderEl.addEventListener('input', function () {
            var dist = parseInt(sliderEl.value, 10);
            var zone = dist > 50 ? 'safe' : dist > 20 ? 'warning' : 'danger';
            var readout = document.getElementById(comp.id + '-readout');
            if (readout) readout.textContent = dist + ' cm';
            sonarPingFlash(comp.id);
            applyState(comp.id, zone);
            var labels = comp.labels || SONAR_ZONE_LABELS;
            setStatus('Distance: ' + dist + ' cm  ·  ' + (labels[zone] || zone));
          });
        }
      }
    });

    /* ── Apply initial visual state + fire initial behaviors ─────────────── */
    components.forEach(function (c) { applyState(c.id, state[c.id], false); });
    evalBehaviors();

    /* ── Register cleanup for re-init ────────────────────────────────────── */
    container._simCleanup = function () {
      stopSequence();
      stopBeep();
      if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    };
  }

  /* ── Timeline playback (code-driven sim) ────────────────────────────────── */

  /**
   * initTimeline(container, result)
   * Plays back a pre-built timeline returned by /sim/run.
   *
   * result shape:
   *   { duration: <ms>, components: [{id, type, color, pin, label, timeline:[{t,state}]}] }
   *
   * After `duration` ms the animation loops automatically.
   */
  function initTimeline(container, result) {
    if (container._simCleanup) container._simCleanup();

    var components = result.components || [];
    var duration   = result.duration   || 0;
    var handles    = [];
    var loopHandle = null;

    /* Build UI — same chrome as the interactive sim */
    container.innerHTML = '';
    container.style.cssText =
      'background:#1a1a2e;border-radius:10px;padding:14px 12px 10px;' +
      'display:flex;flex-direction:column;align-items:center;gap:8px;';

    var canvas = document.createElement('div');
    canvas.style.cssText =
      'display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:center;';
    components.forEach(function (c) { canvas.appendChild(buildCol(c)); });
    container.appendChild(canvas);

    var statusBar = document.createElement('div');
    statusBar.style.cssText =
      'padding:5px 14px;background:rgba(255,255,255,0.04);' +
      'border:1px solid rgba(255,255,255,0.08);border-radius:6px;' +
      'color:#7ab;font-size:10px;font-family:"Courier New",monospace;' +
      'text-align:center;min-width:160px;max-width:100%;';
    statusBar.textContent = 'Simulating…';
    container.appendChild(statusBar);

    /* If every event in every timeline is at t=0 there is nothing to animate —
       the code has no delays so each LED is in a fixed steady state.
       Just apply the final state and stop — no loop, no flicker. */
    var hasTimedEvent = components.some(function (c) {
      return (c.timeline || []).some(function (e) { return e.t > 0; });
    });

    if (!hasTimedEvent) {
      components.forEach(function (c) {
        var tl   = c.timeline || [];
        var last = tl[tl.length - 1];
        if (!last) return;
        if (c.type === 'led') {
          var on = last.state === 'on';
          applyLED(c.id, on, c.color || 'red');
          var modeNote = (c.pin_mode === 'INPUT')
            ? '  \u2014 pinMode is INPUT, LED can\u2019t turn on!'
            : '';
          statusBar.textContent =
            (c.label || ('Pin ' + c.pin)) + '  \u2192  ' +
            (on ? 'always HIGH \u26a1' : 'always LOW \u00b7  (LED off)') + modeNote;
        }
      });
      return;
    }

    /* Minimum loop delay prevents tight-spin when all delays are very short */
    var loopDelay = Math.max(duration, 300);

    function clearHandles() {
      handles.forEach(clearTimeout);
      handles = [];
      if (loopHandle) { clearTimeout(loopHandle); loopHandle = null; }
    }

    function playOnce() {
      clearHandles();

      components.forEach(function (c) {
        var tl = c.timeline || [];

        /* Apply ALL t=0 events synchronously — no deferred callbacks at t=0.
           This means the browser never renders an intermediate t=0 state,
           eliminating the flicker on loop restart. */
        var firstTimed = -1;
        for (var i = 0; i < tl.length; i++) {
          if (tl[i].t === 0) {
            if (c.type === 'led') applyLED(c.id, tl[i].state === 'on', c.color || 'red');
          } else {
            firstTimed = i;
            break;
          }
        }

        /* Schedule only t>0 events */
        if (firstTimed === -1) return;
        for (var j = firstTimed; j < tl.length; j++) {
          (function (event) {
            var h = setTimeout(function () {
              if (c.type === 'led') {
                var on = event.state === 'on';
                applyLED(c.id, on, c.color || 'red');
                statusBar.textContent =
                  (c.label || ('Pin ' + c.pin)) + '  \u2192  ' + (on ? 'HIGH \u26a1' : 'LOW \u00b7');
              }
            }, event.t);
            handles.push(h);
          }(tl[j]));
        }
      });

      loopHandle = setTimeout(playOnce, loopDelay);
    }

    playOnce();

    container._simCleanup = function () { clearHandles(); };
  }

  /**
   * initCodeDriven(container, simConfig)
   * Fetches the current sketch from the block builder, posts it to /sim/run,
   * then hands off to initTimeline.  Adds a Re-run button so the student can
   * refresh the sim after editing their code.
   */
  function initCodeDriven(container, simConfig) {
    if (container._simCleanup) container._simCleanup();

    /* Show a loading state while we wait for the server */
    container.innerHTML = '';
    container.style.cssText =
      'background:#1a1a2e;border-radius:10px;padding:18px 14px;' +
      'display:flex;flex-direction:column;align-items:center;gap:8px;';
    var loading = document.createElement('div');
    loading.style.cssText =
      'color:#7ab;font-size:12px;font-family:"Courier New",monospace;letter-spacing:0.5px;';
    loading.textContent = 'Analysing your code\u2026';
    container.appendChild(loading);

    var sketch = (window.getCurrentSketch ? window.getCurrentSketch() :
      (window.getGeneratedCode ? window.getGeneratedCode() : '')) || '';
    activeRequestId++;
    var thisRequestId = activeRequestId;

    fetch(simConfig.endpoint || '/sim/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sketch: sketch, sim_config: simConfig }),
    })
      .then(function (r) { return r.json(); })
      .then(function (result) {
        if (thisRequestId !== activeRequestId) return; // Skip if a newer request was started
        if (result.error) {
          container.innerHTML = '';
          container.style.cssText =
            'background:#1a1a2e;border-radius:10px;padding:16px 14px;' +
            'display:flex;flex-direction:column;align-items:center;gap:8px;';
          var errMsg = document.createElement('div');
          errMsg.style.cssText = 'color:#f87171;font-size:12px;padding:12px;text-align:center;';
          errMsg.textContent = 'Could not run simulation: ' + result.error;
          container.appendChild(errMsg);
          _appendRerunButton(container, simConfig);
          return;
        }
        initTimeline(container, result);
        _appendRerunButton(container, simConfig);
      })
      .catch(function () {
        container.innerHTML = '';
        container.style.cssText =
          'background:#1a1a2e;border-radius:10px;padding:16px 14px;' +
          'display:flex;flex-direction:column;align-items:center;gap:8px;';
        var errMsg = document.createElement('div');
        errMsg.style.cssText = 'color:#f87171;font-size:12px;padding:12px;text-align:center;';
        errMsg.textContent = 'Simulation error — check your code and try again.';
        container.appendChild(errMsg);
        _appendRerunButton(container, simConfig);
      });
  }

  /**
   * initInterpreted(container, simConfig)
   *
   * Interactive sim, but "interactive" here means every click/toggle POSTs
   * the current input component state to /sim/run (mode: "interpreted"),
   * which runs the real Phase 0 interpreter (utils/sim_engine.py::interpret)
   * against the student's live sketch and returns the resulting output pin
   * states. Unlike initCodeDriven's timeline, this is a discrete
   * request/response per interaction — see SIM_ENGINE_ROLLOUT_SPEC.md's
   * "Target architecture" section. Unlike init()'s `behaviors` DSL, nothing
   * here is hand-authored — output state always reflects whatever the
   * sketch's if/else actually does, including edits the student just made.
   *
   * simConfig shape: same `components` array as init() (button/switch inputs
   * need a `pin`; led/buzzer outputs need a `pin`). No `behaviors` key is
   * read — the sketch is the only source of truth.
   *
   * Input pin values are derived from each pin's pinMode as reported by the
   * server (INPUT_PULLUP: idle=HIGH/1, active=LOW/0; otherwise idle=LOW/0,
   * active=HIGH/1), not hardcoded — a seed request with an empty input_state
   * runs first to learn pin_modes from the sketch before any click is sent.
   *
   * If a result includes `pin_sequences` (a branch paced itself with its own
   * delay() calls — e.g. an LED chase), those pins are looped client-side
   * (setTimeout chain, same shared-restart pattern initTimeline uses for
   * code_driven tabs) instead of set once, repeating every
   * `sequence_duration` ms until the next real input event tears the loop
   * down and applies whatever the new result says instead.
   *
   * Phase 1 (SIM_ENGINE_ROLLOUT_SPEC.md item 4) — persistent state & a real
   * clock: the server's `_state` (globals + pin_modes + clock epoch) is
   * cached here in `persistState` and sent back as `state` on every
   * following call, so a sketch's own `running`/`startTime`-style globals
   * and millis()/micros() survive across separate button presses instead of
   * resetting every request — see utils/sim_engine.py's module docstring.
   * `persistState` is reset to null (a fresh "power-on") whenever the
   * sketch text itself changes between calls, mirroring a real re-upload;
   * without that, editing in a *new* global after state has already been
   * captured would hit "Unknown identifier" (globals only initialise on the
   * first call for a given state) — same failure mode `interpret()` already
   * reports clearly for any other unsupported edit.
   *
   * `console_lines`, if present, is a list of this pass's Serial.print/
   * println args (str()'d) — surfaced as the last line appended to the
   * status bar text. Not the dedicated scrolling console component the
   * rollout spec describes for `five`/`six` — just enough to show a printed
   * value (e.g. a computed reaction time) for sketches that only output text.
   *
   * Phase 2 (SIM_ENGINE_ROLLOUT_SPEC.md item 5) — continuous mapping: a
   * `sonar` component (`pin_trig`/`pin_echo`, same shape `project_seventeen`
   * already shipped for the now-removed hand-authored `behaviors`) sends its
   * slider distance as a raw pulse duration on `pin_echo` — debounced 150ms
   * after the last drag movement, not one request per pixel — and a
   * `pin_frequencies` key in the result (a `tone()` call's actual Hz
   * argument, not collapsed to on/off) paints a live Hz readout under any
   * `buzzer` component via `applyBuzzerFreq()`. There are no discrete zones
   * here on either end — whatever the sketch's own map()/if-chain computes
   * is what's shown, continuously.
   */
  function initInterpreted(container, config) {
    if (container._simCleanup) container._simCleanup();

    var components  = config.components || [];
    var inputState   = {};   // per-component raw UI state: 'pressed'/'released'/'on'/'off'
    var pinModes    = {};   // filled in from the server's reading of the sketch's pinMode() calls
    var colorMap    = {};
    var activeId    = 0;
    var seqHandles  = [];   // pending setTimeout ids for the current pin_sequences playback
    var seqLoopHandle = null;
    var persistState = null;   // Phase 1: opaque server _state, round-tripped between calls
    var lastSketch   = null;   // sketch text as of the last call — a change means "re-upload"

    components.forEach(function (c) {
      inputState[c.id] = (c.type === 'switch') ? 'off'
                        : (c.type === 'button') ? 'released'
                        : (c.type === 'sonar')  ? 80   /* cm, matches buildCol's default slider value */
                        : 'off';
      if (c.type === 'led') colorMap[c.id] = c.color || 'red';
    });

    container.innerHTML = '';
    container.style.cssText =
      'background:#1a1a2e;border-radius:10px;padding:14px 12px 10px;' +
      'display:flex;flex-direction:column;align-items:center;gap:8px;';

    var canvas = document.createElement('div');
    canvas.style.cssText =
      'display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:center;';
    components.forEach(function (c) { canvas.appendChild(buildCol(c)); });
    container.appendChild(canvas);

    /* The zone badge under a sonar component (buildCol's `-zone` element,
       "🟢 SAFE" etc.) belongs to init()'s hand-authored 3-zone `behaviors`
       model. There are no zones here — the sketch's own map()/if-chain is
       the only source of truth for what a given distance means (see
       SIM_ENGINE_ROLLOUT_SPEC.md item 5) — so it's hidden rather than left
       showing a label nothing here ever updates. */
    components.forEach(function (c) {
      if (c.type !== 'sonar') return;
      var zoneTag = document.getElementById(c.id + '-zone');
      if (zoneTag) zoneTag.style.display = 'none';
    });

    var statusBar = document.createElement('div');
    statusBar.style.cssText =
      'padding:5px 14px;background:rgba(255,255,255,0.04);' +
      'border:1px solid rgba(255,255,255,0.08);border-radius:6px;' +
      'color:#7ab;font-size:10px;font-family:"Courier New",monospace;' +
      'text-align:center;min-width:160px;max-width:100%;';
    statusBar.textContent = 'Loading…';
    container.appendChild(statusBar);

    function setStatus(msg) { statusBar.textContent = msg; }

    /* pin value an INPUT-type component should report, given what the
       sketch's own pinMode() declared for that pin (learned from the seed
       request — see module-level doc comment above). */
    function pinValueFor(comp) {
      var active = (inputState[comp.id] === 'pressed' || inputState[comp.id] === 'on');
      var isPullup = pinModes[comp.pin] === 'INPUT_PULLUP';
      if (isPullup) return active ? 0 : 1;
      return active ? 1 : 0;
    }

    /* HC-SR04 sonar reports distance as a round-trip pulse *duration*
       (microseconds), not a distance — same physical signal a real sensor
       puts on its echo pin, which the sketch's own pulseIn()/math (e.g.
       `distance = duration * 0.034 / 2`) turns back into cm. 0.034 cm/us is
       the same speed-of-sound constant every sonar sketch in this repo
       uses, so this is the sensor's own physics, not a copy of any one
       sketch's logic — mirrors how pinValueFor() supplies a raw HIGH/LOW
       level rather than a pre-interpreted "pressed" state. */
    function sonarDurationUs(distanceCm) {
      return Math.round(distanceCm * 2 / 0.034);
    }

    function buildInputPayload() {
      var payload = {};
      components.forEach(function (c) {
        if ((c.type === 'button' || c.type === 'switch') && c.pin !== undefined && c.pin !== '') {
          payload[c.pin] = pinValueFor(c);
        }
        if (c.type === 'sonar' && c.pin_echo !== undefined && c.pin_echo !== '') {
          payload[c.pin_echo] = sonarDurationUs(inputState[c.id]);
        }
      });
      return payload;
    }

    /* Cancels any currently-looping pin_sequences playback — called before
       applying a fresh result (new input event) and on cleanup. */
    function clearSequencePlayback() {
      seqHandles.forEach(clearTimeout);
      seqHandles = [];
      if (seqLoopHandle) { clearTimeout(seqLoopHandle); seqLoopHandle = null; }
    }

    /* Loops a {pin: [{t, state}, ...]} timeline (LED/buzzer) and/or a
       {pin: [{t, angle}, ...]} timeline (servo) client-side — same
       setTimeout-chain / self-rescheduling pattern initTimeline uses for
       code_driven tabs — until clearSequencePlayback() cancels it (the next
       real input event replaces the whole result, sequence or not). Servo
       sequences are a separate angle-valued channel from pin_sequences'
       binary HIGH/LOW one (see SIM_ENGINE_ROLLOUT_SPEC.md item 6), so both
       are looped on the same schedule but read from different result keys. */
    function playSequences(sequences, servoSequences, duration) {
      var loopDelay = Math.max(duration, 300);
      function apply(comp, state) {
        if (comp.type === 'led')    applyLED(comp.id, state === 'HIGH', colorMap[comp.id]);
        if (comp.type === 'buzzer') applyBuzzer(comp.id, state === 'HIGH');
      }
      function playOnce() {
        components.forEach(function (c) {
          if (c.pin === undefined || c.pin === '') return;
          var tl = sequences[c.pin];
          if (tl) {
            tl.forEach(function (ev) {
              if (ev.t === 0) {
                apply(c, ev.state);
              } else {
                seqHandles.push(setTimeout(function () { apply(c, ev.state); }, ev.t));
              }
            });
          }
          var stl = servoSequences[c.pin];
          if (stl) {
            stl.forEach(function (ev) {
              if (ev.t === 0) {
                applyServo(c.id, ev.angle);
              } else {
                seqHandles.push(setTimeout(function () { applyServo(c.id, ev.angle); }, ev.t));
              }
            });
          }
        });
        seqLoopHandle = setTimeout(playOnce, loopDelay);
      }
      playOnce();
    }

    function applyOutputs(result) {
      pinModes = result.pin_modes || pinModes;
      var states          = result.pin_states       || {};
      var sequences       = result.pin_sequences     || {};
      var frequencies     = result.pin_frequencies   || {};
      var servoAngles     = result.servo_angles      || {};
      var servoSequences  = result.servo_sequences   || {};
      clearSequencePlayback();
      components.forEach(function (c) {
        if (c.pin === undefined || c.pin === '') return;
        if (sequences[c.pin] || servoSequences[c.pin]) return; /* driven by playSequences below instead */
        if (c.type === 'led')    applyLED(c.id, states[c.pin] === 'HIGH', colorMap[c.id]);
        if (c.type === 'buzzer') {
          applyBuzzer(c.id, states[c.pin] === 'HIGH');
          applyBuzzerFreq(c.id, frequencies[c.pin]);
        }
        /* Absent (no .write() call happened this pass — e.g. the button's
           if-branch didn't run) means "leave the dial where it already is",
           not "reset to some default" — same as an LED with no pin_states
           entry implicitly staying at its last-painted state. */
        if (c.type === 'servo' && servoAngles[c.pin] !== undefined) {
          applyServo(c.id, servoAngles[c.pin]);
        }
      });
      if (Object.keys(sequences).length || Object.keys(servoSequences).length) {
        playSequences(sequences, servoSequences, result.sequence_duration || 0);
      }
    }

    /* seedInputPayload is {} on the very first call (before pin_modes are
       known) so the interpreter's own idle defaults apply; every call after
       that sends every input pin's live value, which — now that pin_modes
       are known — agrees with those same idle defaults when nothing is
       pressed, so there's no state jump once real payloads take over. */
    function run(inputPayload, statusMsg) {
      var sketch = (window.getCurrentSketch ? window.getCurrentSketch() :
        (window.getGeneratedCode ? window.getGeneratedCode() : '')) || '';
      if (sketch !== lastSketch) persistState = null;  // edited code = a fresh power-on
      lastSketch = sketch;
      activeId++;
      var thisId = activeId;

      fetch(config.endpoint || '/sim/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sketch: sketch, sim_config: config, input_state: inputPayload, state: persistState,
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (result) {
          if (thisId !== activeId) return;
          if (result.error) { setStatus('Could not run: ' + result.error); return; }
          persistState = result._state || null;
          applyOutputs(result);
          var msg = statusMsg || 'Ready';
          if (result.console_lines && result.console_lines.length) {
            msg += '  ·  ' + result.console_lines[result.console_lines.length - 1];
          }
          setStatus(msg);
        })
        .catch(function () {
          if (thisId !== activeId) return;
          setStatus('Simulation error — check your code and try again.');
        });
    }

    /* ── Event binding — same physical interactions as init(), but every
       one triggers a live server re-evaluation instead of local rule
       matching ─────────────────────────────────────────────────────────── */
    components.forEach(function (comp) {
      var el = container.querySelector('[data-id="' + comp.id + '"]');
      if (!el) return;

      if (comp.type === 'button') {
        function press(e) {
          if (e.preventDefault) e.preventDefault();
          inputState[comp.id] = 'pressed';
          applyButton(comp.id, true);
          run(buildInputPayload(), 'Button PRESSED');
        }
        function release() {
          inputState[comp.id] = 'released';
          applyButton(comp.id, false);
          run(buildInputPayload(), 'Button RELEASED');
        }
        el.addEventListener('mousedown',  press);
        el.addEventListener('mouseup',    release);
        el.addEventListener('mouseleave', function () {
          if (inputState[comp.id] === 'pressed') release();
        });
        el.addEventListener('touchstart', press,   { passive: false });
        el.addEventListener('touchend',   release, { passive: false });
      }

      if (comp.type === 'switch') {
        el.addEventListener('click', function () {
          var next = inputState[comp.id] === 'on' ? 'off' : 'on';
          inputState[comp.id] = next;
          applySwitch(comp.id, next === 'on');
          run(buildInputPayload(), 'Switch ' + (next === 'on' ? 'ON' : 'OFF'));
        });
      }

      if (comp.type === 'sonar') {
        var sliderEl = document.getElementById(comp.id + '-slider');
        var debounceHandle = null;
        if (sliderEl) {
          sliderEl.addEventListener('input', function () {
            var dist = parseInt(sliderEl.value, 10);
            inputState[comp.id] = dist;
            var readout = document.getElementById(comp.id + '-readout');
            if (readout) readout.textContent = dist + ' cm';
            sonarPingFlash(comp.id);
            /* Debounced, not per-pixel-of-drag — see the "Target
               architecture" section of SIM_ENGINE_ROLLOUT_SPEC.md: a
               discrete-request server round trip per drag pixel would flood
               /sim/run, unlike button/switch clicks which are naturally
               low-frequency. */
            if (debounceHandle) clearTimeout(debounceHandle);
            debounceHandle = setTimeout(function () {
              run(buildInputPayload(), 'Distance: ' + dist + ' cm');
            }, 150);
          });
        }
      }
    });

    /* Initial idle visuals for inputs, then the seed request (see run()'s
       doc comment) to learn pin_modes and paint the sketch's real idle
       output state. */
    components.forEach(function (c) {
      if (c.type === 'button') applyButton(c.id, false);
      if (c.type === 'switch') applySwitch(c.id, false);
    });
    run({}, 'Ready');

    container._simCleanup = function () { activeId++; clearSequencePlayback(); };
  }

  function _appendRerunButton(container, simConfig) {
    var blurb = document.createElement('div');
    blurb.textContent = 'Changed your code? Click the button to run it and see what happens.';
    blurb.style.cssText =
      'margin-top:6px;color:#9db4d1;font-size:11px;text-align:center;' +
      'font-family:"Courier New",monospace;letter-spacing:0.2px;max-width:260px;';
    container.appendChild(blurb);

    var btn = document.createElement('button');
    btn.textContent = '\u25b6 RUN YOUR CODE';
    btn.style.cssText =
      'margin-top:8px;padding:12px 28px;background:#22c55e;color:#052e13;' +
      'border:none;border-radius:8px;font-size:14px;font-weight:800;' +
      'letter-spacing:0.5px;cursor:pointer;font-family:"Courier New",monospace;' +
      'box-shadow:0 3px 0 #15803d,0 4px 12px rgba(34,197,94,0.4);transition:transform 0.1s;';
    btn.onmouseover = function () { btn.style.background = '#34d465'; };
    btn.onmouseout  = function () { btn.style.background = '#22c55e'; };
    btn.onmousedown = function () { btn.style.transform = 'translateY(2px)'; btn.style.boxShadow = '0 1px 0 #15803d,0 2px 6px rgba(34,197,94,0.4)'; };
    btn.onmouseup   = function () { btn.style.transform = 'translateY(0)'; btn.style.boxShadow = '0 3px 0 #15803d,0 4px 12px rgba(34,197,94,0.4)'; };
    btn.onclick = function () { initCodeDriven(container, simConfig); };
    container.appendChild(btn);
  }

  return {
    init: init,
    initTimeline: initTimeline,
    initCodeDriven: initCodeDriven,
    initInterpreted: initInterpreted,
  };
}());
