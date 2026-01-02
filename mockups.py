from __future__ import annotations

from random import randint
from uuid import uuid4

from game.characteristic_package import CharacteristicPackage
from game.genotype import Genotype
from sophont.character import Sophont


def create_standard_genotype() -> Genotype:
    
    # Let's first create a human genotype which will be a flyweight instance shared across 
    # all human sophonts.
    human_genes_by_name = [
        "Dexterity", 
        "Strength", 
        "Intelligence", 
        "Endurance"
        ] # Purposefully disordered compared to classical Traveller UPP indices.
    
    human_phenes_by_name = [
        "Education",
        "Social Standing",
        "Psionics",
        "Sanity"
        ]

    human_genotype = Genotype.by_characteristic_names(human_genes_by_name, human_phenes_by_name)

    # print("Human Genotype Genes:")
    # print(human_genotype)

    return human_genotype

def create_detailed_genotype() -> Genotype:

    # For this demonstration, we will create a human genotype using the full
    # depth of gene specification.
    from game.characteristic import Characteristic
    from game.gene import Gene
    from game.phene import Phene

    # All genes and characteristics are flyweights, so repeated calls to
    # create the same gene or characteristic will return the same instance.

    characteristic_0 =  Characteristic.of(upp_index=0, subtype=0) # noqa: F841 # This will be Undefined because we are using the T5 mapping that starts at 1
    characteristic_1 = Characteristic.by_name("Strength") # Standard T5 characteristics are string mapped for convenience
    characteristic_2 = Characteristic.of(upp_index=2, subtype=0) # Dexterity
    characteristic_2a = Characteristic.of(upp_index=2, subtype=1) # noqa: F841 # Agility subtype which Humans do not use
    characteristic_3 = Characteristic.of(upp_index=3, subtype=0) # noqa: F841 # Endurance
    characteristic_4 = Characteristic.by_name("Intelligence") # Intelligence
    characteristic_5 = Characteristic.by_name("Education") # noqa: F841 # Education as a demonstration - not used in human genotype
    characteristic_5a = Characteristic.by_name("Instinct") # noqa: F841 # Instinct as a demonstration - not used in human genotype but can be used as a gene for other species

    # Custom characteristic for demonstration using upp_index used in T5 for Strength
    # but with a subtype of 1. Perhaps an alien variable "Density" equivalent to Strength?
    characteristic_custom = Characteristic.of(upp_index=1, subtype=1) # noqa: F841 

    gene_1 = Gene(
        characteristic=characteristic_1, 
        die_mult=1, # Standard 1d6 roll for most species, has impact on sophont size factors
        precidence=0, # Inheritability logic between genes of same characteristic
        gender_link=-1, # Inheritability based on sophont gender (-1 = none, other values point to gender indices)
        inheritance_contributors=2 # Number of parents contributing to this gene
        )

    gene_2 = Gene(characteristic_2) # Using defaults for other parameters
    gene_3 = Gene.by_characteristic_name("Endurance") # Using flyweight constructor by name
    gene_4 = Gene(characteristic=characteristic_4, precidence=1) # Intelligence as a dominant gene

    phene_1 = Phene.by_characteristic_name("Education", expression_value=5)
    phene_2 = Phene.by_characteristic_name("Social Standing", expression_value=3)
    phene_3 = Phene.by_characteristic_name("Psionics", expression_value=0) # No psionic ability
    phene_4 = Phene.by_characteristic_name("Sanity", expression_value=8)

    gene_collection = [gene_1, gene_2, gene_3, gene_4]
    phene_collection = [phene_1, phene_2, phene_3, phene_4]

    genotype = Genotype.of([*gene_collection], [*phene_collection]) # Purposefully disordered input

    print("Detailed Genotype Genes:")
    print(genotype)

    return genotype

def create_unborn_sophont() -> Sophont:
    human_genotype = create_standard_genotype()

    # Now create an unborn sophont (age_seconds=-1) with that genotype.
    sophont = Sophont(species_genotype=human_genotype)

    # print("Sophont Created:")
    # print(sophont)

    return sophont

