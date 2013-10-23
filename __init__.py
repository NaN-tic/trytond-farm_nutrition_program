#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .nutrition_program import *


def register():
    Pool.register(
        NutritionProgram,
        module='nutrition_program', type_='model')
