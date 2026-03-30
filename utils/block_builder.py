import base64
from pathlib import Path

# Use absolute path to ensure the file is found regardless of working directory
_fab_path = Path(__file__).parent.parent / "static" / "graphics" / "fab.svg"
print(_fab_path)
_fab_icon_b64 = base64.b64encode(_fab_path.read_bytes()).decode("ascii")

def get_builder_html(preset, username=None, page=None,
                     drawer_content=None, pin_refs=None, height=500,
                     supabase_url=None, supabase_key=None, is_overlay=False, builder_url=None, lock_mode=None):
    """
    Calls the local arduino_blocks generator and returns
    the complete FAB + overlay HTML as a string.
    """
    try:
        if not is_overlay:
            from utils.arduino_blocks import render_builder
            from config import SUPABASE_ANON_KEY, SUPABASE_URL
            return render_builder(
                preset=preset,
                username=str(username) if username else None,
                page=page,
                drawer_content=drawer_content,
                pin_refs=pin_refs,
                is_overlay=is_overlay,
                height=height, # Pass height here
                supabase_url=SUPABASE_URL,
                supabase_key=SUPABASE_ANON_KEY,
                lock_mode=lock_mode
            )

        # If no URL provided, we fallback to a data URI of the blocks (less ideal for origins)
        if not builder_url:
             from utils.arduino_blocks import render_builder
             from config import SUPABASE_ANON_KEY, SUPABASE_URL
             html_content = render_builder(preset=preset, username=str(username), page=page, is_overlay=True, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_ANON_KEY, lock_mode=lock_mode)
             full_doc = f"<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body style='margin:0;padding:0;'>{html_content}</body></html>"
             b64_html = base64.b64encode(full_doc.encode("utf-8")).decode("utf-8")
             builder_url = f"data:text/html;base64,{b64_html}"

    except Exception as e:
        return f"<p style='color:red'>Block builder unavailable: {e}</p>"

    return f"""
<style>
    #bb-fab {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 90px;
        height: 90px;
        background: #2196f3;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        z-index: 999999;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        user-select: none;
    }}
    #bb-fab:hover {{transform: scale(1.1); background: #1976d2; }}
    #bb-fab.open {{ background: #455a64; transform: rotate(180deg); }}
    #bb-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(15, 23, 42, 0.85);
        display: none;
        z-index: 999998;
        opacity: 0;
        transition: opacity 0.3s ease;
        backdrop-filter: blur(4px);
    }}
    #bb-overlay.visible {{ opacity: 1; }}
    #bb-iframe {{
        position: absolute;
        top: 10px; left: 10px; right: 10px; bottom: 10px;
        width: calc(100% - 20px);
        height: calc(100% - 20px);
        background: white;
        border: none;
        border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.6);
    }}
</style>
<div id="bb-fab" title="Open Block Builder">
    <img src="data:image/svg+xml;base64,{_fab_icon_b64}"
         width="70" height="70" />
</div>
<div id="bb-overlay">
    <iframe id="bb-iframe" src="{builder_url}"></iframe>
</div>
<script>
(function() {{
    var fab = document.getElementById('bb-fab');
    var overlay = document.getElementById('bb-overlay');
    var isOpen = false;

    function openBuilder() {{
        isOpen = true;
        overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';
        void overlay.offsetWidth; // Force reflow
        overlay.classList.add('visible');
        fab.classList.add('open');
        fab.innerHTML = '<span style="color:white;font-size:36px;font-weight:300;">\\u2715</span>';
    }}

    function closeBuilder() {{
        isOpen = false;
        overlay.classList.remove('visible');
        fab.classList.remove('open');
        document.body.style.overflow = '';
        setTimeout(function() {{ overlay.style.display = 'none'; }}, 250);
        fab.innerHTML = '<img src="data:image/svg+xml;base64,{_fab_icon_b64}" width="70" height="70" />';
    }}

    fab.addEventListener('click', function() {{
        if (isOpen) {{
            var iframe = document.getElementById('bb-iframe');
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage({{type: 'bb_save_request'}}, '*');
            }} else {{
                closeBuilder();
            }}
        }} else {{
            openBuilder();
        }}
    }});

    window.addEventListener('message', function(e) {{
        if (e.data && e.data.type === 'bb_close') {{
            closeBuilder();
        }}
    }});
}})();
</script>
"""
