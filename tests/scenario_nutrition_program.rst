==========================
Nutrition Program Scenario
==========================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> now = datetime.datetime.now()
    >>> yesterday = datetime.datetime.now() - relativedelta(days=1)
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install farm::

    >>> Module = Model.get('ir.module.module')
    >>> modules = Module.find([
    ...         ('name', '=', 'farm_nutrition_program'),
    ...         ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='NaN·tic')
    >>> party.save()
    >>> company.party = party
    >>> currencies = Currency.find([('code', '=', 'EUR')])
    >>> if not currencies:
    ...     currency = Currency(name='Euro', symbol=u'€', code='EUR',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point=',')
    ...     currency.save()
    ...     CurrencyRate(date=now.date() + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> kg, = ProductUom.find([('name', '=', 'Kilogram')])
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> individual_template = ProductTemplate(
    ...     name='Male Pig',
    ...     default_uom=unit,
    ...     type='goods',
    ...     list_price=Decimal('40'),
    ...     cost_price=Decimal('25'))
    >>> individual_template.save()
    >>> individual_product = Product(template=individual_template)
    >>> individual_product.save()
    >>> group_template = ProductTemplate(
    ...     name='Group of Pig',
    ...     default_uom=unit,
    ...     type='goods',
    ...     list_price=Decimal('30'),
    ...     cost_price=Decimal('20'))
    >>> group_template.save()
    >>> group_product = Product(template=group_template)
    >>> group_product.save()
    >>> feed_template = ProductTemplate(
    ...     name='Feed',
    ...     default_uom=kg,
    ...     type='goods',
    ...     list_price=Decimal('40'),
    ...     cost_price=Decimal('25'))
    >>> feed_template.save()
    >>> feed_product = Product(template=feed_template)
    >>> feed_product.save()
    >>> feed_product.reload()

Create sequence::

    >>> Sequence = Model.get('ir.sequence')
    >>> event_order_sequence = Sequence(
    ...     name='Event Order Pig Warehouse 1',
    ...     code='farm.event.order',
    ...     padding=4)
    >>> event_order_sequence.save()
    >>> individual_sequence = Sequence(
    ...     name='Individual Pig Warehouse 1',
    ...     code='farm.animal',
    ...     padding=4)
    >>> individual_sequence.save()
    >>> group_sequence = Sequence(
    ...     name='Groups Pig Warehouse 1',
    ...     code='farm.animal.group',
    ...     padding=4)
    >>> group_sequence.save()

Create specie::

    >>> Location = Model.get('stock.location')
    >>> lost_found_location, = Location.find([('type', '=', 'lost_found')])
    >>> warehouse, = Location.find([('type', '=', 'warehouse')])
    >>> Specie = Model.get('farm.specie')
    >>> SpecieBreed = Model.get('farm.specie.breed')
    >>> SpecieFarmLine = Model.get('farm.specie.farm_line')
    >>> pigs_specie = Specie(
    ...     name='Pigs',
    ...     male_enabled=False,
    ...     female_enabled=False,
    ...     individual_enabled=True,
    ...     individual_product=individual_product,
    ...     group_enabled=True,
    ...     group_product=group_product,
    ...     removed_location=lost_found_location,
    ...     foster_location=lost_found_location,
    ...     lost_found_location=lost_found_location,
    ...     feed_lost_found_location=lost_found_location)
    >>> pigs_specie.save()
    >>> pigs_breed = SpecieBreed(
    ...     specie=pigs_specie,
    ...     name='Holland')
    >>> pigs_breed.save()
    >>> pigs_farm_line = SpecieFarmLine(
    ...     specie=pigs_specie,
    ...     farm=warehouse,
    ...     event_order_sequence=event_order_sequence,
    ...     has_individual=True,
    ...     individual_sequence=individual_sequence,
    ...     has_group=True,
    ...     group_sequence=group_sequence)
    >>> pigs_farm_line.save()

Create farm locations::

    >>> location1_id, location2_id = Location.create([{
    ...         'name': 'Location 1',
    ...         'code': 'L1',
    ...         'type': 'storage',
    ...         'parent': warehouse.storage_location.id,
    ...         }, {
    ...         'name': 'Location 2',
    ...         'code': 'L2',
    ...         'type': 'storage',
    ...         'parent': warehouse.storage_location.id,
    ...         }], config.context)
    >>> silo = Location(
    ...     name='Silo',
    ...     code='S',
    ...     type='storage',
    ...     parent=warehouse.storage_location,
    ...     silo=True,
    ...     locations_to_fed=[location1_id, location2_id])
    >>> silo.save()

Put 500 Kg of feed into silo location::

    >>> Move = Model.get('stock.move')
    >>> provisioning_moves = Move.create([{
    ...         'product': feed_product.id,
    ...         'uom': kg.id,
    ...         'quantity': 500.0,
    ...         'from_location': party.supplier_location.id,
    ...         'to_location': silo.id,
    ...         'planned_date': (now - relativedelta(days=10)).date(),
    ...         'effective_date': (now - relativedelta(days=10)).date(),
    ...         'company': config.context.get('company'),
    ...         'unit_price': feed_product.template.list_price,
    ...         }],
    ...     config.context)
    >>> Move.assign(provisioning_moves, config.context)
    >>> Move.do(provisioning_moves, config.context)

Create individual::

    >>> Animal = Model.get('farm.animal')
    >>> individual = Animal(
    ...     type='individual',
    ...     specie=pigs_specie,
    ...     breed=pigs_breed,
    ...     number='0001',
    ...     initial_location=location1_id,
    ...     arrival_date=(now - relativedelta(days=5)).date())
    >>> individual.save()
    >>> individual.location.code
    u'L1'
    >>> individual.farm.code
    u'WH'
    >>> individual.nutrition_program == None
    True

Create nutrition program::

    >>> NutritionProgram = Model.get('farm.nutrition.program')
    >>> nutrition_program = NutritionProgram(
    ...     specie=pigs_specie,
    ...     animal_type='individual',
    ...     min_consumed_feed=2.0,
    ...     max_consumed_feed=10.0,
    ...     product=feed_product)
    >>> nutrition_program.save()
    >>> individual.nutrition_program == None
    True

Feed the animal::

    >>> FeedEvent = Model.get('farm.feed.event')
    >>> feed_event1 = FeedEvent(
    ...     animal_type='individual',
    ...     specie=pigs_specie,
    ...     farm=warehouse,
    ...     animal=individual,
    ...     timestamp=yesterday,
    ...     location=individual.location,
    ...     feed_location=silo,
    ...     feed_product=feed_product,
    ...     uom=kg,
    ...     feed_quantity=Decimal('6.0'))
    >>> feed_event1.feed_product = feed_product
    >>> feed_event1.save()
    >>> FeedEvent.validate_event([feed_event1.id], config.context)
    >>> individual.reload()
    >>> individual.consumed_feed.quantize(Decimal('0.1'))
    Decimal('6.0')
    >>> individual.nutrition_program == nutrition_program
    True

Create another nutrition program::

    >>> nutrition_program2 = NutritionProgram(
    ...     specie=pigs_specie,
    ...     animal_type='individual',
    ...     min_consumed_feed=10.0,
    ...     max_consumed_feed=50.0,
    ...     product=feed_product)
    >>> nutrition_program2.save()
    >>> individual.nutrition_program == nutrition_program
    True

Feed the animal::

    >>> feed_event2 = FeedEvent(
    ...     animal_type='individual',
    ...     specie=pigs_specie,
    ...     farm=warehouse,
    ...     animal=individual,
    ...     timestamp=(yesterday + relativedelta(days=5)),
    ...     start_date=yesterday.date(),
    ...     location=individual.location,
    ...     feed_location=silo,
    ...     feed_product=feed_product,
    ...     uom=kg,
    ...     feed_quantity=Decimal('25.0'))
    >>> feed_event2.feed_product = feed_product
    >>> feed_event2.save()
    >>> FeedEvent.validate_event([feed_event2.id], config.context)
    >>> individual.reload()
    >>> individual.consumed_feed.quantize(Decimal('0.1'))
    Decimal('11.0')
    >>> individual.nutrition_program == nutrition_program2
    True
