from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import replace
from itertools import chain
from pprint import pprint
from random import choice, randint
from typing import Any, Optional, Union

from rich import print
from sortedcontainers import SortedKeyList

from components.applied import UPP, GeneCode, GenotypeCode, PheneCode, SpeciesCode
from components.primitives import CharacteristicCode, GenderCode
from utils.guid import GUID, _instance_id_to_uids, _uid_to_instance_store


def _roll_inheritance_value(xene: Union[GeneCode, PheneCode]) -> int:
    # Placeholder for actual inheritance logic; replace with proper calculations
    die_mult = xene.die_mult
    return sum(randint(1, 6) for _ in range(die_mult))


class InheritanceProcessor:
    """Processes inheritance logic for species and entities, applying genetic traits and calculating derived attributes."""

    @staticmethod
    def species_to_upps(sophont_guid: GUID, species: SpeciesCode) -> None:  # SortedKeyList[UPP]:
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
        pprint(gene_pool)
        print()

        pprint(progenitor_guids)

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

        pprint(progenitor_guids)
        print()
        pprint("Remaining unmatched genes in gene pool:")
        pprint(gene_pool)

        # Randomly assign remaining genes to any progenitor
        for genecode in gene_pool:
            guid = choice(list(progenitor_guids.keys()))
            GUID.add_instance(guid, genecode)
            progenitor_guids[guid].append(genecode)

        print()
        print("Final Progenitor Assignments:")
        pprint(progenitor_guids)
        print()

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # UPP SortedKeyList Construction
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        upp_list: SortedKeyList[UPP] = SortedKeyList(  # pyright: ignore[reportInvalidTypeArguments]
            (
                UPP(xene=gene, value=_roll_inheritance_value(gene))
                for gene in chain(
                    *progenitor_guids.values(),
                    species.genotype.phenes or (),
                )
                if isinstance(gene, (GeneCode))  # if isinstance(gene, (GeneCode, PheneCode))
            ),
            key=lambda upp: upp.xene.characteristic.upp_position,
        )
        print("Constructed UPP List:")
        for upp in upp_list:
            print(
                f"{upp.xene.__class__.__name__} - {upp.xene.characteristic.upp_position} - {repr(upp.xene.characteristic)}: {upp.value}"
            )
