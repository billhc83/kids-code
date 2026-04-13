// bb-blocks.js — Block definitions, pin constants, expression utilities, and data helpers
// Must be loaded FIRST. Creates window._BB shared namespace used by all other BB modules.
(function () {
  ('[DEBUG] bb-blocks.js: start');

  // ── Shared state namespace ────────────────────────────────────────────────
  window._BB = {
    SECTIONS: { global: [], setup: [], loop: [] },
    sel: null,
    exprSel: null,
    activePhantoml: null,
    PROGRESSION_MODE: false,
    STEPS: null,
    CURRENT_STEP: 0,
    STUDENT_SAVES: [],
    CHECK_FAIL_COUNT: 0,
    SKETCH_ERROR_PATHS: [],
    STEP_ERROR_IDS: [],
    PALETTE_ALLOWED: null,
    nextBtnState: { ready: false, mode: '', text: 'Complete Step', visible: false, prevVisible: false },
    stepLabel: 'Step',
    stepProgress: '',
    // Config fields — populated by block_builder.js after CFG is read
    USERNAME: null,
    PAGE: null,
    MASTER_SKETCH: null,
    SUPABASE_URL: null,
    SUPABASE_KEY: null,
    DEFAULT_VIEW: null,
    LOCK_VIEW: null,
    READONLY_MODE: null,
    LOCK_MODE: null,
  };

  var BB = window._BB;

  // ── Hardware constants ────────────────────────────────────────────────────
  BB.UNO_DIGITAL_PINS    = ['0','1','2','3','4','5','6','7','8','9','10','11','12','13'];
  BB.UNO_ANALOG_PINS     = ['A0','A1','A2','A3','A4','A5'];
  BB.UNO_DIGITAL_IO_PINS = BB.UNO_DIGITAL_PINS.concat(BB.UNO_ANALOG_PINS);
  BB.UNO_PWM_PINS        = ['3','5','6','9','10','11'];

  BB.EXPR_COLORS = {
    'analogread': '#1a7f37', 'digitalread': '#1a7f37', 'pulsein': '#1a7f37', 'millis': '#0969da',
    'random': '#e36209', 'math': '#9a6700', 'map': '#6f42c1', 'constrain': '#cf222e', 'value': '#57606a'
  };

  // ── genExpr — defined before BLOCKS so BLOCKS.genStmt functions can close over it ──
  function genExpr(exNode, fallbackParam, fallbackDefault) {
    if (exNode && exNode.type) {
      var def = BB.BLOCKS[exNode.type];
      if (!def || !def.genExpr) return String(fallbackParam || fallbackDefault || '0');
      return def.genExpr(exNode.params || [], exNode.children || []);
    }
    var v = fallbackParam; if (v === '' || v === null || v === undefined) v = fallbackDefault || '0';
    return String(v);
  }

  // ── Block definitions ─────────────────────────────────────────────────────
  BB.BLOCKS = {
    intvar: {
      allowed: ['global', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'text', l: 'Name' }, { t: 'expr', l: 'Value', fallback: '0' }],
      defaults: [null, { type: 'value', params: ['0'], children: [] }],
      genStmt: function (p, ex) { return 'int ' + (p[0] || 'myVar') + ' = ' + genExpr(ex && ex[1], p[1], '0') + ';'; }
    },
    longvar: {
      allowed: ['global', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'text', l: 'Name' }, { t: 'expr', l: 'Value', fallback: '0' }],
      defaults: [null, { type: 'value', params: ['0'], children: [] }],
      genStmt: function (p, ex) { return 'long ' + (p[0] || 'myLong') + ' = ' + genExpr(ex && ex[1], p[1], '0') + ';'; }
    },
    boolvar: {
      allowed: ['global', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'text', l: 'Name' }, { t: 'sel', l: 'Value', o: ['true', 'false'] }],
      genStmt: function (p) { return 'bool ' + (p[0] || 'myFlag') + ' = ' + (p[1] || 'false') + ';'; }
    },
    setvar: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'vartext', l: 'Var' }, { t: 'expr', l: 'Value', fallback: '0' }],
      defaults: [null, { type: 'value', params: ['0'], children: [] }],
      genStmt: function (p, ex) { return (p[0] || 'myVar') + ' = ' + genExpr(ex && ex[1], p[1], '0') + ';'; }
    },
    increment: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'vartext', l: 'Var' }, { t: 'sel', l: 'Op', o: ['++', '--', '+=', '-='] }, { t: 'number', l: 'By' }],
      genStmt: function (p) {
        var v = p[0] || 'myVar', op = p[1] || '++', n = p[2] || '1';
        if (op === '++' || op === '--') return v + op + ';';
        return v + ' ' + op + ' ' + n + ';';
      }
    },
    stringvar: {
      allowed: ['global', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'text', l: 'Name' }, { t: 'expr', l: 'Value', fallback: '""' }],
      defaults: [null, { type: 'value', params: [''], children: [] }],
      genStmt: function (p, ex) { return 'String ' + (p[0] || 'myText') + ' = ' + genExpr(ex && ex[1], p[1], '""') + ';'; }
    },
    pinmode: {
      allowed: ['setup'], asStatement: true, asExpr: false,
      inputs: [{ t: 'vartext', l: 'Pin', o: 'DIGITAL_PIN_OPTIONS' }, { t: 'sel', l: 'Mode', o: ['OUTPUT', 'INPUT', 'INPUT_PULLUP'] }],
      genStmt: function (p) { return 'pinMode(' + (p[0]) + ', ' + (p[1]) + ');'; }
    },
    digitalwrite: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'vartext', l: 'Pin', o: 'DIGITAL_PIN_OPTIONS' }, { t: 'sel', l: 'Value', o: ['HIGH', 'LOW'] }],
      genStmt: function (p) { return 'digitalWrite(' + (p[0]) + ', ' + (p[1]) + ');'; }
    },
    analogwrite: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'sel', l: 'Pin', o: 'PWM_PIN_OPTIONS' }, { t: 'expr', l: 'Value', fallback: '128' }],
      genStmt: function (p, ex) { return 'analogWrite(' + (p[0] || 9) + ', ' + genExpr(ex && ex[1], p[1], '128') + ');'; }
    },
    analogread: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: false, asExpr: true,
      inputs: [{ t: 'sel', l: 'Pin', o: 'ANALOG_PIN_OPTIONS' }],
      genExpr: function (p) { return 'analogRead(' + (p[0] || 'A0') + ')'; }
    },
    digitalread: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: false, asExpr: true,
      inputs: [{ t: 'sel', l: 'Pin', o: 'DIGITAL_PIN_OPTIONS' }],
      genExpr: function (p) { return 'digitalRead(' + (p[0] || '2') + ')'; }
    },
    pulsein: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: false, asExpr: true,
      inputs: [{ t: 'vartext', l: 'Pin' }, { t: 'sel', l: 'Value', o: ['HIGH', 'LOW'] }],
      genExpr: function (p) { return 'pulseIn(' + (p[0] || 'echoPin') + ', ' + (p[1] || 'HIGH') + ')'; }
    },
    delay: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'expr', l: 'ms', fallback: '1000' }],
      genStmt: function (p, ex) { return 'delay(' + genExpr(ex && ex[0], p[0], '1000') + ');'; }
    },
    delaymicroseconds: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'expr', l: 'us', fallback: '100' }],
      defaults: [{ type: 'value', params: ['100'], children: [] }],
      genStmt: function (p, ex) { return 'delayMicroseconds(' + genExpr(ex && ex[0], p[0], '100') + ');'; }
    },
    millis: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: false, asExpr: true,
      inputs: [],
      genExpr: function (p) { return 'millis()'; }
    },
    tone: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'vartext', l: 'Pin', o: 'DIGITAL_PIN_OPTIONS' }, { t: 'expr', l: 'Freq', fallback: '440' }, { t: 'number', l: 'Duration' }],
      genStmt: function (p, ex) {
        var pin = (p[0] || 5), f = genExpr(ex && ex[1], p[1], '440'), d = p[2];
        return (d !== '' && d !== null && d !== undefined) ? ('tone(' + pin + ', ' + f + ', ' + d + ');') : ('tone(' + pin + ', ' + f + ');');
      }
    },
    notone: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'expr', l: 'Pin', fallback: '0' }],
      genStmt: function (p, ex) { return 'noTone(' + genExpr(ex && ex[0], p[0], '0') + ');'; }
    },
    random: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: false, asExpr: true,
      inputs: [{ t: 'number', l: 'Min' }, { t: 'number', l: 'Max' }],
      genExpr: function (p) { return 'random(' + (p[0] || 0) + ', ' + (p[1] || 100) + ')'; }
    },
    math: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [{ t: 'expr', l: 'A', fallback: '0' }, { t: 'sel', l: 'Op', o: [{ v: '+', lb: 'plus' }, { v: '-', lb: 'minus' }, { v: '*', lb: 'multiply' }, { v: '/', lb: 'divide' }, { v: '%', lb: 'modulo' }] }, { t: 'expr', l: 'B', fallback: '0' }],
      genExpr: function (p, ch) {
        var a = genExpr(ch && ch[0], p[0], '0'), op = p[1] || '+', b = genExpr(ch && ch[2], p[2], '0');
        return '(' + a + ' ' + op + ' ' + b + ')';
      }
    },
    map: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [{ t: 'expr', l: 'Val', fallback: '0' }, { t: 'number', l: 'inLo' }, { t: 'number', l: 'inHi' }, { t: 'number', l: 'outLo' }, { t: 'number', l: 'outHi' }],
      genExpr: function (p, ch) {
        var v = genExpr(ch && ch[0], p[0], '0');
        return 'map(' + v + ', ' + (p[1] || 0) + ', ' + (p[2] || 1023) + ', ' + (p[3] || 0) + ', ' + (p[4] || 255) + ')';
      }
    },
    constrain: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [{ t: 'expr', l: 'Val', fallback: '0' }, { t: 'number', l: 'Lo' }, { t: 'number', l: 'Hi' }],
      genExpr: function (p, ch) {
        var v = genExpr(ch && ch[0], p[0], '0');
        return 'constrain(' + v + ', ' + (p[1] || 0) + ', ' + (p[2] || 255) + ')';
      }
    },
    value: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [{ t: 'vartext', l: 'Value' }],
      genExpr: function (p) { return (p[0] || '0'); }
    },
    serialbegin: {
      allowed: ['setup'], asStatement: true, asExpr: false,
      inputs: [{ t: 'sel', l: 'Baud', o: ['9600', '19200', '38400', '57600', '115200'] }],
      genStmt: function (p) { return 'Serial.begin(' + (p[0] || '9600') + ');'; }
    },
    serialprint: {
      allowed: ['setup', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'expr', l: 'Value', fallback: '"Hello"' }, { t: 'sel', l: 'Mode', o: ['println', 'print'] }],
      defaults: [{ type: 'value', params: ['"Hello"'], children: [] }, null],
      genStmt: function (p, ex) {
        var fn = p[1] === 'print' ? 'Serial.print' : 'Serial.println';
        return fn + '(' + genExpr(ex && ex[0], null, '"Hello"') + ');';
      }
    },
    serialreadstring: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [],
      genExpr: function (p) { return 'Serial.readString()'; }
    },
    serialavailable: {
      allowed: [], asStatement: false, asExpr: true,
      inputs: [],
      genExpr: function (p) { return 'Serial.available()'; }
    },
    codeblock: {
      allowed: ['global', 'setup', 'loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [{ t: 'text', l: 'Code' }],
      genStmt: function (p) { return (p[0] || ''); }
    },
    ifblock: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [], genStmt: function () { return ''; }
    },
    elseifclause: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [], genStmt: function () { return ''; }
    },
    elseclause: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [], genStmt: function () { return ''; }
    },
    forloop: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [], genStmt: function () { return ''; }
    },
    whileloop: {
      allowed: ['loop', 'if', 'for', 'while'], asStatement: true, asExpr: false,
      inputs: [], genStmt: function () { return ''; }
    },
  };
  BB.B = BB.BLOCKS;
  BB.genExpr = genExpr;

  // ── Expression utilities ──────────────────────────────────────────────────
  BB.getExprColor = function (type) { return BB.EXPR_COLORS[type] || '#57606a'; };

  BB.makeExNode = function (type) {
    var def = BB.BLOCKS[type]; if (!def || !def.asExpr) return null;
    var params = def.inputs.map(function (inp) {
      if (inp.t === 'sel') { var f = inp.o[0]; return typeof f === 'object' ? f.v : f; }
      if (inp.t === 'number') return '0'; if (inp.t === 'expr') return '';
      if (inp.t === 'vartext') return '0'; return '';
    });
    var children = def.inputs.map(function (inp) { return inp.t === 'expr' ? null : undefined; });
    return { type: type, params: params, children: children };
  };

  // ── Option / suggestion helpers ───────────────────────────────────────────
  BB.getOptions = function (key) {
    var base;
    if (key === 'DIGITAL_PIN_OPTIONS') { base = BB.UNO_DIGITAL_IO_PINS; }
    else if (key === 'PWM_PIN_OPTIONS') { base = BB.UNO_PWM_PINS; }
    else if (key === 'ANALOG_PIN_OPTIONS') { base = BB.UNO_ANALOG_PINS; }
    else { return []; }
    var opts = base.slice();
    BB.SECTIONS.global.forEach(function (b) {
      if (b.type === 'intvar') {
        var n = b.params[0];
        if (n && opts.indexOf(n) === -1) opts.push(n);
      }
    });
    return opts;
  };

  BB.getVarSuggestions = function () {
    var seen = {}, out = [];
    function add(v) { if (!v) return; if (seen[v]) return; seen[v] = true; out.push(v); }
    ['global', 'setup', 'loop'].forEach(function (sec) {
      BB.SECTIONS[sec].forEach(function (b) {
        if (b.type === 'intvar' || b.type === 'longvar' || b.type === 'stringvar') { add(b.params[0]); }
        if (b.type === 'codeblock') {
          var c = b.params[0] || '';
          var m = c.match(/(?:int|long|String|bool|unsigned long)\s+([a-zA-Z_]\w*)/);
          if (m) add(m[1]);
          var m2 = c.match(/([a-zA-Z_]\w*)\s*=/);
          if (m2) add(m2[1]);
        }
      });
      function walkBody(arr) {
        arr.forEach(function (b) {
          if (b.type === 'intvar' || b.type === 'longvar') { add(b.params[0]); }
          if (b.ifbody) walkBody(b.ifbody);
          if (b.elseifs) b.elseifs.forEach(function (ei) { walkBody(ei.body); });
          if (b.elsebody) walkBody(b.elsebody);
          if (b.body) walkBody(b.body);
        });
      }
      walkBody(BB.SECTIONS[sec]);
    });
    return out;
  };

  BB.getConditionSuggestions = function () {
    var seen = {}, out = [];
    function add(v) { if (!v) return; if (seen[v]) return; seen[v] = true; out.push(v); }
    ['global', 'setup', 'loop'].forEach(function (sec) {
      BB.SECTIONS[sec].forEach(function (b) {
        if (b.type === 'pinmode') {
          var pin = b.params[0], mode = b.params[1];
          if (mode === 'INPUT' || mode === 'INPUT_PULLUP') add('digitalRead(' + pin + ')');
        } else if (b.type === 'analogread') {
          var ap = b.params[0], vn = b.params[1] || 'val';
          add('analogRead(' + ap + ')'); add(vn);
        } else if (b.type === 'intvar' || b.type === 'stringvar') { add(b.params[0]); }
      });
    });
    ['HIGH', 'LOW'].forEach(add);
    return out;
  };

  BB.getPinSuggestions = function (optKey) {
    var seen = {}, out = [];
    BB.SECTIONS.global.forEach(function (b) {
      if (b.type === 'intvar' && b.params[0] && !seen[b.params[0]]) { seen[b.params[0]] = true; out.push(b.params[0]); }
    });
    BB.getOptions(optKey || 'DIGITAL_PIN_OPTIONS').forEach(function (p) {
      if (!seen[p]) { seen[p] = true; out.push(p); }
    });
    return out;
  };

  // ── Condition code generation ─────────────────────────────────────────────
  BB.genCond = function (c) {
    var left = c.leftExpr ? genExpr(c.leftExpr, null, 'x') : (c.left || 'x');
    var right = c.rightExpr ? genExpr(c.rightExpr, null, '0') : (c.right || '0');
    var base = left + ' ' + (c.op || '==') + ' ' + right;
    if (c.joiner && c.joiner !== 'none') {
      var left2 = c.leftExpr2 ? genExpr(c.leftExpr2, null, 'x') : (c.left2 || 'x');
      var right2 = c.rightExpr2 ? genExpr(c.rightExpr2, null, '0') : (c.right2 || '0');
      if (left2 !== 'x') base += ' ' + (c.joiner === 'and' ? '&&' : '||') + ' ' + left2 + ' ' + (c.op2 || '==') + ' ' + right2;
    }
    return base;
  };

  ('[DEBUG] bb-blocks.js: done');
})();
