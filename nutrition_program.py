#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, PYSONEncoder
from trytond.wizard import Wizard, StateAction
from trytond.transaction import Transaction

__all__ = ['NutritionProgram', 'OpenBOM']


class NutritionProgram(ModelSQL, ModelView):
    'Nutrition Program'
    __name__ = 'nutrition.program'

    start_weight = fields.Float('Start Weight')
    end_weight = fields.Float('End Weight')
    product = fields.Many2One('product.product', 'Product', required=True)
    bom = fields.Function(fields.Many2One('production.bom', 'BOM',
        domain=[
            ('output_products', '=', Eval('product', 0)),
            ],
        depends=['product']), 'get_bom')

    def get_bom(self, name):
        if self.product and self.product.boms:
            return self.product.boms[0].bom.id

    def get_rec_name(self, name=None):
        return ' %s ( %s - %s) ' % (self.product.rec_name,
            self.start_weight or '',  self.end_weight or '')


class OpenBOM(Wizard):
    'Open BOM'
    __name__ = 'nutrition.program.open.bom'
    start_state = 'open_'
    open_ = StateAction('production.act_bom_list')

    def do_open_(self, action):
        pool = Pool()
        NutritionProgram = pool.get('nutrition.program')

        program = NutritionProgram(Transaction().context.get('active_id'))

        bom_ids = []
        if program.product.boms:
            bom_ids = [bom.bom.id for bom in program.product.boms]
        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', bom_ids)])

        return action, {}

    def transition_open_(self):
        return 'end'
