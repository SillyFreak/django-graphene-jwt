Graphene JWT Auth
=================

**JSON Web Token Authentication support for Django + Graphene**

This package provides JWT authentication via GraphQL using `Graphene`_,
similarly to how `django-rest-framework-jwt`_ exposes JWT via REST.

``django-graphene-jwt`` uses ``djangorestframework-jwt`` under the hood;
it simply adapts the request and response handling to suit Graphene.
That means that `djangorestframework-jwt's settings`_ are used.

Some caveats and known issues:

- This library uses ``DjangoObjectType`` for making users accessible via GraphQL.
  This means that all ``User`` fields, in particular also hashed passwords, superuser status, etc., can be queried.
  User objects are only provided when providing the correct password or a valid token, but still, this is bad!
- The ``JWT_ALLOW_REFRESH`` property is not honored - token refresh is always possible;
  as a workaround, ``JWT_REFRESH_EXPIRATION_DELTA`` can be set to a low value.
- The ``JWTGraphQLView`` class is pretty ad-hoc;
  using the ``REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`` setting would probably be better.
  Also, there is no equivalent of ``DEFAULT_PERMISSION_CLASSES``.
  Checking permissions is currently the resolvers' and mutation methods' responsibility.
- There is no test suite and there has not been a formal code review!
  This is security code, and while the attack surface is small, it has to be pointed out.
  If you think about using this library, read the code; it's only 170 lines in total, in `schema.py`_ and `views.py`_.

If you want production-grade Graphene JWT support, think about contributing!

.. _Graphene: https://github.com/graphql-python/graphene-django/
.. _django-rest-framework-jwt: https://github.com/GetBlimp/django-rest-framework-jwt
.. _djangorestframework-jwt's settings: http://getblimp.github.io/django-rest-framework-jwt/#additional-settings
.. _schema.py: https://github.com/SillyFreak/django-graphene-jwt/blob/master/graphene_jwt/schema.py
.. _views.py: https://github.com/SillyFreak/django-graphene-jwt/blob/master/graphene_jwt/views.py

Installation
------------

``django-graphene-jwt`` is not on pypi yet.
For installation, use::

    pip install git+https://github.com/SillyFreak/django-graphene-jwt

Usage
-----

Like with any Graphene application, make sure you have the following settings applied::

    INSTALLED_APPS = (
        # ...
        'graphene_django',
    )

    GRAPHENE = {
        'SCHEMA': 'app.schema.schema' # Where your Graphene schema lives
    }

Add a URL for the GraphQL API, and use the ``JWTGraphQLView`` class to have the JWT authentication header parsed::

    from django.conf.urls import url
    from graphene_jwt.views import JWTGraphQLView

    urlpatterns = [
        # ...
        url(r'^graphql/', JWTGraphQLView.as_view(graphiql=True)),
    ]

In you schema, make sure you inherit the ``graphene_jwt`` queries and mutations::

    import graphene
    import graphene_jwt.schema

    class Query(graphene_jwt.schema.Query, graphene.ObjectType):
        pass

    class Mutation(graphene_jwt.schema.Mutation, graphene.ObjectType):
        pass

    schema = graphene.Schema(query=Query, mutation=Mutation)

To explore the schema, go to ``http://localhost:8000/graphql/`` and open the documentation explorer.
Here is a quick overview::

    # verifies a token and returns that same token along with the user
    query JWTVerify($token: String!) {
      jwtVerify(token: $token) {
        token
        user {
          id
          username
          email
          firstName
          lastName
          # ...
        }
      }
    }

    # authenticates a user and returns a token along with the user
    mutation JWTLogin($username: String!, $password: String!) {
      jwtLogin(username: $username, password: $password) {
        token
        user {
          # ...
        }
      }
    }

    # refreshes a valid token and returns a new token along with the user
    mutation JWTRefresh($token: String!) {
      jwtLogin(token: $token) {
        token
        user {
          # ...
        }
      }
    }
