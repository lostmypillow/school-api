"""Reusable functions and dependencies.

Unlike other folders, I do not have a refactoring tip in mind, namely there's no equivalent present in `` at the moment of writing. Transforming `src.lib.get_class_with_seats` into a service comes to mind. *But* refactoring this part is not strictly necessary. Maybe find another place for `src.lib.deps`? Again, not strictly necessary.
"""
from .deps import deps
from .get_class_with_seats import get_class_with_seats
