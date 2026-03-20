import base64
from pathlib import Path

# Use absolute path to ensure the file is found regardless of working directory
_fab_path = Path(__file__).parent.parent / "static" / "graphics" / "fab.svg"
print(_fab_path)
_fab_icon_b64 = base64.b64encode(_fab_path.read_bytes()).decode("ascii")

def get_builder_html(preset, username=None, page=None,
                     drawer_content=None, pin_refs=None,
                     supabase_url=None, supabase_key=None):
    """
    Calls the local arduino_blocks generator and returns
    the complete FAB + overlay HTML as a string.
    """
    try:
        from utils.arduino_blocks import render_builder

        html_content = render_builder(
            preset=preset,
            username=str(username) if username else None,
            page=page,
            drawer_content=drawer_content,
            pin_refs=pin_refs,
            is_overlay=True,
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )

        b64_html = base64.b64encode(
            html_content.encode("utf-8")
        ).decode("utf-8")
        builder_url = f"data:text/html;base64,{b64_html}"
    except Exception as e:
        return f"<p style='color:red'>Block builder unavailable: {e}</p>"

    return f"""
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
        setTimeout(function() {{ overlay.classList.add('visible'); }}, 10);
        fab.classList.add('open');
        fab.innerHTML = '<span style="color:white;font-size:36px;font-weight:300;">✕</span>';
    }}

    function closeBuilder() {{
        isOpen = false;
        overlay.classList.remove('visible');
        fab.classList.remove('open');
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
