import logging

import app.util.json as json
from app.da.activity import ActivityDA
from app.exceptions.session import InvalidSessionError, UnauthorizedSession
from app.util.session import get_session_cookie, validate_session

logger = logging.getLogger(__name__)

class ActivitiesResource(object):
    @staticmethod
    def on_get(req, resp):
        try:
            session_id = get_session_cookie(req)
            session = validate_session(session_id)
            member_id = session["member_id"]
            member_email = session["email"]
        except InvalidSessionError as err:
            raise UnauthorizedSession() from err
        if member_id:
            result = ActivityDA().get_recent_activity(member_id, member_email)
            if result: 
                resp.body = json.dumps({
                    "activities": result,
                    "message": "All activities",
                    "success": True
                }, default_parser=json.parser)
            else:
                resp.body = json.dumps({
                    "activities": {},
                    "message": "Failed to get activities",
                    "success": False
                }, default_parser=json.parser)
