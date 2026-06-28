"""
Circuit comparison tool.

Extracts components + Arduino signal pins from an existing project, prompts the
local LLM to generate a fresh logical circuit description, runs it through the
engine, and writes a side-by-side comparison JSON for the dev viewer.

Usage:
    python -m utils.circuit_compare <project_name> [--model MODEL] [--host HOST]
    python -m utils.circuit_compare --all [--model MODEL] [--host HOST]

Examples:
    python -m utils.circuit_compare one
    python -m utils.circuit_compare --all
    python -m utils.circuit_compare two --model qwen3-14b-nothink:latest

Output:
    static/circuit_compare/<project_name>.json
    {
        "project":    "one",
        "llm_input":  { topic, components, pins },
        "llm_output": { meta, components, connections },
        "original":   CIRCUIT_DEFINITION (if present, else null),
        "generated":  engine output
    }
"""

import importlib
import inspect
import json
import os
import re
import sys
import requests

from utils.circuit_engine import generate_circuit
from utils.circuit_prompt import build_prompt

# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_MODEL  = "qwen3-14b-nothink:latest"
DEFAULT_HOST   = "http://localhost:11434"
OUTPUT_DIR     = os.path.join(os.path.dirname(__file__), "..", "static", "circuit_compare")

INJECTED_TYPES = {"RESISTOR"}
POWER_PINS     = {"GND", "5V", "VIN", "3V3"}

# Supported component types the engine can place
SUPPORTED_TYPES = {"LED", "BUTTON", "BUZZER", "SERVO", "LDR", "HC_SR04", "SLIDE_SWITCH"}


# ── Sketch-based extraction ────────────────────────────────────────────────────

def _collect_sketch_code(module):
    """Combine all sketch text from all presets, stripping //>> directives and expanding //## lines."""
    presets = {}
    if hasattr(module, "PROJECT"):
        presets = module.PROJECT.get("presets", {})
    if not presets and hasattr(module, "SKETCH_PRESET"):
        presets = {"default": module.SKETCH_PRESET}

    lines_out = []
    for pdata in presets.values():
        if not isinstance(pdata, dict):
            continue
        for line in pdata.get("sketch", "").splitlines():
            stripped = line.strip()
            if stripped.startswith("//##"):
                lines_out.append(stripped[4:].strip())
            elif stripped.startswith("//>>") or stripped.startswith("//?? "):
                pass  # directive — skip
            else:
                lines_out.append(line)
    return "\n".join(lines_out)


def _resolve_vars(code):
    """Return {varName: 'D8' or 'A0'} for all int x = <pin>; assignments."""
    var_map = {}
    for m in re.finditer(r"\bint\s+(\w+)\s*=\s*(\d+)", code):
        var_map[m.group(1)] = f"D{m.group(2)}"
    for m in re.finditer(r"\bint\s+(\w+)\s*=\s*A(\d+)", code):
        var_map[m.group(1)] = f"A{m.group(2)}"
    return var_map


def _pin_is_buzzer(sketch_code, module_src, pin_num):
    """
    Return True if this OUTPUT pin drives a buzzer rather than an LED.

    Two strict checks to avoid false positives from nearby text:
    1. Sketch code: 'buzzer' on the same line as the pin number
       (matches `// buzzer` inline comments)
    2. Module source: a line contains both 'buzzer' AND an explicit 'pin N' reference
       (matches text like "Pin 8 powers the rocket buzzer")
    """
    pin_str = str(pin_num)

    # Check 1: sketch code same-line (most reliable)
    for line in sketch_code.lower().split("\n"):
        nums = re.findall(r"\b\d+\b", line)
        if pin_str in nums and "buzzer" in line:
            return True

    # Check 2: module source — explicit "pin N" + "buzzer" co-occurrence on one line
    pin_pattern = re.compile(r"\bpin\s*" + re.escape(pin_str) + r"\b")
    for line in module_src.split("\n"):
        if "buzzer" in line and pin_pattern.search(line):
            return True

    return False


