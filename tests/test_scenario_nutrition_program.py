import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.modules.farm.tests.tools import create_feed_product, create_specie
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Imports
        now = datetime.datetime.now()
        yesterday = datetime.datetime.now() - relativedelta(days=1)

        # Install module
        activate_modules('farm_nutrition_program')

        # Create company
        _ = create_company()
        company = get_company()

        # Create specie
        specie, breed, products = create_specie('Pig')

        # Create farm users

        # Get locations
        Location = Model.get('stock.location')
        lost_found_location, = Location.find([('type', '=', 'lost_found')])
        warehouse, = Location.find([('type', '=', 'warehouse')])
        production_location, = Location.find([('type', '=', 'production')])

        # Create feed product
        feed_product = create_feed_product('Feed', 40, 25)

        # Create farm locations
        Location = Model.get('stock.location')
        location1 = Location()
        location1.name = 'Location 1'
        location1.code = 'L1'
        location1.type = 'storage'
        location1.parent = warehouse.storage_location
        location1.save()
        location2 = Location()
        location2.name = 'Location 2'
        location2.code = 'L2'
        location2.type = 'storage'
        location2.parent = warehouse.storage_location
        location2.save()
        silo = Location()
        silo.name = 'Silo'
        silo.code = 'S'
        silo.type = 'storage'
        silo.parent = warehouse.storage_location
        silo.silo = True
        silo.locations_to_fed.append(location1)
        silo.locations_to_fed.append(location2)
        silo.save()

        # Put 500 Kg of feed into silo location
        Move = Model.get('stock.move')
        provisioning_move = Move()
        provisioning_move.product = feed_product
        provisioning_move.uom = feed_product.default_uom
        provisioning_move.quantity = 500.0
        provisioning_move.from_location = company.party.supplier_location
        provisioning_move.to_location = silo
        provisioning_move.planned_date = (now - relativedelta(days=10)).date()
        provisioning_move.effective_date = (now - relativedelta(days=10)).date()
        provisioning_move.company = company
        provisioning_move.unit_price = feed_product.template.list_price
        provisioning_move.currency = company.currency
        provisioning_move.save()
        provisioning_move.click('do')

        # Create individual
        Animal = Model.get('farm.animal')
        individual = Animal()
        individual.type = 'individual'
        individual.specie = specie
        individual.breed = breed
        individual.number = '0001'
        individual.initial_location = location1
        individual.arrival_date = (now - relativedelta(days=5)).date()
        individual.save()
        self.assertEqual(individual.location.code, 'L1')
        self.assertEqual(individual.farm.code, 'WH')
        self.assertEqual(individual.nutrition_program, None)

        # Create nutrition program
        NutritionProgram = Model.get('farm.nutrition.program')
        nutrition_program = NutritionProgram()
        nutrition_program.specie = specie
        nutrition_program.animal_type = 'individual'
        nutrition_program.min_consumed_feed = 2.0
        nutrition_program.max_consumed_feed = 10.0
        nutrition_program.product = feed_product
        nutrition_program.save()
        self.assertEqual(individual.nutrition_program, None)

        # Feed the animal
        FeedEvent = Model.get('farm.feed.event')
        feed_event1 = FeedEvent()
        feed_event1.animal_type = 'individual'
        feed_event1.specie = specie
        feed_event1.farm = warehouse
        feed_event1.animal = individual
        feed_event1.timestamp = yesterday
        feed_event1.location = individual.location
        feed_event1.feed_location = silo
        feed_event1.feed_product = feed_product
        feed_event1.uom = feed_product.default_uom
        feed_event1.feed_quantity = Decimal('6.0')
        feed_event1.feed_product = feed_product
        feed_event1.save()
        feed_event1.click('validate_event')
        individual.reload()
        self.assertEqual(individual.consumed_feed.quantize(Decimal('0.1')),
                         Decimal('6.0'))
        self.assertEqual(individual.nutrition_program, nutrition_program)

        # Create another nutrition program
        nutrition_program2 = NutritionProgram()
        nutrition_program2.specie = specie
        nutrition_program2.animal_type = 'individual'
        nutrition_program2.min_consumed_feed = 10.0
        nutrition_program2.max_consumed_feed = 50.0
        nutrition_program2.product = feed_product
        nutrition_program2.save()
        self.assertEqual(individual.nutrition_program, nutrition_program)

        # Feed the animal
        feed_event2 = FeedEvent()
        feed_event2.animal_type = 'individual'
        feed_event2.specie = specie
        feed_event2.farm = warehouse
        feed_event2.animal = individual
        feed_event2.timestamp = now
        feed_event2.start_date = yesterday.date()
        feed_event2.location = individual.location
        feed_event2.feed_location = silo
        feed_event2.feed_product = feed_product
        feed_event2.uom = feed_product.default_uom
        feed_event2.feed_quantity = Decimal('25.0')
        feed_event2.feed_product = feed_product
        feed_event2.save()
        feed_event2.click('validate_event')
        individual.reload()
        self.assertEqual(individual.consumed_feed.quantize(Decimal('0.1')),
                         Decimal('31.0'))
        self.assertEqual(individual.nutrition_program, nutrition_program2)
