from __future__ import annotations

from components import component
from components.base import Primitive
from utils.inspection import ModuleGraph


@component
class CharacteristicCode(Primitive):
    upp_position: int
    subtype: int
    """0 is default, i.e. upp_position 1 of subtype 0 is strength"""
    category: int
    """1 physical, 2 mental, 3 social, 4 obscure"""


@component
class SkillCode(Primitive):
    key: int
    """code for the skill, i.e. 21 language"""
    set: int
    """1 general, 2 default, 3 talents, 4 personals, 5 intuitions"""
    group: int
    """1 base, 2 starship skills, 3 trades, 4 arts, 5 soldier skills"""


@component
class KnowledgeCode(Primitive):
    key: int
    """code for the knowledge, i.e. 57 sophontology"""
    focus: int
    """lookup code for the name of the specialisation i.e. 'anglic' as part of a language knowledge """
    associated_skill: SkillCode


@component
class GenderCode(Primitive):
    key: int
    """-1 unspecified, 0 solo, 1 female, 2 male, 3 neuter ... etc."""


MODULE_GRAPH = ModuleGraph()