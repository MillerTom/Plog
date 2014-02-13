from pyramid.response import Response
from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError

from plog.models import (
    DBSession,
    Post,
    User,
    Group,
)

from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
)

from passlib.hash import sha256_crypt
from slugify import slugify

conn_err_msg = 'Plog is having a problem using your SQL database.'


@view_config(route_name='home', renderer='home.jinja2')
def home_view(request):
    try:
        posts = DBSession.query(Post).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'posts': posts,
            'project': 'Plog',
            'logged_in': authenticated_userid(request)}


@view_config(route_name='post', renderer='post.jinja2', permission='view')
def post_view(request):
    try:
        post = DBSession.query(Post).filter_by(slug=request.matchdict['slug']).first()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return {'post': post,
            'project': 'Plog',
            'logged_in': authenticated_userid(request)}


@view_config(route_name='add_post', renderer='add_post.jinja2', permission='edit')
def add_post(request):
    token = request.session.get_csrf_token()
    if request.method == 'POST':
        if token == request.params['csrf_token']:
            title = request.params['title']
            body = request.params['body']
            post = Post(title, body)
            DBSession.add(post)
            return HTTPFound(location=request.route_url('post', slug=post.slug))
        else:
            raise ValueError('CSRF token did not match!')
    else:
        return {'project': 'Plog',
                'token': token,
                'logged_in': authenticated_userid(request)}


@view_config(route_name='edit_post', renderer='edit_post.jinja2', permission='edit')
def edit_post(request):
    slug = request.matchdict['slug']
    post = DBSession.query(Post).filter_by(slug=slug).one()
    if request.method == 'POST':
        post.title = request.params['title']
        post.slug = slugify(request.params['title'])
        post.body = request.params['body']
        DBSession.add(post)
        return HTTPFound(location=request.route_url('post', slug=post.slug))
    else:
        return {'project': 'Plog',
                'post': post,
                'logged_in': authenticated_userid(request)}


@view_config(route_name='delete_post', permission='edit')
def delete_post(request):
    slug = request.matchdict['slug']
    post = DBSession.query(Post).filter_by(slug=slug).one()
    DBSession.delete(post)
    return HTTPFound(location=request.route_url('admin'))


@view_config(route_name='login', renderer='login.jinja2')
@forbidden_view_config(renderer='login.jinja2')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'
    came_from = request.params.get('came_from', referrer)
    message = ''
    login_name = ''
    password = ''
    context = dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from,
        login=login_name,
        password=password,
    )
    if 'form.submitted' in request.params:
        login_name = request.params['login']
        password = request.params['password']
        user = DBSession.query(User).filter_by(username=login_name).first()
        try:
            if sha256_crypt.verify(password, user.password):
                headers = remember(request, login_name)
                return HTTPFound(location=came_from, headers=headers)
        except AttributeError:
            context['message'] = 'No such user!'
            return context
        context['message'] = 'Wrong password!'

    return context


@view_config(route_name='add_user', renderer='add_user.jinja2', permission='edit')
def add_user(request):
    token = request.session.get_csrf_token()
    groups = DBSession.query(Group).all()
    if request.method == 'POST':
        if token == request.params['csrf_token']:
            username = request.params['username']
            password = request.params['password']
            email = request.params['email']
            group_name = request.params['group_name']
            user = User(username=username, password=password, email=email)
            group = DBSession.query(Group).filter_by(name=group_name).one()
            user.group.append(group)
            DBSession.add(user)
            return HTTPFound(location=request.route_url('admin'))
        else:
            raise ValueError('CSRF token did not match!')
    else:
        return {'project': 'Plog',
                'logged_in': authenticated_userid(request),
                'token': token,
                'groups': groups}


@view_config(route_name='edit_user', renderer='edit_user.jinja2', permission='edit')
def edit_user(request):
    token = request.session.get_csrf_token()
    username = request.matchdict['username']
    user = DBSession.query(User).filter_by(username=username).one()
    groups = group = DBSession.query(Group).all()
    if request.method == 'POST':
        if token == request.params['csrf_token']:
            user.username = request.params['username']
            #user.password = request.params['password']
            user.email = request.params['email']
            group_name = request.params['group_name']
            group = DBSession.query(Group).filter_by(name=group_name).one()
            user.group[:] = []
            user.group.append(group)
            DBSession.add(user)
            return HTTPFound(location=request.route_url('admin'))
    else:
        return {'project': 'Plog',
                'user': user,
                'groups': groups,
                'logged_in': authenticated_userid(request),
                'token': token}




@view_config(route_name='profile', renderer='profile.jinja2', permission='edit')
def profile(request):
    u_name = request.matchdict['username']
    user = DBSession.query(User).filter_by(username=u_name).one()
    group = user.group
    return {'user': user,
            'group': group,
            'logged_in': authenticated_userid(request)}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('home'), headers=headers)


@view_config(route_name='admin', renderer='admin.jinja2', permission='edit')
def admin(request):
    if request.method == 'POST':
        group_name = request.params['group_name']
        group = Group(group_name)
        DBSession.add(group)

    posts = DBSession.query(Post).all()
    users = DBSession.query(User).all()
    groups = DBSession.query(Group).all()
    return {'project': 'Plog',
            'logged_in': authenticated_userid(request),
            'posts': posts,
            'users': users,
            'groups': groups}