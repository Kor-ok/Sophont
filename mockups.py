from __future__ import annotations

from uuid import uuid4
from random import randint

from game.genotype import Genotype, Species, TreeOfLifeOrigin, TreeOfLifeNode, Genus
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

    human_genotype = Genotype.by_gene_characteristic_names(human_genes_by_name)

    # print("Human Genotype Genes:")
    # print(human_genotype)

    return human_genotype

def create_detailed_genotype() -> Genotype:

    # For this demonstration, we will create a human genotype using the full
    # depth of gene specification.
    from game.gene import Gene
    from game.characteristic import Characteristic

    # All genes and characteristics are flyweights, so repeated calls to
    # create the same gene or characteristic will return the same instance.

    characteristic_0 =  Characteristic.of(upp_index=0, subtype=0) # This will be Undefined because we are using the T5 mapping that starts at 1
    characteristic_1 = Characteristic.by_name("Strength") # Standard T5 characteristics are string mapped for convenience
    characteristic_2 = Characteristic.of(upp_index=2, subtype=0) # Dexterity
    characteristic_2a = Characteristic.of(upp_index=2, subtype=1) # Agility subtype which Humans do not use
    characteristic_3 = Characteristic.of(upp_index=3, subtype=0) # Endurance
    characteristic_4 = Characteristic.by_name("Intelligence") # Intelligence
    characteristic_5 = Characteristic.by_name("Education") # Education as a demonstration - not used in human genotype
    characteristic_5a = Characteristic.by_name("Instinct") # Instinct as a demonstration - not used in human genotype but can be used as a gene for other species

    # Custom characteristic for demonstration using upp_index used in T5 for Strength
    # but with a subtype of 1. Perhaps an alien variable "Density" equivalent to Strength?
    characteristic_custom = Characteristic.of(upp_index=1, subtype=1)

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

    genotype = Genotype.of([
        gene_4,
        gene_2,
        gene_1,
        gene_3
    ]) # Purposefully disordered input

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

def apply_inherited_genes(sophont: Sophont) -> Sophont:
    # Create "Virtual Parents" uuids 
    # (for this demo we're assuming two parents, but we can derive parentage
    #  from gene.inheritance_contributors too i.e. T5 DNA Rules; 2NA, 3NA, etc).
    # Note that self uuid can be used for cloning scenarios.
    parent_1_uuid = uuid4().bytes
    parent_2_uuid = uuid4().bytes

    # Fetch genotype from the Sophont
    genotype = sophont.epigenetic_profile.genotype

    BASE_DIE_VALUE = 6 # nD6 T5 rules

    from game.phene import Phene
    from game.characteristic_package import CharacteristicPackage

    # The is_grafted flag of an AppliedGene can allow for the use of donor/providor uuid scenarios.
    # An "Applied Gene" can therefore supercede another based on some logic.
    # For this demonstration, we will keep it simple and generate inheritance according to the genotype.
    inherited_genes = {}
    for gene in genotype.genes:
        applied_phene = Phene(
            characteristic=gene.characteristic,
            expression_value=randint(1, BASE_DIE_VALUE * gene.die_mult),
            contributor_uuid=parent_1_uuid if randint(0,1) == 0 else parent_2_uuid,
            is_grafted=False
        )
        inherited_genes[gene.characteristic.upp_index] = applied_phene

    inheritance_packages = {}
    for applied_phene in inherited_genes.values():
        package = CharacteristicPackage(item=applied_phene, level=0, context="Inherited Gene")
        inheritance_packages[applied_phene.characteristic.upp_index] = package

    # Apply inherited gene packages to sophont's epigenetic profile
    for package in inheritance_packages.values():
        sophont.epigenetic_profile.insert_package_acquired(
            package=package, 
            age_acquired_seconds=0, # Inception (Gestation period not yet implemented) 
            memo="Inherited Gene")

    print("Sophont with Inherited Genes:")
    print(sophont)
    return sophont

def define_species() -> None:
    human_genotype = create_standard_genotype()
    human_species_id = uuid4().bytes
    human_species = Species(genotype=human_genotype, uuid=human_species_id)

    neanderthal_genotype = create_standard_genotype()
    neanderthal_species_id = uuid4().bytes
    neanderthal_species = Species(genotype=neanderthal_genotype, uuid=neanderthal_species_id)

    vargr_genes_by_name = [
        "Strength",
        "Dexterity",
        "Intelligence",
        "Endurance",
        "Charisma" # For this demo, we add Charisma to differentiate from humans
        ]
    vargr_genotype = Genotype.by_gene_characteristic_names(vargr_genes_by_name)
    vargr_species_id = uuid4().bytes
    vargr_species = Species(genotype=vargr_genotype, uuid=vargr_species_id)

    from game.mappings.world_id import EARTH_WORLD_ID, VLAND_WORLD_ID, KARGOL_WORLD_ID
    tree_of_life_earth = TreeOfLifeOrigin(world_id=EARTH_WORLD_ID)
    tree_of_life_vland = TreeOfLifeOrigin(world_id=VLAND_WORLD_ID)
    tree_of_life_kargol = TreeOfLifeOrigin(world_id=KARGOL_WORLD_ID)
    
    # For Humans, the Genus is 8 levels deep in the Tree of Life from the root.
    human_path = [uuid4().bytes for _ in range(8)]
    tree_of_life_earth.add_node(human_path)

    # Get uuid of the human genus node
    human_genus_uuid = human_path[-1]

    human_genus = Genus(
        species_collection=[human_species, neanderthal_species],
        tree_of_life_node_uuid=human_genus_uuid
    )

    # The Vilani of the World of Vland are a transplanted human OF THE SAME SPECIES.
    vilani_path = human_genus.tree_of_life_node_uuid
    tree_of_life_vland.add_node([vilani_path]) # This creates a direct link to the
                                               # human genus node, maintaining species identity,
                                               # but identifying the world transplantation.

    # The Kargol of the World of Kargol are Neanderthals transplanted to that world.
    kargol_ancestor_path = human_genus.tree_of_life_node_uuid
    # They then diverged from Neanderthals to become a distinct species
    kargol_genotype = create_standard_genotype()
    kargol_species_id = uuid4().bytes
    kargol_species = Species(genotype=kargol_genotype, uuid=kargol_species_id)
    # New node for Kargol species
    kargol_transplanted_genus_id = uuid4().bytes

    tree_of_life_kargol.add_node([kargol_ancestor_path, kargol_transplanted_genus_id]) # This creates a direct link to the
                                                # human genus node, identifying the world transplantation,
                                                # then adds a new node for the transplanted genus.
    kargol_transplanted_genus = Genus(
        species_collection=[kargol_species],
        tree_of_life_node_uuid=kargol_transplanted_genus_id
    )

    # For Vargr, they differentiate from Humans at level 4
    vargr_ancestor_path = human_path[:4] + [uuid4().bytes for _ in range(4)]
    tree_of_life_earth.add_node(vargr_ancestor_path)

    vargr_ancestor_genus_uuid = vargr_ancestor_path[-1]

    # They then diverged to become their own genus
    vargr_genus = Genus(
        species_collection=[vargr_species],
        tree_of_life_node_uuid = uuid4().bytes
    )

    tree_of_life_earth.display()
    

if __name__ == "__main__":
    print("\033c", end="")
    
    sophont = create_unborn_sophont()
    sophont = apply_inherited_genes(sophont)