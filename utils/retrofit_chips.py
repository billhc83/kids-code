#!/usr/bin/env python3
"""
utils/retrofit_chips.py
One-time script: generate CHIPS lists for all project_*.py modules that lack them.

Usage:
    OPENAI_API_KEY=sk-... python utils/retrofit_chips.py
"""

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed.  pip install openai")
    sys.exit(1)

client = OpenAI()
MODEL  = os.getenv("OPENAI_MODEL", "o4-mini")

_SYSTEM = (
    "You generate help chips for a kids Arduino coding platform (ages 8–14). "
    "Given a project title and its assembly step instructions, generate exactly 5 short "
    "first-person symptom phrases a student might tap when they are stuck. "
    "Make the phrases specific to the components used in this project. "
    "Keep each phrase under 45 characters. "
    "Return ONLY a JSON array of 5 strings — no explanation, no markdown fences."
)


def _load(path):
    spec = importlib.util.spec_from_file_location("_proj", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _context(mod):
    meta   = getattr(mod, "META",  {})
    steps  = getattr(mod, "STEPS", []) or []
    title  = meta.get("title", "Unknown Project")
    instructions = [
        re.sub(r"<[^>]+>", " ", s.get("instruction", "")).strip()
        for s in steps if isinstance(s, dict) and s.get("instruction")
    ]
    # Fallback: pull text from DRAWER_CONTENT if steps are empty
    if not instructions:
        drawer = getattr(mod, "DRAWER_CONTENT", {})
        for proj in drawer.values():
            for step in (proj.get("steps") or []):
                for tab in step.get("tabs", {}).values():
                    raw = re.sub(r"<[^>]+>", " ", tab.get("content", "")).strip()
                    if raw:
                        instructions.append(raw[:200])
    return title, instructions


def _call_llm(title, instructions):
    context = f"Project: {title}\n\nAssembly steps:\n" + "\n".join(f"- {i}" for i in instructions)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": context},
        ],
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\s*", "", raw)
    raw = re.sub(r"\s*```$",       "", raw)
    return json.loads(raw)


def _inject(source, chips):
    items       = "".join(f'    "{c}",\n' for c in chips)
    chips_block = f"CHIPS = [\n{items}]\n\n"
    # Insert CHIPS variable before PROJECT = {
    source = re.sub(r"^(PROJECT\s*=\s*\{)", chips_block + r"\1", source, count=1, flags=re.MULTILINE)
    # Insert "chips": CHIPS, before "presets":
    source = re.sub(r'(\n\s+"presets"\s*:)', '\n    "chips": CHIPS,' + r"\1", source, count=1)
    return source


def main():
    files = sorted(
        f for f in (ROOT / "utils").glob("project_*.py")
        if f.name != "project_registry.py"
    )

    for path in files:
        source = path.read_text(encoding="utf-8")

        if "CHIPS" in source:
            print(f"  skip  {path.name}")
            continue

        print(f"  gen   {path.name} ...", end=" ", flush=True)
        try:
            mod              = _load(path)
            title, instrs    = _context(mod)
            chips            = _call_llm(title, instrs)
            path.write_text(_inject(source, chips), encoding="utf-8")
            print(f"done")
            for c in chips:
                print(f"         · {c}")
        except Exception as exc:
            print(f"ERROR — {exc}")


if __name__ == "__main__":
    main()