def apply_inherited_packages(sophont: Sophont) -> Sophont:
    # Create "Virtual Parents" uuids 
    # (for this demo we're assuming two parents, but we can derive parentage
    #  from gene.inheritance_contributors too i.e. T5 DNA Rules; 2NA, 3NA, etc).
    # Note that self uuid can be used for cloning scenarios.
    parent_1_uuid = uuid4().bytes
    parent_2_uuid = uuid4().bytes

    # Fetch phenotype from the Sophont
    phenotype = sophont.epigenetic_profile.genotype.get_phenotype()

    BASE_DIE_VALUE = 6  # nD6 T5 rules

    from game.characteristic_package import CharacteristicPackage
    from game.gene import Gene
    from game.phene import Phene

    def gene_inheritance_level(gene: Gene) -> int:
        # Minimal demo logic: interpret gene.die_mult as "N dice" and roll Nd6.
        dice = max(1, int(getattr(gene, "die_mult", 1)))
        return sum(randint(1, BASE_DIE_VALUE) for _ in range(dice))

    def phene_level(phene: Phene, is_expressed_gene = False) -> int:
        expr_value = getattr(phene, "expression_value", -1)
        if expr_value > 0:
            return expr_value
        if not is_expressed_gene:
            return randint(1, BASE_DIE_VALUE) + randint(1, BASE_DIE_VALUE)
        else:
            # Use the associated gene.die_mult as "N dice" and roll for phene level.
            associated_gene = Gene.by_characteristic_name(phene.characteristic.get_name())
            dice = max(1, int(getattr(associated_gene, "die_mult", 1)))
            return sum(randint(1, BASE_DIE_VALUE) for _ in range(dice))

    # The is_grafted flag of a phene can allow for the use of donor/provider uuid scenarios.
    # A Phene can therefore supersede another based on some logic.
    # For this demonstration we:
    # - always create a package for an inherited Gene (if present)
    # - create a package for a Phene if present (derived or explicit)
    # This keeps the data available for downstream collation logic to reason about types.
    birth_seconds = 0
    memo_base = [
        "Inherited at Birth",
        f"parent_1_uuid={parent_1_uuid!r}",
        f"parent_2_uuid={parent_2_uuid!r}",
    ]

    for upp_index, (gene, phene) in phenotype.items():
        if gene is not None:
            gene_pkg = CharacteristicPackage(item=gene, level=gene_inheritance_level(gene), context="Birth")
            sophont.epigenetic_profile.insert_package_acquired(
                package=gene_pkg,
                age_acquired_seconds=birth_seconds,
                memo=[*memo_base, f"upp_index={upp_index}", "item_type=Gene"],
            )

        if phene is not None and gene is not None:
            phene_pkg = CharacteristicPackage(item=phene, level=phene_level(phene, is_expressed_gene=True), context="Birth")
            sophont.epigenetic_profile.insert_package_acquired(
                package=phene_pkg,
                age_acquired_seconds=birth_seconds,
                memo=[*memo_base, f"upp_index={upp_index}", "item_type=Phene"],
            )

        if phene is not None and gene is None:
            phene_pkg = CharacteristicPackage(item=phene, level=phene_level(phene, is_expressed_gene=False), context="Birth")
            sophont.epigenetic_profile.insert_package_acquired(
                package=phene_pkg,
                age_acquired_seconds=birth_seconds,
                memo=[*memo_base, f"upp_index={upp_index}", "item_type=Phene"],
            )

    sophont.epigenetic_profile.update_collation()
    return sophont

# region: PLACEHOLDERS
# def define_species() -> None:
#     human_genotype = create_standard_genotype()
#     human_species_id = uuid4().bytes
#     human_species = Species(genotype=human_genotype, uuid=human_species_id)

#     neanderthal_genotype = create_standard_genotype()
#     neanderthal_species_id = uuid4().bytes
#     neanderthal_species = Species(genotype=neanderthal_genotype, uuid=neanderthal_species_id)

#     vargr_genes_by_name = [
#         "Strength",
#         "Dexterity",
#         "Intelligence",
#         "Endurance",
#         "Charisma" # For this demo, we add Charisma to differentiate from humans
#         ]
#     vargr_genotype = Genotype.by_gene_characteristic_names(vargr_genes_by_name)
#     vargr_species_id = uuid4().bytes
#     vargr_species = Species(genotype=vargr_genotype, uuid=vargr_species_id)

#     from game.mappings.world_id import EARTH_WORLD_ID, KARGOL_WORLD_ID, VLAND_WORLD_ID
#     tree_of_life_earth = TreeOfLifeOrigin(world_id=EARTH_WORLD_ID)
#     tree_of_life_vland = TreeOfLifeOrigin(world_id=VLAND_WORLD_ID)
#     tree_of_life_kargol = TreeOfLifeOrigin(world_id=KARGOL_WORLD_ID)
    
#     # For Humans, the Genus is 8 levels deep in the Tree of Life from the root.
#     human_path = [uuid4().bytes for _ in range(8)]
#     tree_of_life_earth.add_node(human_path)

#     # Get uuid of the human genus node
#     human_genus_uuid = human_path[-1]

#     human_genus = Genus(
#         species_collection=[human_species, neanderthal_species],
#         tree_of_life_node_uuid=human_genus_uuid
#     )

