import unittest
import transaction

from pyramid import testing


def _init_testing_db():
    from sqlalchemy import create_engine
    from .models import (
        DBSession,
        Post,
        Base
    )
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
    with transaction.manager:
        model = Post('Test Post', 'This is the test post')
        DBSession.add(model)
    return DBSession


def _register_routes(config):
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('admin', '/admin')
    config.add_route('add_post', '/post/add')
    config.add_route('add_user', '/user/add')
    config.add_route('add_group', '/group/add')
    config.add_route('del_group', '/group/del/{group_name}')
    config.add_route('del_user', '/user/del/{username}')
    config.add_route('profile', '/user/profile/{username}')
    config.add_route('edit_user', '/user/edit/{username}')
    config.add_route('edit_post', '/post/edit/{slug}')
    config.add_route('delete_post', '/post/del/{slug}')
    config.add_route('post', '/post/{slug}')


class PostModelTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()

    def tearDown(self):
        self.session.remove()

    @staticmethod
    def _get_target_class():
        from .models import Post
        return Post

    def _makeOne(self, title='Some Title', body='some data'):
        return self._get_target_class()(title, body)

    def test_constructor(self):
        instance = self._makeOne()
        self.assertEqual(instance.title, 'Some Title')
        self.assertEqual(instance.slug, 'some-title')
        self.assertEqual(instance.body, 'some data')


class ViewPostTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import post_view
        return post_view(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['slug'] = 'test-post'
        response = self._call_fut(request)
        self.assertEqual(response['post'].title, 'Test Post')
        self.assertEqual(response['post'].body, 'This is the test post')


class AddPostTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import add_post
        return add_post(request)

    def test_it_notsubmitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        info = self._call_fut(request)
        self.assertEqual(info['project'], 'Plog')

    def test_it_submitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = request.session.get_csrf_token()
        request.params['title'] = 'Another Post'
        request.params['body'] = 'Post body'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/post/another-post')


class EditPostTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import edit_post
        return edit_post(request)

    def test_it_notsubmitted(self):
        from .models import Post
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['slug'] = 'abc'
        post = Post('abc', 'hello')
        self.session.add(post)
        info = self._call_fut(request)
        self.assertEqual(info['post'], post)

    def test_it_submitted(self):
        from .models import Post
        _register_routes(self.config)
        post = Post('Some Title', 'Some content')
        self.session.add(post)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.matchdict['slug'] = post.slug
        request.params['title'] = 'New Title'
        request.params['body'] = 'New body'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/post/new-title')


class DeletePostTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import delete_post
        return delete_post(request)

    def test_it(self):
        from .models import Post
        _register_routes(self.config)
        post = Post('Some Title', 'Some content')
        self.session.add(post)
        request = testing.DummyRequest()
        request.matchdict['slug'] = post.slug
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')


class UserModelTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()

    def tearDown(self):
        self.session.remove()

    @staticmethod
    def _get_target_class():
        from .models import User
        return User

    def _makeOne(self, username='testuser', password='password', email='test@example.com'):
        return self._get_target_class()(username, password, email)

    def test_constructor(self):
        import passlib.hash
        instance = self._makeOne()
        self.assertEqual(instance.username, 'testuser')
        self.assertTrue(passlib.hash.sha256_crypt.verify('password', instance.password))
        self.assertEqual(instance.email, 'test@example.com')


class AddUserTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import add_user
        return add_user(request)

    def test_it_notsubmitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        info = self._call_fut(request)
        self.assertEqual(info['project'], 'Plog')

    def test_it_submitted(self):
        from .models import Group, Permission
        _register_routes(self.config)
        permission = Permission('view')
        self.session.add(permission)
        group = Group('users', permission)
        self.session.add(group)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = request.session.get_csrf_token()
        request.params['username'] = 'testuser'
        request.params['password'] = 'password'
        request.params['email'] = 'test@example.com'
        request.params['group_name'] = 'users'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')


class GroupModelTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()

    def tearDown(self):
        self.session.remove()

    @staticmethod
    def _get_target_class():
        from .models import Group
        return Group

    def _makeOne(self, name='users',):
        from .models import Permission
        permission = Permission('users')
        return self._get_target_class()(name, permission=permission)

    def test_constructor(self):
        instance = self._makeOne()
        self.assertEqual(instance.name, 'users')
        self.assertEqual(instance.permission.name, 'users')