from utils.step_builder import build_step, intro_step, rect, circle, line, lbl


META = {
    'title': 'Project 16: Broken Blinker',
    'circuit_image': 'static/graphics/project_sixteen_circuit.png',
    'banner_image': 'project_sixteen_banner.png',
    'lesson_type': 'troubleshoot',
}


# Wiring and component placement steps.
# rect() / circle() / line() coordinates are placeholders —
# update with real pixel coords once the circuit image is available.
STEPS = []


SKETCH_PRESET = {
    'sketch': 'void setup() {}\n\nvoid loop() {}',
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}


PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": {},
    "presets": {
        "default": SKETCH_PRESET,
    }
}