#     # The Vilani of the World of Vland are a transplanted human OF THE SAME SPECIES.
#     vilani_path = human_genus.tree_of_life_node_uuid
#     tree_of_life_vland.add_node([vilani_path]) # This creates a direct link to the
#                                                # human genus node, maintaining species identity,
#                                                # but identifying the world transplantation.

#     # The Kargol of the World of Kargol are Neanderthals transplanted to that world.
#     kargol_ancestor_path = human_genus.tree_of_life_node_uuid
#     # They then diverged from Neanderthals to become a distinct species
#     kargol_genotype = create_standard_genotype()
#     kargol_species_id = uuid4().bytes
#     kargol_species = Species(genotype=kargol_genotype, uuid=kargol_species_id)
#     # New node for Kargol species
#     kargol_transplanted_genus_id = uuid4().bytes

#     tree_of_life_kargol.add_node([kargol_ancestor_path, kargol_transplanted_genus_id]) # This creates a direct link to the
#                                                 # human genus node, identifying the world transplantation,
#                                                 # then adds a new node for the transplanted genus.
#     kargol_transplanted_genus = Genus(
#         species_collection=[kargol_species],
#         tree_of_life_node_uuid=kargol_transplanted_genus_id
#     )

#     # For Vargr, they differentiate from Humans at level 4
#     vargr_ancestor_path = human_path[:4] + [uuid4().bytes for _ in range(4)]
#     tree_of_life_earth.add_node(vargr_ancestor_path)

#     vargr_ancestor_genus_uuid = vargr_ancestor_path[-1]

#     # They then diverged to become their own genus
#     vargr_genus = Genus(
#         species_collection=[vargr_species],
#         tree_of_life_node_uuid = uuid4().bytes
#     )

#     tree_of_life_earth.display()
# endregion: PLACEHOLDERS
    
