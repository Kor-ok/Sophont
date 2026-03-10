from __future__ import annotations

from json import load
from os import PathLike
from typing import Any, overload

from components.applied import GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode, GenderCode
from semantics.definitions import SEMANTICS
from utils.guid import GUID


@overload
def generate(*, filepath: str | PathLike[str]) -> tuple[SpeciesCode, GUID]: ...


@overload
def generate(*, name: str, genotype: GenotypeCode) -> tuple[SpeciesCode, GUID]: ...


def generate(
    *,
    filepath: str | PathLike[str] | None = None,
    name: str | None = None,
    genotype: GenotypeCode | None = None,
) -> tuple[SpeciesCode, GUID]:
    if filepath is not None:
        if name is not None or genotype is not None:
            raise TypeError("generate() accepts either filepath or name+genotype, not both")

        with open(filepath) as f:
            species_template = load(f)

        name = species_template["name"]
        genotype = _build_genotype(species_template)

    elif name is None or genotype is None:
        raise TypeError("generate() requires either filepath=... or name=... and genotype=...")

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


def _build_genotype(species_template: dict[str, Any]) -> GenotypeCode:
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
    ) -> tuple[str, dict[str, Any]]:
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
                SEMANTICS.create(
                    type=CharacteristicCode,
                    name=template["characteristic_link"],
                )
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

    genes = tuple(
        create_gene_code(*resolve_template(gene, parsed_templates["gene_templates"]))
        for gene in species_template["gene_list"]
    )

    phenes = (
        tuple(
            create_phene_code(*resolve_template(phene, parsed_templates["phene_templates"]))
            for phene in species_template["phene_list"]
        )
        or None
    )

    return GenotypeCode(
        genes=genes,
        phenes=phenes,
    )