def _pin_is_switch(sketch_code, module_src, pin_num):
    """
    Return True if this INPUT_PULLUP pin is a SLIDE_SWITCH rather than a BUTTON.

    Two checks:
    1. Sketch code: 'switch' on the same line as the pin number
    2. Module source: 'switch' within 2 lines AFTER a 'pin N' reference
       (assembly steps typically list "Arduino Pin N" then "signal wire for Switch N")
    """
    pin_str = str(pin_num)

    # Check 1: sketch code — 'switch' in the comment portion of a line that also
    # contains the pin number.  Ignores variable names like 'switchPin'.
    for line in sketch_code.lower().split("\n"):
        comment_start = line.find("//")
        if comment_start == -1:
            continue
        nums = re.findall(r"\b\d+\b", line)
        if pin_str in nums and "switch" in line[comment_start:]:
            return True

    # Check 2: module source — 'switch' within 2 lines AFTER a 'pin N' reference
    # (assembly steps typically list "Arduino Pin N" then "signal wire for Switch N")
    lines = module_src.split("\n")   # already lowercased
    pin_pattern = re.compile(r"\bpin\s*" + re.escape(pin_str) + r"\b")
    for i, line in enumerate(lines):
        if pin_pattern.search(line):
            window = lines[i: min(len(lines), i + 3)]
            if any("switch" in l for l in window):
                return True

    return False


