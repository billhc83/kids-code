import base64
from pathlib import Path

def img_to_b64(path):
    """
    Converts an image file to a base64 string for embedding in HTML.
    """
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = Path(path).suffix.lstrip(".")
    return f"data:image/{ext};base64,{b64}"