from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from plog.security import groupfinder
from uuid import uuid4

from plog.models import (
    DBSession,
    Base,
)
sf = UnencryptedCookieSessionFactoryConfig(uuid4().__str__())


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    authn_policy = AuthTktAuthenticationPolicy(
        uuid4().__str__(), callback=groupfinder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings, root_factory='plog.models.RootFactory', session_factory=sf)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path("plog:templates")
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('admin', '/admin')
    config.add_route('add_post', '/add')
    config.add_route('add_user', '/new-user')
    config.add_route('edit_user', '/user/{username}')
    config.add_route('profile', '/profile/{username}')
    config.add_route('edit_post', '/edit/{slug}')
    config.add_route('delete_post', '/delete/{slug}')
    config.add_route('post', '/{slug}')
    config.scan()
    return config.make_wsgi_app()