def _extract_from_sketch(module):
    """
    Parse the project sketch(es) to infer component types and signal pins.

    Returns (components, pins):
        components  — list of {type, properties} — no IDs, no coords
        pins        — list of 'D8', 'A0', … signal pin strings (no GND/5V)
    """
    code    = _collect_sketch_code(module)
    var_map = _resolve_vars(code)

    def resolve(name):
        name = name.strip()
        if re.fullmatch(r"\d+", name):
            return f"D{name}"
        if re.fullmatch(r"A\d+", name):
            return name
        return var_map.get(name)

    claimed    = set()   # pins already assigned to a component
    components = []

    # ── HC_SR04 — pair trig/echo variable names by suffix ──
    # e.g. trigPin+echoPin → suffix='pin', trigA+echoA → suffix='a'
    trig_map = {}  # suffix → resolved pin
    echo_map = {}  # suffix → resolved pin
    for varname, pin in var_map.items():
        lower = varname.lower()
        if "trig" in lower:
            suffix = re.sub(r"trig", "", lower)
            trig_map[suffix] = pin
        elif "echo" in lower:
            suffix = re.sub(r"echo", "", lower)
            echo_map[suffix] = pin
    # Also capture echo pins from pulseIn() calls
    for mm in re.finditer(r"pulseIn\s*\(\s*(\w+)", code):
        p = resolve(mm.group(1))
        if p:
            for varname, vpin in var_map.items():
                if vpin == p and "echo" in varname.lower():
                    suffix = re.sub(r"echo", "", varname.lower())
                    echo_map[suffix] = p

    for suffix in sorted(set(trig_map) & set(echo_map)):
        trig_pin = trig_map[suffix]
        echo_pin = echo_map[suffix]
        if trig_pin not in claimed and echo_pin not in claimed:
            claimed.add(trig_pin)
            claimed.add(echo_pin)
            components.append({
                "type": "HC_SR04",
                "properties": {},
                "_pin":      trig_pin,   # TRIG (primary signal — OUTPUT)
                "_echo_pin": echo_pin,   # ECHO (secondary signal — INPUT)
            })

    # ── Helper for single-pin components ──────────────────────────────────────
    def _add(comp_type, pin, **props):
        if not pin or pin in claimed:
            return
        if pin.startswith("A") and comp_type != "LDR":
            return  # A-pins only valid for LDR
        claimed.add(pin)
        components.append({"type": comp_type, "properties": props, "_pin": pin})

    # SERVO — .attach() is unambiguous
    for m in re.finditer(r"\.attach\s*\(\s*(\w+)", code):
        _add("SERVO", resolve(m.group(1)))

    # BUZZER — tone(pin, ...)
    for m in re.finditer(r"\btone\s*\(\s*(\w+)", code):
        _add("BUZZER", resolve(m.group(1)))

    # LDR — analogRead(A-pin)
    for m in re.finditer(r"analogRead\s*\(\s*(\w+)", code):
        p = resolve(m.group(1))
        if p and p.startswith("A"):
            _add("LDR", p)

    # Module source used for component disambiguation (buzzer vs LED, switch vs button)
    try:
        module_src = inspect.getsource(module).lower()
    except Exception:
        module_src = ""

    # BUTTON or SLIDE_SWITCH — digitalRead(pin)
    for m in re.finditer(r"digitalRead\s*\(\s*(\w+)", code):
        p = resolve(m.group(1))
        if p:
            pin_num = int(p[1:]) if p.startswith("D") and p[1:].isdigit() else None
            if pin_num and _pin_is_switch(code, module_src, pin_num):
                _add("SLIDE_SWITCH", p)
            else:
                _add("BUTTON", p)

    # LED or BUZZER — digitalWrite on an OUTPUT-configured pin not already claimed
    # A passive buzzer driven by digitalWrite can't be distinguished from an LED
    # by code alone — check module text for "buzzer" near the pin number.
    output_pins = set()
    for m in re.finditer(r"pinMode\s*\(\s*(\w+)\s*,\s*OUTPUT", code):
        p = resolve(m.group(1))
        if p:
            output_pins.add(p)
    for m in re.finditer(r"digitalWrite\s*\(\s*(\w+)", code):
        p = resolve(m.group(1))
        if p and (p in output_pins or p not in claimed):
            pin_num = int(p[1:]) if p.startswith("D") and p[1:].isdigit() else None
            if pin_num and _pin_is_buzzer(code, module_src, pin_num):
                _add("BUZZER", p)
            else:
                _add("LED", p, color="red")

    # Build output lists — include both trig and echo pins for HC_SR04
    result_comps = [
        {"type": c["type"], "properties": {k: v for k, v in c["properties"].items()}}
        for c in components if c["type"] in SUPPORTED_TYPES
    ]
    pins = []
    for c in components:
        if c["type"] not in SUPPORTED_TYPES:
            continue
        pins.append(c["_pin"])
        if "_echo_pin" in c:
            pins.append(c["_echo_pin"])

    return result_comps, pins


# ── Main extraction entry point ────────────────────────────────────────────────

def extract_hints(project_key):
    """
    Load utils/project_{key}.py and return:
        topic        — META title
        components   — list of {type, properties}
        pins         — Arduino signal pins (no GND/5V)
        circuit_def  — raw CIRCUIT_DEFINITION (or None for sketch-inferred projects)
        difficulty   — difficulty string

    Prefers CIRCUIT_DEFINITION when present; falls back to sketch parsing.
    """
    module      = importlib.import_module(f"utils.project_{project_key}")
    meta        = getattr(module, "META", {})
    circuit_def = getattr(module, "CIRCUIT_DEFINITION", None)
    topic       = meta.get("title", project_key)

    if circuit_def is not None:
        # Ground-truth path — use the hand-built definition
        components = [
            {"type": c["type"], "properties": dict(c.get("properties", {}))}
            for c in circuit_def["components"]
            if c["type"] not in INJECTED_TYPES
        ]
        pins = []
        for conn in circuit_def["connections"]:
            for endpoint in (conn["from"], conn["to"]):
                if endpoint.startswith("arduino."):
                    pin = endpoint[len("arduino."):]
                    if pin not in POWER_PINS and pin not in pins:
                        pins.append(pin)
        difficulty = circuit_def.get("meta", {}).get("difficulty", "easy")
        return topic, components, pins, circuit_def, difficulty

    # Fallback — infer from sketch
    components, pins = _extract_from_sketch(module)
    return topic, components, pins, None, "easy"


