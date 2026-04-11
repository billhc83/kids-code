/**
 * SimEngine — interactive Arduino circuit simulator for the drawer sim tab.
 * Usage: SimEngine.init(containerElement, simConfig)
 *
 * simConfig shape:
 *   components: [{type, id, color?, pin?, label}]
 *   behaviors:  [{when: {id: state, ...}, then: {id: state, ...}}]
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
 *   timer — shows a running millisecond counter; toggled via {timerId: "toggle"}
 *   sonar — HC-SR04 ultrasonic sensor with a distance slider (0-100 cm);
 *            state emitted: "safe" (>50 cm), "warning" (20-50 cm), "danger" (<20 cm)
 */
window.SimEngine = (function () {
  'use strict';

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

  function applySonar(id, zone) {
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
    if (zoneTag) { zoneTag.textContent = SONAR_ZONE_LABELS[zone] || zone; zoneTag.style.color = color; }
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
      case 'buzzer':  wrap.innerHTML = buzzerSVG(comp.id); break;
      case 'timer':   wrap.innerHTML = timerSVG(comp.id);  break;
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
      'background:#1a1a2e;border-radius:12px;padding:24px 16px 16px;' +
      'display:flex;flex-direction:column;align-items:center;gap:14px;';

    var canvas = document.createElement('div');
    canvas.style.cssText =
      'display:flex;flex-wrap:wrap;gap:28px;align-items:flex-end;justify-content:center;';
    components.forEach(function (c) { canvas.appendChild(buildCol(c)); });
    container.appendChild(canvas);

    var statusBar = document.createElement('div');
    statusBar.style.cssText =
      'padding:7px 20px;background:rgba(255,255,255,0.04);' +
      'border:1px solid rgba(255,255,255,0.08);border-radius:6px;' +
      'color:#7ab;font-size:11px;font-family:"Courier New",monospace;' +
      'text-align:center;min-width:220px;max-width:100%;';
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
      state[id] = newState;
      var comp = compById(id);
      if (!comp) return;
      switch (comp.type) {
        case 'led':    applyLED(id, newState === 'on', colorMap[id]); break;
        case 'buzzer': applyBuzzer(id, newState === 'on'); break;
        case 'switch': applySwitch(id, newState === 'on'); break;
        case 'button': applyButton(id, newState === 'pressed'); break;
        case 'sonar':  applySonar(id, newState); break;
      }
      if (evaluate !== false) evalBehaviors();
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
            setStatus('Distance: ' + dist + ' cm  ·  ' + (SONAR_ZONE_LABELS[zone] || zone));
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

  return { init: init };
}());
