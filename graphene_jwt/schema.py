import graphene
from graphql.error.base import GraphQLError
from graphene_django import DjangoObjectType

import jwt
from calendar import timegm
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext as _
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.compat import get_username_field


User = get_user_model()
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class UserType(DjangoObjectType):
    class Meta:
        model = User


class Login(graphene.Mutation):
    token = graphene.String()
    user = graphene.Field(UserType)

    class Input:
        username = graphene.String()
        password = graphene.String()

    @graphene.resolve_only_args
    def mutate(root, username, password):
        credentials = {
            get_username_field(): username,
            'password': password,
        }

        user = authenticate(**credentials)

        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise GraphQLError(msg)
        if not user.is_active:
            msg = _("User account is disabled.")
            raise GraphQLError(msg)

        payload = jwt_payload_handler(user)

        return Login(
            token=jwt_encode_handler(payload),
            user=user,
        )


def _check_payload(token):
    try:
        payload = jwt_decode_handler(token)
    except jwt.ExpiredSignature:
        msg = _("Signature has expired.")
        raise GraphQLError(msg)
    except jwt.DecodeError:
        msg = _("Error decoding signature.")
        raise GraphQLError(msg)

    return payload


def _check_user(payload):
    username = jwt_get_username_from_payload(payload)

    if not username:
        msg = _("Invalid payload.")
        raise GraphQLError(msg)

    # Make sure user exists
    try:
        user = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        msg = _("User doesn't exist.")
        raise GraphQLError(msg)

    if not user.is_active:
        msg = _("User account is disabled.")
        raise GraphQLError(msg)

    return user


class VerifyType(graphene.ObjectType):
    token = graphene.String()
    user = graphene.Field(UserType)


class Refresh(graphene.Mutation):
    token = graphene.String()
    user = graphene.Field(UserType)

    class Input:
        token = graphene.String()

    @graphene.resolve_only_args
    def mutate(root, token):
        payload = _check_payload(token)
        user = _check_user(payload)
        orig_iat = payload.get('orig_iat')

        if orig_iat:
            # Verify expiration
            refresh_limit = api_settings.JWT_REFRESH_EXPIRATION_DELTA

            if isinstance(refresh_limit, timedelta):
                refresh_limit = refresh_limit.days * 24 * 3600 + refresh_limit.seconds

            expiration_timestamp = orig_iat + int(refresh_limit)
            now_timestamp = timegm(datetime.utcnow().utctimetuple())

            if now_timestamp > expiration_timestamp:
                msg = _("Refresh has expired.")
                raise GraphQLError(msg)
        else:
            msg = _("orig_iat field is required.")
            raise GraphQLError(msg)

        new_payload = jwt_payload_handler(user)
        new_payload['orig_iat'] = orig_iat

        return Refresh(
            token=jwt_encode_handler(new_payload),
            user=user,
        )


class Query(graphene.AbstractType):
    jwtVerify = graphene.Field(VerifyType, token=graphene.String())

    @graphene.resolve_only_args
    def resolve_jwtVerify(self, token):
        payload = _check_payload(token)
        user = _check_user(payload)

        return VerifyType(
            token=token,
            user=user,
        )


class Mutation(graphene.AbstractType):
    jwtLogin = Login.Field()
    jwtRefresh = Refresh.Field()
