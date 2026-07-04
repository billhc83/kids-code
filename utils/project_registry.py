import importlib
import pkgutil
import utils

PROJECTS = {}

for _, module_name, _ in pkgutil.iter_modules(utils.__path__):
    if module_name.startswith("project_") or module_name == "block_builder_tutorial":
        try:
            module = importlib.import_module(f"utils.{module_name}")
            # Look for the new unified PROJECT dictionary
            if hasattr(module, "PROJECT"):
                project = module.PROJECT
                # If the project declares a circuit_spec, run it through the engine
                # to produce a fully-resolved circuit_definition (connections + walkthrough).
                spec = project.get("circuit_spec")
                if spec and "circuit_definition" not in project:
                    try:
                        from utils.circuit_engine import generate_circuit
                        project = dict(project)
                        project["circuit_definition"] = generate_circuit(
                            spec["meta"],
                            spec["components"],
                            spec["connections"],
                        )
                    except Exception as eng_err:
                        import traceback
                        traceback.print_exc()
                        print(f"circuit_engine error for {module_name}: {eng_err}")
                PROJECTS[module_name] = project
            # Fallback for old style modules while they are being converted
            elif hasattr(module, "META") and hasattr(module, "STEPS"):
                PROJECTS[module_name] = {
                    "meta": module.META,
                    "steps": module.STEPS,
                    "drawer": getattr(module, "DRAWER_CONTENT", {}),
                    "presets": getattr(module, "presets", {})
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error loading module {module_name}: {e}")