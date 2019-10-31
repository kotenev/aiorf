import json
from enum import Enum

from aiohttp import web
import sqlalchemy as sa

# TODO import apispec
from aiohttp_security import permits

class RESTError(web.HTTPError):
    status_code = 500
    error = "Unknown Error"

    def __init__(self, message=None, status_code=None, **kwargs):

        if status_code is not None:
            self.status_code = status_code

        super().__init__(reason=message)
        if not message:
            message = self.error

        msg_dict = {"error": message}

        if kwargs:
            msg_dict['error_details'] = kwargs

        self.text = json.dumps(msg_dict)
        self.content_type = 'application/json'

class ForbiddenError(RESTError):
    status_code = 401
    error = "Access denied"

class NotFoundError(RESTError):
    status_code = 404
    error = "Not found"

class MethodNotAllowed(RESTError):
    status_code = 405
    error = "Method not allowed"

class BadRequest(RESTError):
    status_code = 400
    error = 'Bad request'


async def require(request, permission):
    has_perm = await permits(request, permission)
    if not has_perm:
        msg = 'User has no permission {}'.format(permission)
        raise ForbiddenError(msg)

class Endpoint:
    pool = None
    model = None
    schema = None
    lookup_field = 'id'
    lookup_regex = '\d+'
    filters = []
    path = '/endpoint'

    def __init__(self, pool):
        self.pool = pool

    async def dispatch(self, request):
        method = request.method.lower()
        if not hasattr(self, method):
            raise MethodNotAllowed
        if 'id' not in request.match_info:
            method = 'list'
        return await getattr(self, method)(request, *request.match_info.values())

    async def get_object(self, object_id):
        async with self.pool.acquire() as conn:
            query = self.model.__table__.select().where(getattr(self.model, self.lookup_field) == object_id)
            row = await conn.execute(query)
            rec = await row.first()
        if not rec:
            raise NotFoundError
        return rec

    async def get(self, request, object_id):
        # await require(request, Permissions.view)
        rec = await self.get_object(object_id)
        return web.json_response(self.schema.dump(rec))

    async def list(self, request):
        # await require(request, Permissions.view)
        # def text_filter(query, value, table):
        #     pairs = ((n, c) for n, c in table.c.items()
        #              if isinstance(c.type, sa.sql.sqltypes.String))
        #     sub_queries = []
        #     for name, column in pairs:
        #         do_compare = op("like", column)
        #         sub_queries.append(do_compare(column, value))
        #
        #     query = query.where(or_(*sub_queries))
        #     return query
        async with self.pool.acquire() as conn:
            query = self.model.__table__.select()
            count = await conn.scalar(
                sa.select([sa.func.count()]).select_from(query.alias('foo'))
            )
            # sort_dir = sa.asc if paging.sort_dir == ASC else sa.desc
            cursor = await conn.execute(query)
            # .offset(paging.offset)
            # .limit(paging.limit)
            # .order_by(sort_dir(paging.sort_field)))

            recs = await cursor.fetchall()
            headers = {'X-Total-Count': str(count)}
            return web.json_response(self.schema.dump(recs, many=True), headers=headers)

    async def post(self, request):
        # await require(request, Permissions.view)
        data = await request.json()
        errors = self.schema.validate(data)
        if errors:
            raise BadRequest(errors)
        async with self.pool.acquire() as conn:
            query = self.model.__table__.insert().values(data)
            rec = await conn.execute(query)
            await conn.execute('commit;')

    async def put(self, request, object_id):
        # await require(request, Permissions.edit)
        data = await request.json()
        rec = await self.get_object(object_id)
        errors = self.schema.validate(data)
        if errors:
            raise BadRequest(errors)
        async with self.pool.acquire() as conn:
            row = await conn.execute(
                self.model.__table__.update()
                    .values(data))
                    # .returning(*self.__table__.c)
                    # .where(self._pk == entity_id))
            await conn.execute('commit;')

    async def patch(self, request, object_id):
        return await self.put(request, object_id)

    async def delete(self, request, object_id):
        # await require(request, Permissions.delete)
        async with self.pool.acquire() as conn:
            query = self.model.__table__.delete().where(getattr(self.model, self.lookup_field) == object_id)
            await conn.execute(query)
            # TODO: Think about autocommit by default
            await conn.execute('commit;')

    def setup_routes(self, router):
        router.add_route('*', f'{self.path}', self.dispatch)
        router.add_route('*', f'{self.path}/{{id}}', self.dispatch)


import marshmallow_sqlalchemy
from aiopg.sa import create_engine

import sqlalchemy as sa
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref

engine = sa.create_engine("postgres://127.0.0.1/test")
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)

    def __repr__(self):
        return "<Author(name={self.name!r})>".format(self=self)


class AuthorSchema(ModelSchema):
    class Meta:
        model = Author
        transient = True

Base.metadata.create_all(engine)
author = Author(name="Chuck Paluhniuk")
session.add(author)
session.commit()
author = Author(name="Adolf Hitler")
session.add(author)
session.commit()

import ipdb
ipdb.set_trace()

class Test(Endpoint):
    model = Author
    schema = AuthorSchema()
    path = '/test'



app = web.Application()
async def on_startup(app):
    db = await create_engine(database='test')
    test = Test(db)
    test.setup_routes(app.router)

# import ipdb
# ipdb.set_trace()
# aiohttp_autoreload.start()
app.on_startup.append(on_startup)
web.run_app(app)

