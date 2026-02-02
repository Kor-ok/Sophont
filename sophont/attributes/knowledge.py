from __future__ import annotations

from game.primitives.data import CanonicalStrKey, FullCode, StringAliases
from game.primitives.set import ATTRIBUTES
from sophont.attributes.base import AppliedAttributeBase


class Knowledge(AppliedAttributeBase[FullCode]):
    """Immutable flyweight defining knowledges.

    Implements: FullCodeAttribute protocol (base_code", associated_skill, focus)
    """
    __slots__ = ("code",)
    code: FullCode
    Key = FullCode

    def __new__(cls, code: FullCode = (-99, -99, -99)) -> Knowledge:
        cached, found = cls._cache_get_or_create(code)
        if found:
            return cached  # type: ignore[return-value]

        self = super().__new__(cls)
        self._set_attr("code", code)
        cls._cache_set(code, self)
        return self
    
    @classmethod
    def by_name(cls, name: str) -> Knowledge:
        full_code = ATTRIBUTES.knowledges.get_full_code(name)
        return cls(full_code)
    @classmethod
    def by_code(cls, code: FullCode) -> Knowledge:
        return cls(code)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        return ATTRIBUTES.knowledges.get_aliases(self.code)
    
    def get_code(self) -> FullCode:
        return self.code