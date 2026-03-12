from __future__ import annotations

from collections import defaultdict, deque
from itertools import chain
from random import choice, randint
from typing import Union

from rich import print
from sortedcontainers import SortedKeyList

from components.applied import UPP, GeneCode, PheneCode, SpeciesCode
from components.primitives import GenderCode
from utils.guid import GUID


def _roll_inheritance_values(xene: Union[GeneCode, PheneCode]) -> tuple[int, ...]:
    die_mult = xene.die_mult
    return tuple(randint(1, 6) for _ in range(die_mult))


class InheritanceProcessor:
    """Processes inheritance logic for species and entities, applying genetic traits and calculating derived attributes."""

    @staticmethod
    def species_to_upps(sophont_guid: GUID, species: SpeciesCode) -> tuple[SortedKeyList[UPP], dict[GUID, list[Union[GenderCode, GeneCode, PheneCode]]]]:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Populate Progenitors
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        Infer number of progenitors from max contributor pool size across all genes
        """
        max_contributor_pool_size = max(
            (gene.contributor_pool_size for gene in species.genotype.genes),
            default=0,
        )

        progenitor_guids = {}
        for i in range(max_contributor_pool_size):
            ancestor_guid = GUID.generate(
                ns1=GUID.Entity.CHARACTERS,
                ns2=GUID.Owner.NPC,
                name=(f"{sophont_guid.lookup_name()}.PROGENITOR.{i}"),
            )
            progenitor_guids[ancestor_guid] = []

        # Apply each gender to each progenitor and register in GUID system
        for guid, gender in zip(progenitor_guids.keys(), species.genders):
            GUID.add_instance(guid, gender)
            progenitor_guids[guid].append(gender)

        gene_pool = list(species.genotype.genes)

        # Build progenitor lookup by gender
        progenitors_by_gender: dict[GenderCode, deque[GUID]] = defaultdict(deque)

        for guid, gender in zip(progenitor_guids.keys(), species.genders):
            GUID.add_instance(guid, gender)
            progenitor_guids[guid].append(gender)
            progenitors_by_gender[gender].append(guid)

        remaining_genes: list[GeneCode] = []

        for genecode in species.genotype.genes:
            gender = genecode.gender_link

            if gender is None:
                remaining_genes.append(genecode)
                continue

            candidate_guids = progenitors_by_gender.get(gender)
            if not candidate_guids:
                remaining_genes.append(genecode)
                continue

            guid = candidate_guids[0]
            GUID.add_instance(guid, genecode)
            progenitor_guids[guid].append(genecode)

            # Optional: rotate if multiple progenitors share the same gender
            candidate_guids.rotate(-1)

        gene_pool = remaining_genes

        # Of the remaining genes in the gene pool, match the characteristic_link to the characteristic of the genes in the progenitor_guids, and assign to the same progenitor
        for genecode in gene_pool:
            char_link = genecode.characteristic_link
            if char_link is None:
                continue

            matched = False
            for guid, traits in progenitor_guids.items():
                for trait in traits:
                    if isinstance(trait, GeneCode) and trait.characteristic == char_link:
                        GUID.add_instance(guid, genecode)
                        progenitor_guids[guid].append(genecode)
                        # Optional: could rotate here as well if multiple genes link to the same characteristic
                        # progenitors_by_gender[genecode.gender_link].rotate(-1)
                        gene_pool.remove(genecode)
                        matched = True
                        break
                if matched:
                    break

        # Randomly assign remaining genes to any progenitor
        for genecode in gene_pool:
            guid = choice(list(progenitor_guids.keys()))
            GUID.add_instance(guid, genecode)
            progenitor_guids[guid].append(genecode)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # UPP SortedKeyList Construction
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        upp_list: SortedKeyList[UPP] = SortedKeyList(  # pyright: ignore[reportInvalidTypeArguments]
            (
                UPP(xene=xene, rolls=_roll_inheritance_values(xene))
                for xene in chain(
                    *progenitor_guids.values(),
                    species.genotype.phenes or (),
                )
                if isinstance(
                    xene, (GeneCode, PheneCode)
                )  # if isinstance(gene, (GeneCode, PheneCode))
            ),
            key=lambda upp: upp.xene.characteristic.upp_position,
        )

        return upp_list, progenitor_guids
