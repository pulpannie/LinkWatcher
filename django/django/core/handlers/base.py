import logging
import types
import inspect
import json
from collections import defaultdict
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.core.signals import request_finished
from django.db import connections, transaction
from django.urls import get_resolver, set_urlconf
from django.utils.log import log_response
from django.utils.module_loading import import_string
from django.utils import link_tee


from .exception import convert_exception_to_response

logger = logging.getLogger('django.request')
mapping = defaultdict()
mapping["/signup/ POST"] = "Entry function: SignUpView.post"
mapping["/delete-user/ POST"] = "/delete-user/ POST"
mapping["/login/ POST"] = "Entry function: LoginView.post"
mapping["/order/ POST"] = "Entry function: AddOrderView.post"
mapping["/review/ POST"] = "Entry function: AddReview.post"
mapping["/ GET"] = "Entry function: base"


class BaseHandler:
    _view_middleware = None
    _template_response_middleware = None
    _exception_middleware = None
    _middleware_chain = None

    def load_middleware(self):
        """
        Populate middleware lists from settings.MIDDLEWARE.

        Must be called after the environment is fixed (see __call__ in subclasses).
        """
        self._view_middleware = []
        self._template_response_middleware = []
        self._exception_middleware = []

        handler = convert_exception_to_response(self._get_response)
        for middleware_path in reversed(settings.MIDDLEWARE):
            middleware = import_string(middleware_path)
            try:
                mw_instance = middleware(handler)
            except MiddlewareNotUsed as exc:
                if settings.DEBUG:
                    if str(exc):
                        logger.debug('MiddlewareNotUsed(%r): %s', middleware_path, exc)
                    else:
                        logger.debug('MiddlewareNotUsed: %r', middleware_path)
                continue

            if mw_instance is None:
                raise ImproperlyConfigured(
                    'Middleware factory %s returned None.' % middleware_path
                )

            if hasattr(mw_instance, 'process_view'):
                self._view_middleware.insert(0, mw_instance.process_view)
            if hasattr(mw_instance, 'process_template_response'):
                self._template_response_middleware.append(mw_instance.process_template_response)
            if hasattr(mw_instance, 'process_exception'):
                self._exception_middleware.append(mw_instance.process_exception)

            handler = convert_exception_to_response(mw_instance)

        # We only assign to this when initialization is complete as it is used
        # as a flag for initialization being complete.
        self._middleware_chain = handler

    def make_view_atomic(self, view):
        non_atomic_requests = getattr(view, '_non_atomic_requests', set())
        for db in connections.all():
            if db.settings_dict['ATOMIC_REQUESTS'] and db.alias not in non_atomic_requests:
                view = transaction.atomic(using=db.alias)(view)
        return view

    def get_response(self, request):
        """Return an HttpResponse object for the given HttpRequest."""
        # Setup default url resolver for this thread
        set_urlconf(settings.ROOT_URLCONF)
        response = self._middleware_chain(request)
        #link-TEE response
        
        path_method = request.path + " " +request.method
        #print("RESPONSE: ", response.content)
        f = open('/home/annie/django-ecommerce/django-ecommerce/output2.json')
        data = json.load(f)
        #if response.content:
            #tmp = json.loads(response.content)
            #content['hashes'] = defaultdict(list)
            #content = {'data': tmp}
            # content['tags'] = 1
            # hashes = content['hashes']
            # tags = content['tags']
            # for entry_function, sinks in data['direct_dataflow'].items():
            #     if path_method in mapping and entry_function == mapping[path_method]:
            #         for sink in sinks:                            
            #             #check if sink of json file matches sink being processed
            #             if "redirect" in sink['sink']['label']:
            #                 for field_name, field_sources in sink['fields'][0].items():
            #                     field = field_name.split(".")[1:]
            #                     f = field[0]
            #                     for i in field[1:]:
            #                         f += "." + i
            #                     field = f
            #                     for field_source in field_sources:
            #                         for hash_key in link_tee.hashes:
            #                             if field_source['field'] == "self.request.POST":
            #                                 if field_source['field'] in hash_key:
            #                                     for item in link_tee.hashes[hash_key]:
            #                                         hashes[hash_key].append(item)
            #                             else:
            #                                 source = field_source['path'] + "." + str(field_source['line_number']) 
            #                                 f_split = field_source['field'].split(".")
            #                                 if len(f_split) == 1:
            #                                     source += "." + f_split[0]
            #                                 else:
            #                                     for i in field_source['field'].split(".")[1:]:
            #                                         source += "." + i
            #                                 if source in hash_key:
            #                                     for item in link_tee.hashes[hash_key]:
            #                                         if item not in hashes[field]:
            #                                             hashes[field].append(item)
            #                         for tag_key in link_tee.tags:
            #                             if source in tag_key: 
            #                                 tags[field] = link_tee.tags[tag_key]
            # for key, item in content['data'].items():
            #     if 'self.request.POST' in key:
            #         tmp = link_tee.hashes[key]
            #         if tmp:
            #             for i in tmp:
            #                 hashes[key].append(i)
            #         if key in link_tee.tags:
            #             tags[key] = link_tee.tags[key]
            #response.content = json.dumps(content)
        # if response.content:
        #     a = json.loads(response.content)
        #     print("response.content: ", a)
        #     json.dumps(a)
        response._closable_objects.append(request)
        if response.status_code >= 400:
            log_response(
                '%s: %s', response.reason_phrase, request.path,
                response=response,
                request=request,
            )
        # print("request:", request.path, request.method)
        # caller = inspect.getframeinfo(inspect.stack()[5][0])
        # print("inspect", caller.lineno, caller.filename, caller.code_context[0])
        return response

    def _get_response(self, request):
        """
        Resolve and call the view, then apply view, exception, and
        template_response middleware. This method is everything that happens
        inside the request/response middleware.
        """
        response = None

        if hasattr(request, 'urlconf'):
            urlconf = request.urlconf
            set_urlconf(urlconf)
            resolver = get_resolver(urlconf)
        else:
            resolver = get_resolver()

        resolver_match = resolver.resolve(request.path_info)
        callback, callback_args, callback_kwargs = resolver_match
        request.resolver_match = resolver_match

        # Apply view middleware
        for middleware_method in self._view_middleware:
            response = middleware_method(request, callback, callback_args, callback_kwargs)
            if response:
                break

        if response is None:
            wrapped_callback = self.make_view_atomic(callback)
            try:
                response = wrapped_callback(request, *callback_args, **callback_kwargs)
            except Exception as e:
                response = self.process_exception_by_middleware(e, request)
        #print("sending response1: ", response, request, request.path, response.content, callback.__name__)

        # Complain if the view returned None (a common error).
        if response is None:
            if isinstance(callback, types.FunctionType):    # FBV
                view_name = callback.__name__
            else:                                           # CBV
                view_name = callback.__class__.__name__ + '.__call__'

            raise ValueError(
                "The view %s.%s didn't return an HttpResponse object. It "
                "returned None instead." % (callback.__module__, view_name)
            )

        # If the response supports deferred rendering, apply template
        # response middleware and then render the response
        elif hasattr(response, 'render') and callable(response.render):
            for middleware_method in self._template_response_middleware:
                response = middleware_method(request, response)
                # Complain if the template response middleware returned None (a common error).
                if response is None:
                    raise ValueError(
                        "%s.process_template_response didn't return an "
                        "HttpResponse object. It returned None instead."
                        % (middleware_method.__self__.__class__.__name__)
                    )

            try:
                response = response.render()
            except Exception as e:
                response = self.process_exception_by_middleware(e, request)

        return response

    def process_exception_by_middleware(self, exception, request):
        """
        Pass the exception to the exception middleware. If no middleware
        return a response for this exception, raise it.
        """
        for middleware_method in self._exception_middleware:
            response = middleware_method(request, exception)
            if response:
                return response
        raise


def reset_urlconf(sender, **kwargs):
    """Reset the URLconf after each request is finished."""
    set_urlconf(None)


request_finished.connect(reset_urlconf)
