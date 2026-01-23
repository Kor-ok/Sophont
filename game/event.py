from __future__ import annotations

import operator as op
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import IntFlag, auto
from typing import Union

from game.package import AttributePackage
from game.uid.guid import GUID, NameSpaces


class LogicFlag(IntFlag):
    """For authoring the conditional constraints for player character's package selections for the authored event."""
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto()
    NAND = auto()
    NOR = auto()
    XNOR = auto()

_LOGIC_OPERATORS: dict[LogicFlag, Callable[[bool, bool], bool]] = {
    LogicFlag.AND: op.and_,
    LogicFlag.OR: op.or_,
    LogicFlag.XOR: op.xor,
    LogicFlag.NAND: lambda a, b: not (a and b),
    LogicFlag.NOR: lambda a, b: not (a or b),
    LogicFlag.XNOR: lambda a, b: not (a ^ b),
}


_BINARY_OPERATORS: tuple[LogicFlag, ...] = (
    LogicFlag.AND,
    LogicFlag.OR,
    LogicFlag.XOR,
    LogicFlag.NAND,
    LogicFlag.NOR,
    LogicFlag.XNOR,
)


def _operator_part(flag: LogicFlag) -> Union[LogicFlag, None]:
    """Extract the binary operator portion of a possibly-combined flag."""
    for op_flag in _BINARY_OPERATORS:
        if flag & op_flag:
            return op_flag
    return None


@dataclass(frozen=True)
class AuthoredConstraint:
    """A single authored constraint term used to gate presenting a ChoiceGroup.

    `flag` may include `LogicFlag.NOT` (unary negation of the package predicate),
    plus one binary operator flag.
    """

    flag: LogicFlag
    package: AttributePackage

class PackageRegistry:
    def __init__(self) -> None:
        self._registry: list[tuple[LogicFlag, AttributePackage]] = []

    def register_package(
            self,
            flag: LogicFlag,
            package: AttributePackage
    ) -> None:
        self._registry.append((flag, package))

    def iter_packages(self) -> Iterable[tuple[LogicFlag, AttributePackage]]:
        return tuple(self._registry)

class ChoiceGroup:
    def __init__(
            self,
            label: str,
            valid_flags: LogicFlag,
            max_choices: int,
            registry: Union[PackageRegistry, None] = None,
            presentation_constraints: Iterable[AuthoredConstraint] = (),
    ) -> None:
        self.label = label
        self.valid_flags = valid_flags
        self.max_choices = max_choices
        self.registry = registry if registry is not None else PackageRegistry()
        self.presentation_constraints: list[AuthoredConstraint] = list(presentation_constraints)

    def add_presentation_constraint(self, flag: LogicFlag, package: AttributePackage) -> None:
        self.presentation_constraints.append(AuthoredConstraint(flag=flag, package=package))

    def is_presentable(self, selected_packages: Iterable[AttributePackage] = ()) -> bool:
        """Return True if this ChoiceGroup should be shown, given selected/owned packages.

        Constraints are evaluated left-to-right.
        - Each term's predicate is `package in selected_packages`, optionally negated via `LogicFlag.NOT`.
        - Subsequent terms are combined using the binary operator encoded in the term's flag.
        - The first term seeds the expression (its binary operator, if present, is ignored).
        """

        constraints = self.presentation_constraints
        if not constraints:
            return True

        selected_set = set(selected_packages)

        def _term_value(term: AuthoredConstraint) -> bool:
            value = term.package in selected_set
            if term.flag & LogicFlag.NOT:
                value = not value
            return value

        result: bool | None = None
        for index, term in enumerate(constraints):
            term_value = _term_value(term)
            if index == 0:
                result = term_value
                continue

            operator_flag = _operator_part(term.flag)
            if operator_flag is None:
                raise ValueError(
                    f"Constraint term missing binary operator: {term.flag!r}"
                )
            operator_fn = _LOGIC_OPERATORS.get(operator_flag)
            if operator_fn is None:
                raise ValueError(f"Unsupported operator: {operator_flag!r}")

            result = operator_fn(bool(result), term_value)

        return bool(result)

    def available_packages(self):
        return [
            (flag, pkg)
            for flag, pkg in self.registry.iter_packages()
            if (_operator_part(flag) or flag) & self.valid_flags
        ]
        
class EventOutcome:
    def __init__(
            self,
            label: str
    ) -> None:
        self.label = label
        self.choice_groups: list[ChoiceGroup] = []

    def add_choice_group(
            self,
            choice_group: ChoiceGroup
    ) -> None:
        self.choice_groups.append(choice_group)

class Event:
    def __init__(
            self,
            name: str
    ) -> None:
        self.name = name
        self.uid: int = GUID.generate(NameSpaces.Entity.EVENTS, NameSpaces.Owner.PLAYER)
        self.outcomes: list[EventOutcome] = []
        self.registry: PackageRegistry = PackageRegistry()

    def add_outcome(
            self,
            outcome: EventOutcome
    ) -> None:
        self.outcomes.append(outcome)

    def present_event(self, selected_packages: Iterable[AttributePackage] = ()) -> None:
        print(f"Event: {self.name} (ID: {self.uid})")
        for outcome in self.outcomes:
            print(f" Outcome: {outcome.label}")
            for choice_group in outcome.choice_groups:
                if not choice_group.is_presentable(selected_packages):
                    continue
                print(f"  Choice Group: {choice_group.label} (Max Choices: {choice_group.max_choices})")
                for flag, pkg in choice_group.available_packages():
                    print(f"   Package: {pkg} with LogicFlag: {flag.name}")