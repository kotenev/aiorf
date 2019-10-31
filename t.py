import asyncio

import aiohttp_autoreload
from aiohttp import web
from aiohttp_utils.routing import ResourceRouter
import peewee
import peewee_async
from marshmallow.fields import Nested
from playhouse.fields import ManyToManyField
from aiorf.modelschema import ModelSchema
from aiorf.viewsets import ModelViewSet

database = peewee_async.PostgresqlDatabase('test')
from aiorf.views import ListCreateAPIView, RetrieveAPIView


class TestModel(peewee.Model):
    text = peewee.CharField()

    class Meta:
        database = database


class FkeyModel(peewee.Model):
    z = peewee.IntegerField(default=lambda: 1)
    test = peewee.ForeignKeyField(TestModel)

    class Meta:
        database = database


TestModel.create_table(True)
FkeyModel.create_table(True)
z=TestModel.create(text="Yo, I can do it sync!")
x=FkeyModel.create(test=z)

class Test(ModelSchema):
    class Meta:
        model = TestModel

class Fkey(ModelSchema):
    test = Nested(Test)
    class Meta:
        model = FkeyModel

loop = asyncio.new_event_loop()
database.set_allow_sync(False)


class MyView(ModelViewSet):
    serializer_class = Test
    manager = peewee_async.Manager(database, loop=loop)

routes = web.RouteTableDef()

@routes.view('/test')
class Foo(ListCreateAPIView):
    serializer_class = Test
    manager = peewee_async.Manager(database, loop=loop)



loop = asyncio.new_event_loop()

app = web.Application()
app.add_routes(MyView.get_routes('/test'))
# import ipdb
# ipdb.set_trace()
aiohttp_autoreload.start()
web.run_app(app)
