from __future__ import annotations

from random import randint
from uuid import uuid4

from game import genotype
from game.characteristic_package import CharacteristicPackage
from game.genotype import Genotype
from sophont.character import Sophont

# TODO: I need to improve the step by step instantiation of the sophont's inherited characteristics.

human_genes_by_name = [
        "Dexterity", 
        "Strength", 
        "Intelligence", 
        "Endurance"
        ] # Purposefully disordered compared to classical Traveller UPP indices.
    
human_phenes_by_name = [
    "Psionics",
    "Social Standing",
    "Education",
    "Sanity"
    ]

human_genotype = Genotype.by_characteristic_names(human_genes_by_name, human_phenes_by_name)

genes_without_phenes = human_genotype.get_genes_without_phenes()
phenes_without_genes = human_genotype.get_phenes_without_genes()

print("Genes without corresponding phenes:")
for upp_index, gene in genes_without_phenes.items():
    print(f"  UPP Index {upp_index}: {gene.characteristic.get_name()}")

print("\nPhenes without corresponding genes:")
for upp_index, phene in phenes_without_genes.items():
    print(f"  UPP Index {upp_index}: {phene.characteristic.get_name()}")