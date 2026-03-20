import base64
from io import BytesIO
from PIL import Image # type: ignore

def hover_zoom_html(image, height=600, zoom_factor=2.5, key="unique"):
    if not isinstance(image, Image.Image):
        image = Image.open(image)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    container_id = f"zoom-container-{key}"
    return f"""
    <div id="{container_id}" class="zoom-container">
        <img src="data:image/png;base64,{img_str}" id="img-{key}">
    </div>
    <style>
    #{container_id} {{
        width: 100%;
        height: {height}px;
        overflow: hidden;
        border: 1px solid #dbeafe;
        border-radius: 10px;
        position: relative;
    }}
    #{container_id} img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        transition: transform 0.1s ease-out;
        transform-origin: center center;
    }}
    #{container_id}:hover img {{
        transform: scale({zoom_factor});
        cursor: crosshair;
    }}
    </style>
    <script>
    (function() {{
        const container = document.getElementById("{container_id}");
        const img = document.getElementById("img-{key}");
        container.addEventListener("mousemove", function(e) {{
            const rect = container.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            img.style.transformOrigin = x + "% " + y + "%";
        }});
        container.addEventListener("mouseleave", function() {{
            img.style.transformOrigin = "center center";
        }});
    }})();
    </script>
    """