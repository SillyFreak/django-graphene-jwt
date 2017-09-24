from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from graphene_django.views import GraphQLView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class JWTGraphQLView(GraphQLView):
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        auth = JSONWebTokenAuthentication()
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple is not None:
            request.user, request.auth = user_auth_tuple
        return super(JWTGraphQLView, self).dispatch(request, *args, **kwargs)
