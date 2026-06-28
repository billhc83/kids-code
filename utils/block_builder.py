import base64
import math
from pathlib import Path
from flask import render_template
from utils.block_builder_config import build_config
import json

_fab_path = Path(__file__).parent.parent / "static" / "graphics" / "fab.svg"
print(_fab_path)
_fab_icon_b64 = base64.b64encode(_fab_path.read_bytes()).decode("ascii")

# ── Fan menu geometry ─────────────────────────────────────────────────────────
_CX, _CY   = 170, 170   # hub centre in the 200×200 SVG viewBox
_R1, _R2   = 48, 150    # inner / outer slice radius
_RL        = 99         # label position radius

def _polar(cx, cy, r, deg):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)

def _arc_path(cx, cy, r1, r2, a1, a2):
    p1 = _polar(cx, cy, r1, a1); p2 = _polar(cx, cy, r2, a1)
    p3 = _polar(cx, cy, r2, a2); p4 = _polar(cx, cy, r1, a2)
    lg = 1 if (a2 - a1) > 180 else 0
    return (f"M {p1[0]:.2f} {p1[1]:.2f} L {p2[0]:.2f} {p2[1]:.2f} "
            f"A {r2} {r2} 0 {lg} 1 {p3[0]:.2f} {p3[1]:.2f} "
            f"L {p4[0]:.2f} {p4[1]:.2f} A {r1} {r1} 0 {lg} 0 {p1[0]:.2f} {p1[1]:.2f} Z")

# (a1, a2, fill, label, action-id)
_SLICE_DEFS = [
    (180, 213, '#3b82f6', 'Blocks', 'bb'),
    (217, 250, '#7c3aed', 'Help',   'help'),
    (254, 282, '#475569', 'Close',  'close'),
]

def _slice_svg(a1, a2, color, label, sid):
    d  = _arc_path(_CX, _CY, _R1, _R2, a1, a2)
    lx, ly = _polar(_CX, _CY, _RL, (a1 + a2) / 2)
    return (f'<g id="bb-slice-{sid}" class="bb-slice" data-action="{sid}">'
            f'<path d="{d}" fill="{color}" filter="url(#bb-shadow)"/>'
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="13" fill="white" font-weight="700" '
            f'font-family="system-ui,sans-serif" pointer-events="none">{label}</text>'
            f'</g>')

_slices_svg = '\n    '.join(_slice_svg(*s) for s in _SLICE_DEFS)

