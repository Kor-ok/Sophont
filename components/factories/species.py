from __future__ import annotations

from typing import Any

from components.applied import GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode, GenderCode
from semantics.definitions import SEMANTICS
from utils.guid import GUID


def parse_species_template(filepath: str) -> tuple[SpeciesCode, GUID]:
    from json import load

    with open(filepath) as f:
        species_template = load(f)

    parsed_templates = {
        "gene_templates": {
            int(id): template
            for gene_template in species_template["gene_templates"]
            for id, template in gene_template.items()
        },
        "phene_templates": {
            int(id): template
            for phene_template in species_template["phene_templates"]
            for id, template in phene_template.items()
        },
    }

    def resolve_template(
        item: dict[str, Any], templates: dict[int, dict[str, Any]]
    ) -> tuple[str, dict[Any, Any] | dict[str, Any]]:
        id, value = next(iter(item.items()))
        template = value if isinstance(value, dict) else templates[int(value)]
        return id, template

    def create_gene_code(id: str, template: dict[str, Any]) -> GeneCode:
        return GeneCode(
            characteristic=SEMANTICS.create(type=CharacteristicCode, name=id),
            precedence=template["precedence"],
            die_mult=template["die_mult"],
            gender_link=(
                SEMANTICS.create(type=GenderCode, name=template["gender_link"])
                if template["gender_link"] is not None
                else None
            ),
            characteristic_link=(
                SEMANTICS.create(type=CharacteristicCode, name=template["characteristic_link"])
                if template["characteristic_link"] is not None
                else None
            ),
            contributor_pool_size=template["contributor_pool_size"],
        )

    def create_phene_code(id: str, template: dict[str, Any]) -> PheneCode:
        return PheneCode(
            characteristic=SEMANTICS.create(type=CharacteristicCode, name=id),
            is_grafted=template["is_grafted"],
            precedence=template["precedence"],
            die_mult=template["die_mult"],
        )

    genes: tuple[GeneCode, ...] = tuple(
        create_gene_code(*resolve_template(gene, parsed_templates["gene_templates"]))
        for gene in species_template["gene_list"]
    )

    phenes: tuple[PheneCode, ...] | None = tuple(
        create_phene_code(*resolve_template(phene, parsed_templates["phene_templates"]))
        for phene in species_template["phene_list"]
    )

    if not phenes:
        phenes = None

    genotype = GenotypeCode(
        genes=genes,
        phenes=phenes,
    )

    species, guid = generate_species(
        name=species_template["name"],
        genotype=genotype,
    )

    return species, guid


def generate_species(
    name: str,
    genotype: GenotypeCode,
) -> tuple[SpeciesCode, GUID]:
    species = SpeciesCode(
        genotype=genotype,
    )

    guid = GUID.generate(
        ns1=GUID.Entity.SPECIES,
        ns2=GUID.Owner.ENV,
        name=name,
        instance=species,
    )

    return species, guid
