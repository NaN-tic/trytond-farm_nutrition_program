# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from .nutrition_program import *


def register():
    Pool.register(
        Animal,
        AnimalGroup,
        NutritionProgram,
        Specie,
        module='farm_nutrition_program', type_='model')
    Pool.register(
        OpenBOM,
        module='farm_nutrition_program', type_='wizard')
