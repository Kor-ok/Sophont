from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Type, Union, Tuple, cast
from uuid import uuid4

from sortedcontainers import SortedKeyList

from game.genotype import Genotype
from game.gene import Gene
from game.phene import Phene
from game.characteristic_package import CharacteristicPackage

class Acquired:
    __slots__ = ('package', 'age_acquired_seconds', 'memo')

    def __init__(self, package: CharacteristicPackage, age_acquired_seconds: int, memo: Optional[str] = None):
        object.__setattr__(self, 'package', package)
        object.__setattr__(self, 'age_acquired_seconds', age_acquired_seconds)
        object.__setattr__(self, 'memo', memo)

    @classmethod
    def by_age(cls, package: CharacteristicPackage, age_seconds: int, memo: Optional[str] = None) -> 'Acquired':
        return cls(package=package, memo=memo, age_acquired_seconds=age_seconds)
    
    def __repr__(self) -> str:
        return f"Acquired(package={repr(self.package)}, age_acquired_seconds={self.age_acquired_seconds}, memo={repr(self.memo)})"

def _package_key(acquired: Acquired) -> Tuple[int, int]:
    return (acquired.package.item.gene.characteristic.upp_index, acquired.age_acquired_seconds)

# TODO: phenotype_collation similar to Aptitudes to be the computed layer that expresses the top level characteristics
class EpigeneticProfile:
    """
    genotype: SpeciesGenotype - The genetic blueprint of the sophont.
    acquired_packages_collection: SortedKeyList[Acquired] ordered by (gene.characteristic.upp_index, age_acquired_seconds)
    is_packages_dirty: bool - Flag to indicate if the aptitude collation needs to be recomputed.
    """
    __slots__ = (
        'acquired_packages_collection',
        'is_packages_dirty',
        'genotype',
    )
    def __init__(self, genotype: Genotype):
        # === COLD DATA (infrequently updated) ============================
        self.acquired_packages_collection: SortedKeyList = SortedKeyList(key=_package_key)
        self.is_packages_dirty = False

        # === NEVER UPDATED DATA === (But Frequently Read) ================
        self.genotype = genotype

    def insert_package_acquired(self, package: CharacteristicPackage, age_acquired_seconds: int, memo: Optional[str] = None) -> None:
        acquired = Acquired.by_age(package=package, age_seconds=age_acquired_seconds, memo=memo)
        self.acquired_packages_collection.add(acquired)
        self.is_packages_dirty = True
        # TODO: Phenotype collation update logic to be added later


