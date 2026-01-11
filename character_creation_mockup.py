from __future__ import annotations

from game.characteristic import Characteristic
from game.genotype import Genotype
from game.phene import Phene

# TODO: I need to improve the step by step instantiation of the sophont's inherited characteristics.

def create_aslan_genotype() -> Genotype:
    # Let's create a custom Phene for TER that works alongside Social Standing
    # to stress test the underlying model logic and validation. Multiple Genes
    # of the same UPP Index is NOT allowed, but multiple Phenes of the same UPP
    # Index is allowed.

    ter_characteristic = Characteristic.of(upp_index=6, subtype=3, category_code=3) # This subtype is not in the base mappings.
    ter_phene = Phene(characteristic=ter_characteristic)
    aslan_genes_by_name = [
        "Strength", 
        "Dexterity",
        "Endurance",
        "Intelligence",
    ]
    aslan_phenes_by_name = [
        "Education",
        "Social Standing",
        "Psionics",
        "Sanity",
    ]
    aslan_genotype = Genotype.by_characteristic_names(
        aslan_genes_by_name,
        aslan_phenes_by_name,
        custom_phenes=[ter_phene]
    )

    return aslan_genotype

print(create_aslan_genotype().get_phenes_without_genes())