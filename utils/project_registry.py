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
                PROJECTS[module_name] = module.PROJECT
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