# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, PYSONEncoder
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateAction

__all__ = ['NutritionProgram', 'Animal', 'AnimalGroup', 'OpenBOM', 'Specie']


class NutritionProgram(ModelSQL, ModelView):
    'Nutrition Program'
    __name__ = 'farm.nutrition.program'

    specie = fields.Many2One('farm.specie', 'Specie', required=True,
        select=True, states={
            'readonly': True,
            })
    animal_type = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('individual', 'Individual'),
        ('group', 'Group'),
        ], "Animal Type", required=True, select=True)
    min_consumed_feed = fields.Float('Min Consumed Feed (Kg)', required=True)
    max_consumed_feed = fields.Float('Max Consumed Feed (Kg)', required=True)
    product = fields.Many2One('product.product', 'Product', required=True)
    bom = fields.Function(fields.Many2One('production.bom', 'BOM', domain=[
                ('output_products', '=', Eval('product', 0)),
                ], depends=['product']),
        'get_bom')

    @staticmethod
    def default_specie():
        return Transaction().context.get('specie')

    def get_bom(self, name):
        if self.product and self.product.boms:
            return self.product.boms[0].bom.id

    def get_rec_name(self, name=None):
        return '%s (%s - %s)' % (self.product.rec_name,
            self.min_consumed_feed or '', self.max_consumed_feed or '')


def _get_nutrition_program(animal):
    pool = Pool()
    Program = pool.get('farm.nutrition.program')

    consumed_feed = animal.consumed_feed
    programs = Program.search([
            ('specie', '=', animal.specie),
            ('animal_type', '=', animal.lot.animal_type),
            ('min_consumed_feed', '<=', consumed_feed),
            ('max_consumed_feed', '>=', consumed_feed),
            ], order=[('max_consumed_feed', 'DESC')], limit=1)
    if len(programs) > 0:
        return programs[0].id


class Animal(metaclass=PoolMeta):
    __name__ = 'farm.animal'

    nutrition_program = fields.Function(
        fields.Many2One('farm.nutrition.program', 'Nutrition Program'),
        'get_nutrition_program')

    def get_nutrition_program(self, name):
        return _get_nutrition_program(self)


class AnimalGroup(metaclass=PoolMeta):
    __name__ = 'farm.animal.group'

    nutrition_program = fields.Function(
        fields.Many2One('farm.nutrition.program', 'Nutrition Program'),
        'get_nutrition_program')

    def get_nutrition_program(self, name):
        return _get_nutrition_program(self)


class OpenBOM(Wizard):
    'Open BOM'
    __name__ = 'farm.nutrition.program.open_bom'
    start_state = 'open_'
    open_ = StateAction('production.act_bom_list')

    def do_open_(self, action):
        pool = Pool()
        NutritionProgram = pool.get('farm.nutrition.program')

        program = NutritionProgram(Transaction().context.get('active_id'))

        bom_ids = []
        if program.product.boms:
            bom_ids = [bom.bom.id for bom in program.product.boms]
        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', bom_ids)])

        return action, {}

    def transition_open_(self):
        return 'end'


class Specie(metaclass=PoolMeta):
    __name__ = 'farm.specie'

    def _create_additional_menus(self, specie_menu, specie_submenu_seq,
            current_menus, current_actions, current_wizards):
        pool = Pool()
        Menu = pool.get('ir.ui.menu')
        ModelData = pool.get('ir.model.data')

        specie_submenu_seq = super(Specie,
            self)._create_additional_menus(specie_menu, specie_submenu_seq,
            current_menus, current_actions, current_wizards)

        nutrition_programs_menu = Menu(
            ModelData.get_id('farm_nutrition_program',
                'menu_nutrition_programs'))

        new_domain = [
            ('specie', '=', self.id),
            ]
        new_context = {
            'specie': self.id,
            }
        self._duplicate_menu(nutrition_programs_menu, specie_menu,
            specie_submenu_seq, current_menus, current_actions,
            current_wizards, new_domain=new_domain, new_context=new_context)
        return specie_submenu_seq + 1
