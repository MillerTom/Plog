import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from plog.models import (
    DBSession,
    Post,
    User,
    Group,
    Permission,
    Base,
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        post = Post(title='Hello World', body='First post of Plog project.')
        DBSession.add(post)
        user = User(username='admin', password='admin', email='admin@example.com')
        permission = Permission('edit')
        permission2 = Permission('view')
        user.group.append(Group('admins', permission=permission))
        DBSession.add(user)
        DBSession.add(permission2)