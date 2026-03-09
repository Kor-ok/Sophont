from __future__ import annotations

from rich.pretty import pprint

from components.primitives import CharacteristicCode, KnowledgeCode, SkillCode
from semantics.definitions import SEMANTICS


def test_semantics_extraction() -> None:
    initialised_skill_code = SkillCode(key=12, set=1, group=-99)
    initialised_knowledge_code = KnowledgeCode(
        key=6, focus=-99, associated_skill=initialised_skill_code
    )
    initialised_characteristic_code = CharacteristicCode(upp_position=1, subtype=0, category=1)

    skill_code_semantics = initialised_skill_code.semantics
    knowledge_code_semantics = initialised_knowledge_code.semantics
    characteristic_code_semantics = initialised_characteristic_code.semantics

    print("SkillCode semantics:")
    pprint(skill_code_semantics, indent_guides=True)
    print()
    print("KnowledgeCode semantics:")
    pprint(knowledge_code_semantics, indent_guides=True)
    print()
    print("CharacteristicCode semantics:")
    pprint(characteristic_code_semantics, indent_guides=True)

    code = SkillCode(key=12, set=1, group=-99)

    # New — filter to a specific component type
    semantics_data_of_type = code.semantics.of_type(SkillCode).canonical  # ('Skill-name',)

    # New — get all alias lists
    semantics_data_aliases = code.semantics.aliases  # (('alias1', 'alias2'), ...)

    # New — access per-member semantics
    semantics_data_members = code.semantics.members  # {SkillCode: {'SkillCode.set': {...}, ...}}

    # New — drill into a specific member
    semantics_data_member = code.semantics.member(
        "SkillCode.set"
    )  # {'value': 1, 'canonical': 'Set-name', 'aliases': [...]}
    semantics_data_member_canonical = code.semantics.member_canonical("SkillCode.set")  # 'Set-name'

    # New — which types are present?
    semantics_data_types = code.semantics.types  # (SkillCode, KnowledgeCode)

    print("\nExtracted semantics data:")
    print("Semantics of type SkillCode:")
    pprint(semantics_data_of_type, indent_guides=True)
    print("\nAll alias lists:")
    pprint(semantics_data_aliases, indent_guides=True)
    print("\nPer-member semantics:")
    pprint(semantics_data_members, indent_guides=True)
    print("\nSemantics of member 'SkillCode.set':")
    pprint(semantics_data_member, indent_guides=True)
    print("\nCanonical semantics of member 'SkillCode.set':")
    pprint(semantics_data_member_canonical, indent_guides=True)
    print("\nTypes present in semantics:")
    pprint(semantics_data_types, indent_guides=True)


if __name__ == "__main__":
    index = SEMANTICS.canonical_definitions.by_alias_for_signature
    print("Index of canonical definitions by alias for signature:")
    pprint(index, indent_guides=True)
    print()

    result = SEMANTICS.create(type=KnowledgeCode, name="rider")
    print("Result of SEMANTICS.create(...):")
    pprint(result, indent_guides=True)
    print()