# ── LLM call ───────────────────────────────────────────────────────────────────

def call_llm(system_prompt, user_message, model=DEFAULT_MODEL, host=DEFAULT_HOST):
    """POST to ollama /api/chat and return parsed JSON dict."""
    url = f"{host}/api/chat"
    payload = {
        "model":    model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not reach ollama at {host}. Is it running? (ollama serve)"
        )

    raw = resp.json()["message"]["content"].strip()

    # Safety strip for any stray markdown fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


# ── Prompt builder ─────────────────────────────────────────────────────────────

def _component_str(components):
    """Format extracted component list for the prompt."""
    parts = []
    for c in components:
        label = c["type"]
        props = {k: v for k, v in c["properties"].items() if k != "ohms"}
        if props:
            label += " (" + ", ".join(f"{k}={v}" for k, v in props.items()) + ")"
        parts.append(label)
    return ", ".join(parts)


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_comparison(project_key, model=DEFAULT_MODEL, host=DEFAULT_HOST):
    print(f"\n── Comparing project_{project_key} ──")

    topic, components, pins, original, difficulty = extract_hints(project_key)

    if not components:
        print(f"  SKIP: no supported components found for project_{project_key}")
        return None

    print(f"  Topic      : {topic}")
    print(f"  Components : {_component_str(components)}")
    print(f"  Pins       : {', '.join(pins) if pins else '(none)'}")
    if original is None:
        print("  (hints inferred from sketch — no CIRCUIT_DEFINITION)")

    comp_str = _component_str(components)
    system_prompt, user_message = build_prompt(
        topic=topic,
        components=comp_str,
        difficulty=difficulty,
        pin_hint=pins if pins else None,
    )

    print(f"\n  Calling {model} ...")
    llm_output = call_llm(system_prompt, user_message, model=model, host=host)
    print(f"  LLM returned {len(llm_output.get('components', []))} components, "
          f"{len(llm_output.get('connections', []))} connections")

    print("  Running engine ...")
    generated = generate_circuit(
        meta=llm_output.get("meta", {}),
        components=llm_output.get("components", []),
        logical_connections=llm_output.get("connections", []),
    )
    print(f"  Engine placed {len(generated['components'])} components, "
          f"{len(generated['connections'])} wires")

    comparison = {
        "project": project_key,
        "llm_input": {
            "topic":      topic,
            "components": comp_str,
            "pins":       pins,
        },
        "llm_output": llm_output,
        "original":   original,
        "generated":  generated,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{project_key}.json")
    with open(out_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"  Written → {out_path}")
    return comparison


def _all_project_keys():
    """Discover all project keys from utils/project_*.py files."""
    utils_dir = os.path.join(os.path.dirname(__file__))
    keys = []
    for fname in sorted(os.listdir(utils_dir)):
        m = re.fullmatch(r"project_(\w+)\.py", fname)
        if m and m.group(1) != "registry":
            keys.append(m.group(1))
    return keys


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate and compare circuit JSON for a project.")
    parser.add_argument("project", nargs="?",        help="Project name, e.g. 'one', 'two'. Omit with --all.")
    parser.add_argument("--all",   action="store_true", help="Run all projects.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag")
    parser.add_argument("--host",  default=DEFAULT_HOST,  help="Ollama host URL")
    args = parser.parse_args()

    if not args.all and not args.project:
        parser.error("Provide a project name or use --all")

    keys = _all_project_keys() if args.all else [args.project]

    errors = []
    for key in keys:
        try:
            run_comparison(key, model=args.model, host=args.host)
        except Exception as e:
            print(f"\n  ERROR ({key}): {e}")
            errors.append((key, str(e)))

    if errors:
        print(f"\n── {len(errors)} project(s) failed ──")
        for k, msg in errors:
            print(f"  {k}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
