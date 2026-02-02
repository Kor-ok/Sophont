from __future__ import annotations

from game.primitives.data import CanonicalStrKey, FullCode, StringAliases
from game.primitives.set import ATTRIBUTES
from sophont.attributes.base import AppliedAttributeBase


class Skill(AppliedAttributeBase[FullCode]):
    """Immutable flyweight defining skills.

    Implements: FullCodeAttribute protocol (master_category, sub_category, base_code)
    where master_category identifies groups like "trades", "starship skills" etc., sub_category
    defines conditional bags of skills like "default", "personals", "intuitions" etc.,
    and base_code identifies the specific skill within those categories i.e. "language", "pilot", etc.
    """

    __slots__ = ("code",)
    code: FullCode
    Key = FullCode

    def __new__(cls, code: FullCode = (-99, -99, -99)) -> Skill:
        cached, found = cls._cache_get_or_create(code)
        if found:
            return cached  # type: ignore[return-value]

        self = super().__new__(cls)
        self._set_attr("code", code)
        cls._cache_set(code, self)
        return self
    
    @classmethod
    def by_name(cls, name: str) -> Skill:
        full_code = ATTRIBUTES.skills.get_full_code(name)
        return cls(full_code)
    
    @classmethod
    def by_code(cls, code: FullCode) -> Skill:
        return cls(code)
    
    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        return ATTRIBUTES.skills.get_aliases(self.code)
    
    def get_code(self) -> FullCode:
        return self.code
