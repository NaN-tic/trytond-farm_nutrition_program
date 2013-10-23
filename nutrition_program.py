#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

__all__ = ['NutritionProgram']


class NutritionProgram(ModelSQL, ModelView):
    'Nutrition Program'
    __name__ = 'nutrition.program'

    start_weight = fields.Float('Start Weight')
    end_weight = fields.Float('End Weight')
    product = fields.Many2One('product.product', 'Product', required=True)
    bom = fields.Many2One('production.bom', 'BOM',
        domain=[
            ('output_products', '=', Eval('product', 0)),
            ],
        depends=['product'])

    def get_rec_name(self, name=None):
        return ' %s ( %s - %s) ' % (self.product.rec_name,
            self.start_weight or '',  self.end_weight or '')