def colorise_stdout_hex_references(text: str) -> str:
    """Colorize 0x-prefixed hex references using deterministic, ordered hues.

    - Unique matches are sorted numerically (lowest to highest).
    - Colors are assigned across the hue spectrum (truecolor) so relative
      ordering holds meaning.
    - Avoids white/black by using high saturation and mid-high brightness.
    """

    import colorsys
    import re

    HEX_PATTERN = r"0x[0-9a-fA-F]+"
    COLOR_RESET = "\033[0m"

    matches = re.findall(HEX_PATTERN, text)
    if not matches:
        return text

    def hex_to_int(hex_str: str) -> int:
        return int(hex_str, 16)

    unique_sorted = sorted(set(matches), key=hex_to_int)
    count = len(unique_sorted)

    # Count occurrences per token so we can dim unique references and brighten
    # repeated references.
    match_counts: dict[str, int] = {}
    for token in matches:
        match_counts[token] = match_counts.get(token, 0) + 1

    # Spread hues across the full circle. Use fixed saturation/value to avoid
    # grayscale (white/black) while keeping the colors legible.
    saturation = 0.85
    value_for_unique_instances_exist_only = 0.25
    value_for_multiple_instances_exist = 0.95

    def ansi_truecolor_fg(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"
    
    def value_for_token(token: str) -> float:
        return (
            value_for_unique_instances_exist_only
            if match_counts.get(token, 0) <= 1
            else value_for_multiple_instances_exist
        )

    color_map: dict[str, str] = {}
    for index, token in enumerate(unique_sorted):
        # Avoid duplicating the starting color at the end when count > 1.
        hue_deg = (index * (360.0 / count)) if count > 1 else 120.0
        value = value_for_token(token)
        r_f, g_f, b_f = colorsys.hsv_to_rgb(hue_deg / 360.0, saturation, value)
        r = int(round(r_f * 220))
        g = int(round(g_f * 255))
        b = int(round(b_f * 220))
        color_map[token] = ansi_truecolor_fg(r, g, b)

    def replace_with_color(match: re.Match) -> str:
        token = match.group(0)
        return f"{color_map[token]}{token}{COLOR_RESET}"

    return re.sub(HEX_PATTERN, replace_with_color, text)

def colorise_stdout_by_keywords(text: str) -> str:

    match_keywords_including_aliases = [
        ["Genes", "Gene"],
        ["Phenes", "Phene"],
    ]

    # For each keyword group, assign a distinct random color.
    import random
    import re
    COLOR_RESET = "\033[0m"
    color_map: list[tuple[tuple[str, ...], str]] = []
    for keyword_group in match_keywords_including_aliases:
        r = random.randint(100, 220)
        g = random.randint(100, 255)
        b = random.randint(100, 220)
        ansi_truecolor_fg = f"\033[38;2;{r};{g};{b}m"
        color_map.append((tuple(keyword_group), ansi_truecolor_fg))
    
    def replace_with_color(match: re.Match) -> str:
        token = match.group(0)
        for keyword_group, color_code in color_map:
            if token in keyword_group:
                return f"{color_code}{token}{COLOR_RESET}"
        return token  # Should not happen
    pattern = r"\b(" + "|".join(kw for group in match_keywords_including_aliases for kw in group) + r")\b"
    return re.sub(pattern, replace_with_color, text)

def display(object: object) -> str:
    hex_coloured = colorise_stdout_hex_references(str(object))
    keyword_coloured = colorise_stdout_by_keywords(hex_coloured)
    return keyword_coloured

def show_characteristics_collation_summary(sophont: Sophont) -> None:
    characteristics_collation = sophont.epigenetic_profile.characteristics_collation
    if characteristics_collation is not None:
        display_lines = []
        for unique_applied in characteristics_collation:
            characteristic_name = unique_applied.item.get_name()  # Force name resolution for display purposes
            computed_level = unique_applied.computed_level
            display_lines.append(f"{characteristic_name}: {computed_level}")
        display_text = "\n".join(display_lines)
        print(display_text)

def make_characteristic_package(contributor_uuid: bytes) -> CharacteristicPackage:
    from game.phene import Phene

    characteristic_name = "Dexterity"
    expression_value = 1
    # contributor_uuid = uuid4().bytes
    dexterity_characteristic = Phene.by_characteristic_name(characteristic_name, expression_value=expression_value, contributor_uuid=contributor_uuid)

    level = 2
    context = "Adolescent Training Program"

    dexterity_package = CharacteristicPackage(item=dexterity_characteristic, level=level, context=context)
    return dexterity_package

if __name__ == "__main__":
    print("\033c", end="")
    
    sophont = create_unborn_sophont()
    sophont = apply_inherited_packages(sophont)
    show_characteristics_collation_summary(sophont)

    # Let's now make a new package that modifies Dexterity by +2 at age 16 years (504576000 seconds).
    characteristic_contributor_uuid = uuid4().bytes
    dexterity_package = make_characteristic_package(characteristic_contributor_uuid)
    print("\nNew Package Created:")
    print(display(dexterity_package))

    add_characteristic_at_age_seconds = 16 * 31536000  # 16 years in seconds

    sophont.epigenetic_profile.insert_package_acquired(
        package=dexterity_package,
        age_acquired_seconds=add_characteristic_at_age_seconds,
        memo=["Adolescent Training Program Dexterity Boost"],
        trigger_collation=True
    )
    show_characteristics_collation_summary(sophont)

    # Now let's make two aptitude packages, one Skill and one Knowledge.
    from game.aptitude_package import AptitudePackage
    from game.skill import Skill

    aptitude_contributor_uuid = uuid4().bytes

    skill_name = "Vacc Suit" # Vacc Suit skill code = 34
    vacc_suit_skill = Skill.by_skill_name(skill_name)

    vacc_suit_skill_package = AptitudePackage(
        item=vacc_suit_skill, 
        level=1, 
        context=f"Basic Training Course: {str(aptitude_contributor_uuid)}")
    
    print("\nNew Aptitude Package Created:")
    print(display(vacc_suit_skill_package))

    skill_name = "Language"
    language_name = "Anglic"
    language_skill = Skill.of(21)  # Language skill code
    language_knowledge = language_skill.apply_knowledge(knowledge_code=66, focus=language_name)  # Anglic Knowledge
    language_knowledge_package = AptitudePackage(
        item=language_knowledge,
        level=2,
        context=f"Secondary Education Course: {str(aptitude_contributor_uuid)}"
    )
    print("\nNew Knowledge Package Created:")
    print(display(language_knowledge_package))

    added_aptitude_at_age_seconds = 18 * 31536000  # 18 years in seconds

    sophont.aptitudes.insert_package_acquired(
        package=vacc_suit_skill_package,
        age_acquired_seconds=added_aptitude_at_age_seconds,
        memo=["Basic Vacc Suit Skill Training", str(aptitude_contributor_uuid)],
        trigger_collation=False # Default is False
    )
    sophont.aptitudes.insert_package_acquired(
        package=language_knowledge_package,
        age_acquired_seconds=added_aptitude_at_age_seconds,
        memo=["Secondary Education Language Knowledge", str(aptitude_contributor_uuid)]
    )

    sophont.aptitudes.update_collation() # Manual update for this demonstration

    aptitude_collation = sophont.aptitudes.aptitude_collation
    if aptitude_collation is not None:
        print("\nAptitudes Collation Summary:")
        display_lines = []
        for unique_applied in aptitude_collation:
            aptitude_item = unique_applied.item
            computed_level = unique_applied.computed_level
            display_lines.append(f"{aptitude_item}: {computed_level}")
        display_text = "\n".join(display_lines)
        print(display_text)