"""
Manual circuit engine test runner.

Usage:
  1. Generate the prompt:
       python -m utils.circuit_prompt "a doorbell" "BUTTON,BUZZER" easy

  2. Paste the output into Claude or any LLM. Copy the JSON response.

  3. Save the JSON to a file (e.g. test_input.json) and run:
       python run_circuit_test.py test_input.json

  4. Or pipe the JSON directly:
       echo '{"meta":...}' | python run_circuit_test.py

The script prints the engine output as formatted JSON.
Any placement or connection errors are reported with context.
"""

import json
import sys
from utils.circuit_engine import generate_circuit


def run(llm_json: dict) -> None:
    meta       = llm_json.get("meta", {})
    components = llm_json.get("components", [])
    conns      = llm_json.get("connections", [])

    print(f"\nRunning engine for: {meta.get('title', '(untitled)')}")
    print(f"  Components:  {[c['id'] + ':' + c['type'] for c in components]}")
    print(f"  Connections: {len(conns)} logical links")
    print()

    result = generate_circuit(meta, components, conns)

    print("══ ENGINE OUTPUT ══")
    print(json.dumps(result, indent=2))

    print()
    print("══ SUMMARY ══")
    print(f"  Components placed: {len(result['components'])}")
    print(f"  Wires resolved:    {len(result['connections'])}")
    print(f"  Walkthrough steps: {len(result['walkthrough'])}")

    print()
    print("══ COMPONENT PINS ══")
    for comp in result["components"]:
        print(f"  {comp['id']} ({comp['type']}):")
        for pin, loc in comp["pins"].items():
            print(f"    {pin:12s} → col {loc['col']}, row {loc['row']}")

    print()
    print("══ WIRES ══")
    for w in result["connections"]:
        print(f"  {w['from']:30s} → {w['to']:30s}  {w['color']}")


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path) as f:
            llm_json = json.load(f)
    elif not sys.stdin.isatty():
        llm_json = json.load(sys.stdin)
    else:
        print(__doc__)
        sys.exit(0)

    try:
        run(llm_json)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
