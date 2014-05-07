# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, PYSONEncoder
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateAction

__all__ = ['NutritionProgram', 'Animal', 'AnimalGroup', 'OpenBOM', 'Specie']
__metaclass__ = PoolMeta


class NutritionProgram(ModelSQL, ModelView):
    'Nutrition Program'
    __name__ = 'farm.nutrition.program'

    specie = fields.Many2One('farm.specie', 'Specie', required=True,
        readonly=True, select=True)
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


class Animal:
    __name__ = 'farm.animal'

    nutrition_program = fields.Function(
        fields.Many2One('farm.nutrition.program', 'Nutrition Program'),
        'get_nutrition_program')

    def get_nutrition_program(self, name):
        return _get_nutrition_program(self)


class AnimalGroup:
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


class Specie:
    __name__ = 'farm.specie'

    @classmethod
    def _create_additional_menus(cls, specie, specie_menu, specie_submenu_seq,
            current_menus, current_actions):
        pool = Pool()
        ActWindow = pool.get('ir.action.act_window')
        Group = pool.get('res.group')
        ModelData = pool.get('ir.model.data')

        super(Specie, cls)._create_additional_menus(specie, specie_menu,
                specie_submenu_seq, current_menus, current_actions)

        act_window_program = ActWindow(ModelData.get_id(
                'farm_nutrition_program', 'act_nutrition_program'))
        program_group = Group(ModelData.get_id('farm_nutrition_program',
                'group_nutrition_program'))

        cls._create_menu_w_action(specie, [
                ('specie', '=', specie.id),
                ], {
                    'specie': specie.id,
                },
            'Nutrition Programs', specie_menu, specie_submenu_seq,
            'tryton-list', program_group, act_window_program, False,
            current_menus, current_actions)
        specie_submenu_seq += 1
