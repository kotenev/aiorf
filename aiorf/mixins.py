import peewee_async
from aiohttp import web


class CreateModelMixin:
    """
    Create a model instance.
    """
    async def create(self):
        serializer = self.get_serializer()
        data = await request.json()
        obj = serializer.load(data)
        await self.perform_create(obj)
        headers = self.get_success_headers(serializer.data)
        return web.json_response(serializer.data, status=web.HTTPCreated.status_code, headers=headers)

    async def perform_create(self, obj):
        await self.manager.create(obj)

    def get_success_headers(self, data):
        return {}


class ListModelMixin:
    """
    List a queryset.
    """
    async def list(self):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            page = await peewee_async.execute(page)
            serializer = self.get_serializer()
            serializer.dump(page, many=True)
            return self.get_paginated_response(serializer)

        queryset = await peewee_async.execute(queryset)
        serializer = self.get_serializer()
        return web.json_response(serializer.dump(queryset, many=True))


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """
    async def retrieve(self):
        instance = await self.get_object()
        serializer = self.get_serializer()
        return web.json_response(serializer.dump(instance))


class UpdateModelMixin:
    """
    Update a model instance.
    """
    async def update(self):
        partial = kwargs.pop('partial', False)
        instance = await self.get_object()
        serializer = self.get_serializer()
        data = await request.json()
        obj = serializer.load(data, instance=instance)
        await self.perform_update(obj)

        return web.json_response(obj._data)

    async def perform_update(self, obj):
        await self.manager.update(obj)

    async def partial_update(self):
        kwargs['partial'] = True
        return await self.update(request, *args, **kwargs)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """
    async def destroy(self):
        instance = await self.get_object()

        await self.perform_destroy(instance)
        return web.json_response(status=web.HTTPNoContent.status_code)

    async def perform_destroy(self, instance):
        await self.manager.delete(instance)
