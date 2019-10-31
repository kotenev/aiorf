from aiohttp import web

from aiorf import mixins
from aiorf.views import GenericAPIView


class GenericViewSet(GenericAPIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        async def method_not_allowed(self):
            raise web.HTTPMethodNotAllowed
        super().__init__(*args, **kwargs)
        for method in ['create', 'list', 'retrieve', 'update', 'partial_update', 'destroy', 'list']:
            if not hasattr(self, method):
                setattr(self, method, method_not_allowed)

    @classmethod
    def get_routes(cls, path):
        def wrap(klass, method):
            async def wrapped(request):
                print(request.match_info.keys())
                r = klass(request)
                return await getattr(r, method)()
            return wrapped
        return [
            web.route('get', r'{}/{{{}}}'.format(path, cls.lookup_url_kwarg or cls.lookup_field), wrap(cls, 'retrieve')),
            web.route('get', r'{}'.format(path), wrap(cls, 'list')),
            web.route('post', r'{}'.format(path), wrap(cls, 'create')),
            web.route('delete', r'{}'.format(path), wrap(cls, 'destroy')),
            web.route('put', r'{}/<{}:\d+>'.format(path, cls.lookup_url_kwarg or cls.lookup_field), wrap(cls, 'update')),
            web.route('patch', r'{}/<{}:\d+>'.format(path, cls.lookup_url_kwarg or cls.lookup_field), wrap(cls, 'partial_update')),
        ]


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
