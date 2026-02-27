from __future__ import annotations

import ast
import inspect
import re
import sys
from importlib import import_module
from typing import Any


class _DecoratorFinder(ast.NodeVisitor):
    """AST visitor that extracts decorator expressions per class definition."""

    def __init__(self):
        self.results: dict[str, list[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        self.results[node.name] = [ast.unparse(d) for d in node.decorator_list]
        self.generic_visit(node)


def _find_class_decorators(source: str) -> dict[str, list[str]]:
    """Return a mapping of class name -> list of decorator source strings."""
    finder = _DecoratorFinder()
    finder.visit(ast.parse(source))
    return finder.results


def _resolve_decorator(expr: str, namespace: dict[str, Any]) -> Any:
    """Best-effort resolve a decorator expression string to the actual object.

    Handles plain names (``mydecorator``), dotted names (``mod.dec``), and
    call-style decorators (``dataclass(frozen=True)``).  If the base callable
    cannot be resolved, the original string is returned as a fallback.
    """
    # Strip a trailing call – e.g. "dataclass(frozen=True)" -> "dataclass"
    base_name = re.split(r"\s*\(", expr, maxsplit=1)[0]

    parts = base_name.split(".")
    try:
        obj: Any = namespace[parts[0]]
        for part in parts[1:]:
            obj = getattr(obj, part)
        return obj
    except (KeyError, AttributeError):
        return expr  # unresolvable – keep the string representation


def build_class_graph(
    module_name: str | None = None,
) -> dict[type, dict[str, Any]]:
    """Collect every class defined in *module_name* and return a graph-like
    dict describing the class hierarchy and decorators.

    Parameters
    ----------
    module_name:
        Fully-qualified module name.  When ``None`` the caller's module is
        used.

    Returns
    -------
    dict[type, dict[str, Any]]
        A mapping of each class (the actual type object) to a dict with:

        * ``"decorators"`` – list of decorator objects (actual callables when
          resolvable, otherwise the source string).
        * ``"bases"`` – list of base classes (excluding ``object``).
        * ``"subclasses"`` – list of direct subclasses that are also defined
          in the same module.
    """
    # -- Resolve the target module ----------------------------------------
    if module_name is not None:
        module = import_module(module_name)
    else:
        caller_name = sys._getframe(1).f_globals.get("__name__", "<unknown>") # type: ignore
        module = import_module(caller_name)

    module_ns: dict[str, Any] = vars(module)

    # -- Discover classes defined in this module --------------------------
    module_classes: dict[str, type] = {
        name: obj
        for name, obj in module_ns.items()
        if isinstance(obj, type) and obj.__module__ == module.__name__
    }

    # -- Parse decorator info from source via AST -------------------------
    decorator_map = _find_class_decorators(inspect.getsource(module))

    # -- Build the graph dict ---------------------------------------------
    result: dict[type, dict[str, Any]] = {}

    for name, cls in module_classes.items():
        bases = cls.mro()[2:]  # Exclude the class itself
        bases = [b for b in bases if b is not object]  # Exclude 'object'

        decorators = [
            _resolve_decorator(d, module_ns)
            for d in decorator_map.get(name, [])
        ]

        subclasses = [
            sc for sc in cls.__subclasses__()
            if sc.__name__ in module_classes
        ]
        

        result[cls] = {
            "decorators": decorators,
            "bases": bases,
            "subclasses": subclasses,
        }

    return result

class ModuleGraph:
    """High-level view of every class defined in a single module.

    Parameters
    ----------
    module_name:
        Fully-qualified module name to inspect.  When ``None`` the module
        that *instantiated* this object is used automatically.
    """

    def __init__(self, module_name: str | None = None):
        # Resolve the caller's module here so that build_class_graph never
        # has to guess — sys._getframe(1) from *this* __init__ points at the
        # module that did ``ModuleGraph()``.
        if module_name is None:
            module_name = sys._getframe(1).f_globals.get("__name__", "__main__") # type: ignore
            
        self._module_name: str = module_name if module_name is not None else "__main__"
        self.graph: dict[type, dict[str, Any]] = build_class_graph(module_name)

    # -- basic accessors ---------------------------------------------------

    @property
    def classes(self) -> list[type]:
        """All classes discovered in the module."""
        return list(self.graph.keys())

    @property
    def class_names(self) -> list[str]:
        """Names of all discovered classes."""
        return [cls.__name__ for cls in self.graph]
    
    # -- lookup helpers ----------------------------------------------------

    def get(self, cls: type) -> dict[str, Any] | None:
        """Return the graph entry for *cls*, or ``None`` if not present."""
        return self.graph.get(cls)

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Lookup a class entry by its name string."""
        for cls, info in self.graph.items():
            if cls.__name__ == name:
                return info
        return None

    # -- hierarchy queries -------------------------------------------------

    def bases_of(self, cls: type) -> list[type]:
        """Direct bases of *cls* (excluding ``object``)."""
        results = []
        for entry_cls, info in self.graph.items():
            if cls in info["subclasses"]:
                results.append(entry_cls)
        return results

    def subclasses_of(self, cls: type) -> list[type]:
        """Direct subclasses of *cls* that are also in this module."""
        results = []
        for entry_cls, info in self.graph.items():
            if cls in info["bases"]:
                results.append(entry_cls)
        return results

    def roots(self) -> list[type]:
        """Classes that  have no bases  (tree  roots). If *internal*  is ``True``
        (the default), only consider bases that  are also  defined in the same
        module.  When ``False``, any class with no bases is considered a root."""
        return [cls for cls in self.graph if not self.bases_of(cls)]
    
    def bases(self) -> list[type]:
        """Get the unique set of all base classes (excluding ``object``) that are
        used by any class in this module."""
        return list({base for info in self.graph.values() for base in info["bases"]})
    
    def leaves(self) -> list[type]:
        """Classes that have no in-module subclasses (tree leaves). If *internal* is ``True``
        (the default), only consider subclasses that  are also  defined in the same
        module.  When ``False``, any class with no subclasses is considered a leaf."""
        return [cls for cls in self.graph if not self.subclasses_of(cls)]
    

    def ancestors(self, cls: type) -> list[type]:
        """All transitive bases of *cls* within this module (breadth-first)."""
        seen: set[type] = set()
        queue = list(self.bases_of(cls))
        result: list[type] = []
        while queue:
            current = queue.pop(0)
            if current in seen or current not in self.graph:
                continue
            seen.add(current)
            result.append(current)
            queue.extend(self.bases_of(current))
        return result

    def descendants(self, cls: type) -> list[type]:
        """All transitive subclasses of *cls* within this module (breadth-first)."""
        seen: set[type] = set()
        queue = list(self.subclasses_of(cls))
        result: list[type] = []
        while queue:
            current = queue.pop(0)
            if current in seen or current not in self.graph:
                continue
            seen.add(current)
            result.append(current)
            queue.extend(self.subclasses_of(current))
        return result

    # -- decorator queries -------------------------------------------------

    def decorators_of(self, cls: type) -> list[Any]:
        """Decorators applied to *cls*."""
        entry = self.graph.get(cls)
        return entry["decorators"] if entry else []

    def classes_with_decorator(self, decorator: Any) -> list[type]:
        """Return every class that uses *decorator*.

        *decorator* can be the actual callable **or** a string name.
        """
        matches: list[type] = []
        for cls, info in self.graph.items():
            for d in info["decorators"]:
                if d is decorator:
                    matches.append(cls)
                    break
                # Also allow matching by name string
                if isinstance(decorator, str):
                    name = d.__name__ if callable(d) else str(d)
                    if name == decorator:
                        matches.append(cls)
                        break
        return matches

    def decorated_classes(self) -> dict[type, list[Any]]:
        """Return only classes that have at least one decorator."""
        return {
            cls: info["decorators"]
            for cls, info in self.graph.items()
            if info["decorators"]
        }

    # -- representations ---------------------------------------------------

    def __repr__(self) -> str:
        cls_names = ", ".join(self.class_names)
        return f"ModuleGraph({self._module_name!r}, classes=[{cls_names}])"
    
    def __str__(self) -> str:
        lines = [f"ModuleGraph for {self._module_name}:"]
        for cls, info in self.graph.items():
            lines.append(f"  {cls.__name__}:")
            if info["bases"]:
                base_names = ", ".join(b.__name__ for b in info["bases"])
                lines.append(f"    Bases: {base_names}")
            if info["subclasses"]:
                sub_names = ", ".join(s.__name__ for s in info["subclasses"])
                lines.append(f"    Subclasses: {sub_names}")
            if info["decorators"]:
                decs: list[str] = []
                for d in info["decorators"]:
                    if callable(d):
                        decs.append(d.__name__)
                    else:
                        decs.append(str(d))
                lines.append(f"    Decorators: {', '.join(decs)}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.graph)

    def __contains__(self, cls: type) -> bool:
        return cls in self.graph

    def __iter__(self):
        return iter(self.graph)

    def __getitem__(self, cls: type) -> dict[str, Any]:
        return self.graph[cls]
