from plog.models import (
    DBSession,
    User,
)


def groupfinder(userid, request):
    users = [i.username for i in DBSession.query(User).all()]
    if userid in users:
        user = DBSession.query(User).filter_by(username=userid).one()
        groups = [g.name for g in user.group]
        return groups