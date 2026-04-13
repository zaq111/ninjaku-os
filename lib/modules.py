import importlib
from pathlib import Path

MODULE_PATH = Path("/opt/ninjaku/modules")

def load_modules():
    loaded = {}

    for f in MODULE_PATH.glob("*.py"):
        if f.name.startswith("_"):
            continue
        if f.name == "__init__.py":
            continue

        name = f.stem
        mod = importlib.import_module(f"modules.{name}")
        loaded[name] = mod

    return loaded

def execute(module_name, command, **kwargs):
    modules = load_modules()

    if module_name not in modules:
        raise Exception(f"Module not found: {module_name}")

    mod = modules[module_name]

    if not hasattr(mod, "execute"):
        raise Exception(f"Module has no execute(): {module_name}")

    return mod.execute(command, **kwargs)
