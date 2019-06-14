# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from . import nutrition_program


def register():
    Pool.register(
        nutrition_program.Animal,
        nutrition_program.AnimalGroup,
        nutrition_program.NutritionProgram,
        nutrition_program.Specie,
        module='farm_nutrition_program', type_='model')
    Pool.register(
        nutrition_program.OpenBOM,
        module='farm_nutrition_program', type_='wizard')
