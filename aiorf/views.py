from aiohttp.web import View

from aiorf import mixins


class APIView(View):
    pass


class GenericAPIView(APIView):
    serializer_class = None
    lookup_field = 'pk'
    lookup_url_kwarg = None
    pagination_class = None
    filter_backends = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        if self.lookup_field == 'pk':
            if not self.lookup_url_kwarg:
                self.lookup_url_kwarg = 'pk'
            self.lookup_field = self.serializer_class.Meta.model._meta.primary_key.name

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'view': self
        }

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        # kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        return self.serializer_class.Meta.model.select()

    async def get_object(self):
        """
        Returns the object the view is displaying.
        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        filter_kwargs = {self.lookup_field: self.request.match_info[lookup_url_kwarg]}
        obj = await self.manager.get(self.serializer_class.Meta.model, **filter_kwargs)

        # May raise a permission denied
        # self.check_object_permissions(self.request, obj)

        return obj

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class CreateAPIView(mixins.CreateModelMixin,
                    GenericAPIView):
    """
    Concrete view for creating a model instance.
    """
    async def post(self, *args):
        return await self.create()


class ListAPIView(mixins.ListModelMixin,
                  GenericAPIView):
    """
    Concrete view for listing a queryset.
    """
    async def get(self, *args):
        return await self.list()


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      GenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    async def get(self, *args):
        return await self.retrieve()


class DestroyAPIView(mixins.DestroyModelMixin,
                     GenericAPIView):
    """
    Concrete view for deleting a model instance.
    """
    async def delete(self, *args):
        return await self.destroy()


class UpdateAPIView(mixins.UpdateModelMixin,
                    GenericAPIView):
    """
    Concrete view for updating a model instance.
    """
    async def put(self, *args):
        return await self.update()

    async def patch(self, *args):
        return await self.partial_update()


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        GenericAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    async def get(self, *args):
        return await self.list()

    async def post(self, *args):
        return await self.create()


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            GenericAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """
    async def get(self, *args):
        return await self.retrieve()

    async def put(self, *args):
        return await self.update()

    async def patch(self, *args):
        return await self.partial_update()


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             GenericAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """
    async def get(self, *args):
        return await self.retrieve()

    async def delete(self, *args):
        return await self.destroy()


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   GenericAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    async def get(self, *args):
        return await self.retrieve()

    async def put(self, *args):
        return await self.update()

    async def patch(self, *args):
        return await self.partial_update()

    async def delete(self, *args):
        return await self.destroy()
