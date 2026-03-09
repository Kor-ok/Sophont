from __future__ import annotations

from dataclasses import replace
from random import choice, randint
from typing import Any, Optional

from rich import print
from rich.pretty import pprint

from components.applied import UPP, GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode, GenderCode
from semantics.definitions import SEMANTICS
from utils.guid import GUID


def _get_max_contributor_pool_size(species: SpeciesCode) -> int:
    max_pool_size = 0
    for gene in species.genotype.genes:
        if gene.contributor_pool_size > max_pool_size:
            max_pool_size = gene.contributor_pool_size

    return max_pool_size


def _get_gender_links(species: SpeciesCode) -> set[GenderCode]:
    gender_links: set[GenderCode] = set()
    for gene in species.genotype.genes:
        if gene.gender_link is not None:
            gender_links.add(gene.gender_link)

    return gender_links


def _get_characteristic_links(species: SpeciesCode) -> set[CharacteristicCode]:
    characteristic_links: set[CharacteristicCode] = set()
    for gene in species.genotype.genes:
        if gene.characteristic_link is not None:
            characteristic_links.add(gene.characteristic_link)

    return characteristic_links


def _generate_inheritance_guids(
    count: int,
    gender_links: Optional[set[GenderCode]],
    characteristic_links: Optional[set[CharacteristicCode]],
) -> Any:
    gender_pool = list(gender_links) if gender_links else None
    characteristic_pool = list(characteristic_links) if characteristic_links else None

    guids = {}
    for i in range(count):
        guid = GUID.generate(
            ns1=GUID.NameSpaces.Entity.CHARACTERS,
            ns2=GUID.NameSpaces.Owner.NPC,
            name=f"Contributor_{i + 1}",
        )
        guids[guid] = {}
        if gender_links and gender_pool:
            random_gender = choice(list(gender_pool))
            guids[guid]["gender"] = random_gender
            gender_pool.remove(random_gender)
        if characteristic_links and characteristic_pool:
            random_characteristic = choice(list(characteristic_pool))
            guids[guid]["characteristic"] = random_characteristic
            characteristic_pool.remove(random_characteristic)

    return guids


class InheritanceProcessor:
    """Processes inheritance logic for species and entities, applying genetic traits and calculating derived attributes."""

    @staticmethod
    def species_to_genotype(species: SpeciesCode) -> GenotypeCode:
        """Extracts the genotype from a given species."""
        pool_size = _get_max_contributor_pool_size(species)
        gender_links = _get_gender_links(species)
        characteristic_links = _get_characteristic_links(species)

        contributor_guids = _generate_inheritance_guids(
            pool_size, gender_links, characteristic_links
        )

        pprint(contributor_guids, expand_all=True)

        print()

        genes: tuple[GeneCode, ...] = ()

        for i, gene in enumerate(species.genotype.genes):
            if gene.gender_link is not None:
                # Find a contributor with the matching gender
                matching_contributors = [
                    guid
                    for guid, info in contributor_guids.items()
                    if info.get("gender") == gene.gender_link
                ]
                if matching_contributors:
                    contributor_guid = choice(matching_contributors)
                else:
                    contributor_guid = choice(list(contributor_guids.keys()))

            gene = replace(gene, contributor_guid=contributor_guid)

            genes += (gene,)

        genotype = replace(species.genotype, genes=genes)

        return genotype
