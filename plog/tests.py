import unittest
import transaction

from pyramid import testing


def _init_testing_db():
    from sqlalchemy import create_engine
    from .models import (
        DBSession,
        Post,
        Permission,
        Group,
        User,
        Base
    )
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
    with transaction.manager:
        post = Post('Test Post', 'This is the test post')
        DBSession.add(post)
        permission = Permission('test_permission')
        DBSession.add(permission)
        group = Group('A group', permission)
        DBSession.add(group)
        user = User('test_user', 'password', 'test@example.com')
        user.group.append(group)
        DBSession.add(user)
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
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
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

    def test_it_with_wrong_token(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = 'wrong token'
        response = self._call_fut(request)
        self.assertEqual(response.status, '403 Forbidden')


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
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['slug'] = 'test-post'
        info = self._call_fut(request)
        self.assertEqual(info['post'].title, 'Test Post')

    def test_it_submitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.matchdict['slug'] = 'test-post'
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
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['slug'] = 'test-post'
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

    def _makeOne(self, username='testuser', password='password', email='testuser@example.com'):
        return self._get_target_class()(username, password, email)

    def test_constructor(self):
        import passlib.hash
        instance = self._makeOne()
        self.assertEqual(instance.username, 'testuser')
        self.assertTrue(passlib.hash.sha256_crypt.verify('password', instance.password))
        self.assertEqual(instance.email, 'testuser@example.com')


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
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = request.session.get_csrf_token()
        request.params['username'] = 'testuser'
        request.params['password'] = 'password'
        request.params['email'] = 'test@example.com'
        request.params['group_name'] = 'A group'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')

    def test_it_with_wrong_token(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = 'wrong token'
        response = self._call_fut(request)
        self.assertEqual(response.status, '403 Forbidden')


class EditUserTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import edit_user
        return edit_user(request)

    def test_it_notsubmitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['username'] = 'test_user'
        response = self._call_fut(request)
        self.assertEqual(response['user'].email, 'test@example.com')

    def test_it_submitted(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = request.session.get_csrf_token()
        request.params['username'] = 'new_username'
        request.params['email'] = 'new_mail@example.com'
        request.params['group_name'] = 'A group'
        request.matchdict['username'] = 'test_user'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')

    def test_it_with_wrong_token(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.matchdict['username'] = 'test_user'
        request.params['csrf_token'] = 'wrong token'
        response = self._call_fut(request)
        self.assertEqual(response.status, '403 Forbidden')


class DeleteUserTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import del_user
        return del_user(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['username'] = 'test_user'
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


class AddGroupTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import add_group
        return add_group(request)

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
        request.params['group_name'] = 'Test Group'
        request.params['permission_name'] = 'test_permission'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')

    def test_it_with_wrong_token(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.method = 'POST'
        request.params['csrf_token'] = 'wrong token'
        response = self._call_fut(request)
        self.assertEqual(response.status, '403 Forbidden')


class DeleteGroupTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import del_group
        return del_group(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        request.matchdict['group_name'] = 'A group'
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')


class HomeViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import home_view
        return home_view(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        response = self._call_fut(request)
        self.assertEqual(len(response['posts']), 1)


class ProfileViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import profile
        return profile(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.matchdict['username'] = 'test_user'
        response = self._call_fut(request)
        self.assertEqual(response['user'].username, 'test_user')


class LogoutViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import logout
        return logout(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        response = self._call_fut(request)
        self.assertEqual(response.location, 'http://example.com/admin')


class AdminViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _init_testing_db()
        self.config = testing.setUp()

    def tearDown(self):
        self.session.remove()
        testing.tearDown()

    @staticmethod
    def _call_fut(request):
        from .views import admin
        return admin(request)

    def test_it(self):
        _register_routes(self.config)
        request = testing.DummyRequest()
        response = self._call_fut(request)
        self.assertEqual(len(response['posts']), 1)
        self.assertIsNotNone(response['users'])
        self.assertIsNotNone(response['groups'])