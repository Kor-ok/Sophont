from __future__ import annotations

from components.primitives import KnowledgeCode, SkillCode
from semantics.definitions import SEMANTICS

if __name__ == "__main__":
    print("TESTS")
    initialised_skill_code = SkillCode(key=12, set=1, group=-99)
    initialised_knowledge_code = KnowledgeCode(
        key=6, focus=-99, associated_skill=initialised_skill_code
    )

    skill_code_semantics = SEMANTICS.of(initialised_skill_code)
    knowledge_code_semantics = SEMANTICS.of(initialised_knowledge_code)

    print("SkillCode Semantics:")
    for type_, semantics in skill_code_semantics.items():
        print(f"Type: {type_.__name__}")
        for key, value in semantics.items():
            print(f"  {key}: {value}")

    print("\nKnowledgeCode Semantics:")
    for type_, semantics in knowledge_code_semantics.items():
        print(f"Type: {type_.__name__}")
        for key, value in semantics.items():
            print(f"  {key}: {value}")