def get_builder_html(preset, username=None, page=None,
                     drawer_content=None, pin_refs=None, height=500,
                     is_overlay=False, builder_url=None, lock_mode=None,
                     chips=None, **_ignored):

    try:
        if not is_overlay:
            config = build_config(
                preset=preset,
                username=str(username) if username else None,
                page=page,
                lock_mode=lock_mode,
                is_overlay=False,
            )
            config_json = json.dumps(config).replace('</', '<\\/')
            return render_template("block_builder_fragment.html", config=config_json)

        if not builder_url:
            config = build_config(
                preset=preset,
                username=str(username) if username else None,
                page=page,
                lock_mode=lock_mode,
                is_overlay=True,
            )
            config_json = json.dumps(config).replace('</', '<\\/')
            return render_template("block_builder_fragment.html", config=config_json)
            full_doc = f"<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body style='margin:0;padding:0;'>{html_content}</body></html>"
            b64_html = base64.b64encode(full_doc.encode("utf-8")).decode("utf-8")
            builder_url = f"data:text/html;base64,{b64_html}"

    except Exception as e:
        return f"<p style='color:red'>Block builder unavailable: {e}</p>"

    _default_chips = [
        "Something isn't working",
        "My code isn't doing what I expect",
        "My circuit looks wrong",
        "I don't know where to start",
    ]
    _chip_list = chips if chips else _default_chips
    _chips_html = "\n      ".join(
        f'<button type="button" class="bb-chip">{c}</button>' for c in _chip_list
    )

    return f"""
<style>
  #bb-fan-container {{
    position: fixed;
    bottom: 20px; right: 20px;
    width: 200px; height: 200px;
    z-index: 999999;
    pointer-events: none;
  }}
  #bb-fan-svg {{ overflow: visible; }}
  .bb-slice {{
    pointer-events: all;
    cursor: pointer;
    transform-box: view-box;
    transform-origin: {_CX}px {_CY}px;
    transform: scale(0);
    opacity: 0;
    transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease;
  }}
  .bb-slice.visible {{ transform: scale(1); opacity: 1; }}
  .bb-slice.visible:hover:not(.inactive) {{ transform: scale(1.08); }}
  .bb-slice path {{ transition: opacity 0.2s ease; }}
  .bb-slice.inactive path {{ opacity: 0.3; }}
  #bb-hub {{
    pointer-events: all;
    cursor: pointer;
  }}
  #bb-hub circle {{ transition: filter 0.2s ease; }}
  #bb-hub:hover circle {{ filter: brightness(1.15); }}
  #bb-overlay {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.9);
    display: none;
    z-index: 999998;
    opacity: 0;
    transition: opacity 0.3s ease;
    backdrop-filter: blur(4px);
  }}
  #bb-overlay.visible {{ opacity: 1; }}
  #bb-iframe {{
    position: absolute;
    top: 20px; left: 20px; right: 20px; bottom: 20px;
    width: calc(100% - 40px);
    height: calc(100% - 40px);
    background: white;
    border: none;
    border-radius: 24px;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
  }}
  #bb-help-dialog {{
    display: none;
    position: fixed;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 340px;
    max-height: 520px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px -10px rgba(0,0,0,0.4), 0 0 0 1px rgba(0,0,0,0.08);
    z-index: 1000001;
    flex-direction: column;
    overflow: hidden;
    font-family: system-ui, sans-serif;
  }}
  #bb-help-titlebar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: linear-gradient(135deg, #7c3aed, #5b21b6);
    cursor: grab;
    user-select: none;
    border-radius: 16px 16px 0 0;
    flex-shrink: 0;
  }}
  #bb-help-titlebar:active {{ cursor: grabbing; }}
  #bb-help-title {{ color: white; font-weight: 700; font-size: 15px; }}
  #bb-help-close {{
    background: rgba(255,255,255,0.2);
    border: none;
    color: white;
    width: 28px; height: 28px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 14px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }}
  #bb-help-close:hover {{ background: rgba(255,255,255,0.35); }}
  #bb-help-body {{
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
    padding: 16px;
    gap: 12px;
  }}
  .bb-help-hint {{
    font-size: 13px;
    color: #64748b;
    margin: 0 0 4px 0;
    font-weight: 600;
  }}
  #bb-help-chips {{ display: flex; flex-direction: column; gap: 8px; }}
  .bb-chip {{
    background: #f1f5f9;
    border: 1.5px solid #e2e8f0;
    border-radius: 20px;
    padding: 9px 16px;
    font-size: 13px;
    color: #334155;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
    font-family: system-ui, sans-serif;
  }}
  .bb-chip:hover {{ background: #ede9fe; border-color: #7c3aed; color: #5b21b6; }}
  #bb-help-chat {{
    flex: 1;
    overflow-y: auto;
    display: none;
    flex-direction: column;
    gap: 10px;
    min-height: 0;
  }}
  #bb-help-input-row {{ display: flex; gap: 8px; align-items: center; flex-shrink: 0; }}
  #bb-help-input {{
    flex: 1;
    border: 1.5px solid #e2e8f0;
    border-radius: 20px;
    padding: 9px 14px;
    font-size: 13px;
    outline: none;
    font-family: system-ui, sans-serif;
    transition: border-color 0.15s;
  }}
  #bb-help-input:focus {{ border-color: #7c3aed; }}
  #bb-help-send {{
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #7c3aed;
    border: none;
    color: white;
    font-size: 16px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
    flex-shrink: 0;
  }}
  #bb-help-send:hover {{ background: #5b21b6; }}
</style>

<div id="bb-fan-container">
  <svg id="bb-fan-svg" viewBox="0 0 200 200" width="200" height="200">
    <defs>
      <filter id="bb-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="rgba(0,0,0,0.3)"/>
      </filter>
    </defs>
    {_slices_svg}
    <g id="bb-hub">
      <circle cx="{_CX}" cy="{_CY}" r="40" fill="#3b82f6" filter="url(#bb-shadow)"/>
      <image href="data:image/svg+xml;base64,{_fab_icon_b64}"
             x="{_CX - 35}" y="{_CY - 35}" width="70" height="70"/>
    </g>
  </svg>
</div>

<div id="bb-help-dialog">
  <div id="bb-help-titlebar">
    <span id="bb-help-title">💡 Help</span>
    <button id="bb-help-close" title="Close">✕</button>
  </div>
  <div id="bb-help-body">
    <div id="bb-help-chips">
      <p class="bb-help-hint">What's going wrong?</p>
      {_chips_html}
    </div>
    <div id="bb-help-chat"></div>
    <div id="bb-help-input-row">
      <input id="bb-help-input" type="text" placeholder="Describe what's happening..." autocomplete="off"/>
      <button id="bb-help-send">➤</button>
    </div>
  </div>
</div>

<div id="bb-ai-consent-modal" style="display:none;position:fixed;inset:0;
     background:rgba(15,23,42,0.75);z-index:1000002;
     align-items:center;justify-content:center;padding:20px;">
  <div style="background:#fff;border-radius:16px;max-width:380px;width:100%;
              box-shadow:0 20px 60px rgba(0,0,0,0.3);padding:28px 24px;">
    <div style="font-size:28px;text-align:center;margin-bottom:12px;">🤖</div>
    <h3 style="font-size:16px;font-weight:800;color:#1f2328;margin:0 0 10px;text-align:center;">
      AI Hint — Quick Note
    </h3>
    <p style="font-size:13px;color:#57606a;line-height:1.65;margin:0 0 16px;">
      To generate a hint, your current code and question will be sent to
      <strong>OpenAI</strong>. OpenAI does not use this to train its models.
    </p>
    <p style="font-size:12px;color:#57606a;line-height:1.6;margin:0 0 20px;">
      See our <a href="/privacy" target="_blank"
        style="color:#0969da;">Privacy Policy</a> for full details.
      This message only shows once.
    </p>
    <div style="display:flex;gap:10px;">
      <button id="bb-consent-confirm"
              style="flex:1;background:#2ea44f;color:#fff;border:none;border-radius:8px;
                     padding:10px;font-size:14px;font-weight:700;cursor:pointer;
                     font-family:system-ui,sans-serif;">
        Got it, continue
      </button>
      <button id="bb-consent-cancel"
              style="flex:1;background:#f6f8fa;color:#24292f;border:1px solid #d0d7de;
                     border-radius:8px;padding:10px;font-size:14px;font-weight:600;
                     cursor:pointer;font-family:system-ui,sans-serif;">
        Cancel
      </button>
    </div>
  </div>
</div>

<div id="bb-overlay">
  <iframe id="bb-iframe" src="{builder_url}"></iframe>
</div>

<script>
(function() {{
  var overlay = document.getElementById('bb-overlay');
  var menuOpen = false;
  var bbOpen = false;

  function openMenu() {{
    menuOpen = true;
    document.querySelectorAll('.bb-slice').forEach(function(el, i) {{
      setTimeout(function() {{ el.classList.add('visible'); }}, i * 70);
    }});
  }}

  function closeMenu() {{
    menuOpen = false;
    document.querySelectorAll('.bb-slice').forEach(function(el) {{
      el.classList.remove('visible');
    }});
  }}

  function openBuilder() {{
    bbOpen = true;
    overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';
    void overlay.offsetWidth;
    overlay.classList.add('visible');
    var s = document.getElementById('bb-slice-bb');
    if (s) s.classList.add('inactive');
  }}

  function closeBuilder() {{
    bbOpen = false;
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    setTimeout(function() {{ overlay.style.display = 'none'; }}, 250);
    var s = document.getElementById('bb-slice-bb');
    if (s) s.classList.remove('inactive');
  }}

  document.getElementById('bb-hub').addEventListener('click', function() {{
    if (!menuOpen) {{ openMenu(); }} else {{ closeMenu(); }}
  }});

  document.querySelectorAll('.bb-slice').forEach(function(el) {{
    el.addEventListener('click', function() {{
      var action = el.getAttribute('data-action');
      if (action === 'bb') {{
        if (!bbOpen) openBuilder();
      }} else if (action === 'help') {{
        openHelp();
      }} else if (action === 'close') {{
        if (bbOpen) {{
          var iframe = document.getElementById('bb-iframe');
          if (iframe && iframe.contentWindow) {{
            iframe.contentWindow.postMessage({{type: 'bb_save_request'}}, '*');
          }} else {{
            closeBuilder();
            closeMenu();
          }}
        }} else {{
          closeMenu();
        }}
      }}
    }});
  }});

  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'bb_close') {{
      closeBuilder();
      closeMenu();
    }}
  }});

  // ── Help dialog ────────────────────────────────────────────────────────────
  var helpDialog = document.getElementById('bb-help-dialog');
  var helpDrag = null;
  var helpPositioned = false;

  function openHelp() {{
    helpDialog.style.display = 'flex';
    if (!helpPositioned) {{
      helpDialog.style.transform = 'translate(-50%, -50%)';
    }}
    var s = document.getElementById('bb-slice-help');
    if (s) s.classList.add('inactive');
  }}

  function closeHelp() {{
    helpDialog.style.display = 'none';
    var s = document.getElementById('bb-slice-help');
    if (s) s.classList.remove('inactive');
  }}

  document.getElementById('bb-help-close').addEventListener('click', closeHelp);

  function dragStart(clientX, clientY) {{
    var r = helpDialog.getBoundingClientRect();
    helpDialog.style.left = r.left + 'px';
    helpDialog.style.top = r.top + 'px';
    helpDialog.style.transform = 'none';
    helpPositioned = true;
    helpDrag = {{ x: clientX, y: clientY, l: r.left, t: r.top }};
  }}

  function dragMove(clientX, clientY) {{
    if (!helpDrag) return;
    var l = Math.max(0, Math.min(window.innerWidth  - helpDialog.offsetWidth,  helpDrag.l + clientX - helpDrag.x));
    var t = Math.max(0, Math.min(window.innerHeight - helpDialog.offsetHeight, helpDrag.t + clientY - helpDrag.y));
    helpDialog.style.left = l + 'px';
    helpDialog.style.top  = t + 'px';
  }}

  var helpTitlebar = document.getElementById('bb-help-titlebar');
  helpTitlebar.addEventListener('mousedown', function(e) {{ dragStart(e.clientX, e.clientY); e.preventDefault(); }});
  document.addEventListener('mousemove', function(e) {{ dragMove(e.clientX, e.clientY); }});
  document.addEventListener('mouseup',   function()  {{ helpDrag = null; }});
  helpTitlebar.addEventListener('touchstart', function(e) {{ var t = e.touches[0]; dragStart(t.clientX, t.clientY); e.preventDefault(); }}, {{passive: false}});
  document.addEventListener('touchmove',  function(e) {{ if (helpDrag) {{ var t = e.touches[0]; dragMove(t.clientX, t.clientY); e.preventDefault(); }} }}, {{passive: false}});
  document.addEventListener('touchend',   function()  {{ helpDrag = null; }});

  // ── Help chat ──────────────────────────────────────────────────────────────
  var helpProjectKey = {json.dumps(page or '')};
  var helpStepIndex  = 0;

  // Track step changes broadcast from the block builder iframe
  window.addEventListener('message', function(e) {{
    if (e.data && e.data.type === 'bb_step_change') helpStepIndex = e.data.step || 0;
  }});

  // Reset dialog to chips view when closed
  var _origCloseHelp = closeHelp;
  closeHelp = function() {{
    _origCloseHelp();
    document.getElementById('bb-help-chips').style.display = '';
    var chat = document.getElementById('bb-help-chat');
    chat.style.display = 'none';
    chat.innerHTML = '';
  }};

  function sendHelp(symptom, freeform) {{
    document.getElementById('bb-help-chips').style.display = 'none';
    var chat = document.getElementById('bb-help-chat');
    chat.style.display = 'flex';

    var userBubble = document.createElement('div');
    userBubble.style.cssText = 'align-self:flex-end;background:#7c3aed;color:white;border-radius:14px 14px 4px 14px;padding:8px 12px;font-size:13px;max-width:85%;word-break:break-word;';
    userBubble.textContent = symptom || freeform;
    chat.appendChild(userBubble);

    var aiBubble = document.createElement('div');
    aiBubble.style.cssText = 'align-self:flex-start;background:#f1f5f9;color:#1e293b;border-radius:14px 14px 14px 4px;padding:8px 12px;font-size:13px;max-width:85%;word-break:break-word;';
    aiBubble.textContent = '...';
    chat.appendChild(aiBubble);
    chat.scrollTop = chat.scrollHeight;

    fetch('/api/help', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        project_key:  helpProjectKey,
        step_index:   helpStepIndex,
        symptom:      symptom,
        freeform:     freeform,
      }})
    }}).then(function(resp) {{
      if (resp.status === 429) {{
        return resp.json().then(function(d) {{
          if (d.error === 'daily_cap') {{
            aiBubble.innerHTML = "This might need more help than I can give — ask a parent or teacher to have a look! Or <a href='/feedback' style='color:#7c3aed;font-weight:600;'>contact us</a> and we’ll help out. 🙋";
          }} else {{
            aiBubble.textContent = "Slow down a little — try again in a minute! ⏱️";
          }}
        }});
      }}
      var reader  = resp.body.getReader();
      var decoder = new TextDecoder();
      var text    = '';
      aiBubble.textContent = '';
      function read() {{
        reader.read().then(function(r) {{
          if (r.done) return;
          decoder.decode(r.value).split('\\n').forEach(function(line) {{
            if (!line.startsWith('data: ')) return;
            var payload = line.slice(6);
            if (payload === '[DONE]') return;
            try {{ text += JSON.parse(payload); aiBubble.textContent = text; chat.scrollTop = chat.scrollHeight; }} catch(e) {{}}
          }});
          read();
        }});
      }}
      read();
    }}).catch(function() {{ aiBubble.textContent = 'Something went wrong — try again!'; }});
  }}

  function maybeRequestConsent(callback) {{
    if (localStorage.getItem('ai_tutor_consented')) {{
      callback();
      return;
    }}
    var modal = document.getElementById('bb-ai-consent-modal');
    modal.style.display = 'flex';
    document.getElementById('bb-consent-confirm').onclick = function() {{
      localStorage.setItem('ai_tutor_consented', 'true');
      modal.style.display = 'none';
      callback();
    }};
    document.getElementById('bb-consent-cancel').onclick = function() {{
      modal.style.display = 'none';
    }};
  }}

  document.querySelectorAll('.bb-chip').forEach(function(chip) {{
    chip.addEventListener('click', function(e) {{
      e.preventDefault();
      maybeRequestConsent(function() {{ sendHelp(chip.textContent.trim(), ''); }});
    }});
  }});

  var helpInput = document.getElementById('bb-help-input');
  document.getElementById('bb-help-send').addEventListener('click', function() {{
    var txt = helpInput.value.trim();
    if (txt) {{
      maybeRequestConsent(function() {{ sendHelp('', txt); helpInput.value = ''; }});
    }}
  }});
  helpInput.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') {{ document.getElementById('bb-help-send').click(); }}
  }});
}})();
</script>
"""