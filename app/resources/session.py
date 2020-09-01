import logging
import app.util.json as json
from app.util.session import get_session_cookie, validate_session
from app.exceptions.session import InvalidSessionError, UnauthorizedSession
from app.da.group import GroupMembershipDA, GroupDA

logger = logging.getLogger(__name__)

class SessionResource(object):

    # This call needs to only be allowed from the web presentation layer
    def on_get(self, req, resp, session_id):

        try:
            session = validate_session(session_id)
            resp.set_header('X-Auth-Session', session_id)
            resp.body = json.dumps(session, default_parser=json.parser)
        except InvalidSessionError as err:
            raise UnauthorizedSession() from err


class ValidateSessionResource(object):

    auth = {
        'exempt_methods': ['GET']
    }

    def on_get(self, req, resp):

        logger.debug('Request Cookies: {}'.format(req.cookies))

        session_id = get_session_cookie(req)

        logger.debug('Session ID: {}'.format(session_id))

        try:
            session = validate_session(session_id)
            room = req.get_param('room')
            self.__validate_session(session, room)

            resp.set_header('X-Auth-Session', session_id)
            resp.body = json.dumps(session, default_parser=json.parser)
        except InvalidSessionError as err:
            raise UnauthorizedSession() from err

    def __validate_session(self, session, room=None):
        logger.debug(f"Room check: {room}")
        if not room:
            return True

        try:
            # 1-21-Accel
            [group_leader_id, group_id, group_name] = room.split('-', 2)
            logger.debug(f"Room split: {[group_leader_id, group_id, group_name]}")

            group = GroupDA.get_group(group_id)
            if not group:
                raise InvalidSessionError

            if int(group['group_leader_id']) == session['member_id']:
                return True

            group_members = GroupMembershipDA().get_members_by_group_id(group_id)
            group_members = [m for m in group_members if m['member_id'] == session['member_id']]

            if len(group_members) == 0:
                raise InvalidSessionError
        except ValueError:
            return True
        return True
