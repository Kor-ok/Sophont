from __future__ import annotations

import gui.initialisation.species as init_species
from sophont.character import Sophont

IS_DEBUG = True

example_sophont_1 = Sophont(species_genotype=init_species.create_human_genotype())
example_sophont_2 = Sophont(species_genotype=init_species.create_human_genotype())

# TODO: I need to create classes that can hold initial bags of default elements like
# various character cards, species, default genes/phenes, default skills, etc.
# And this should line up with state management so they can be easily swapped out

# Clean up:
#  initialisation.pickables
#  initialisation.species
#  initialisation.state