import logging

import falcon
import falcon.status_codes as status_codes
import traceback

logger = logging.getLogger(__name__)


class HTTPError(falcon.HTTPError):
    def __init__(self, status, description, **kwargs):
        http_status = "HTTP_{}".format(status)
        if hasattr(status_codes, http_status):
            title = getattr(status_codes, http_status)
        else:
            raise ValueError("Status code '{}' does not exist!".format(http_status))
        super(HTTPError, self).__init__(title, title, str(description), **kwargs)


def error_handler(ex, req, resp, params):
    logger.debug('Exception Happened in Request:')
    logger.debug(traceback.format_exc())
    if not isinstance(ex, falcon.HTTPError) and not isinstance(ex, falcon.HTTPStatus):
        logger.exception("Unhandled error while processing request: {}".format(ex))
        raise HTTPError(500, str(ex))
    else:
        raise ex
