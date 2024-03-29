import logging
import multiprocessing
import importlib
import gunicorn.app.base

try:
    gevent_spec = importlib.util.find_spec(
        ".gevent.monkey", package="gevent")
    if gevent_spec is not None:
        import gevent.monkey
        gevent.monkey.patch_all()
except ModuleNotFoundError:
    pass


from pprint import pformat

from app import configure, create_app, start
from app.config import parser, settings


gunicorn.SERVER_SOFTWARE = "gunicorn"  # hide gunicorn version

LOCAL_ENVS = ["LOCAL", "DEV"]

logger = logging.getLogger(__name__)


class Application(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(Application, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def init_app():
    args = vars(parser.parse_args())
    # Get the configuration values from runtime/env/parameters
    # Essentially puts them in the settings variable
    configure(**args)
    return create_app()


def _post_fork(server=None, w=None):
    _config_logging()
    start()


def _config_logging():
    for logger in "gunicorn.access", "gunicorn.error":
        logging.getLogger(logger).propagate = True
        logging.getLogger(logger).handlers = []


if __name__ == "__main__":
    app = init_app()
    env_name = settings.get("ENV_NAME")
    default_workers = (multiprocessing.cpu_count() * 2) + 1
    opts = {
        "accesslog": settings.get("ACCESS_LOG"),
        "access_log_format": settings.get("ACCESS_LOG_FORMAT"),
        "bind": settings.get("BIND"),
        "errorlog": settings.get("ERROR_LOG"),
        "keepalive": settings.get("KEEP_ALIVE"),
        "post_fork": _post_fork,
        "preload": settings.get("GUNICORN_PRELOAD"),
        "proc_name": settings.get("APP_NAME"),
        "max_requests": settings.get("MAX_REQUESTS"),
        "max_requests_jitter": settings.get("MAX_REQUESTS_JITTER"),
        "worker_class": settings.get("WORKER_CLASS"),
        "workers": settings.get("WORKERS") or (1 if env_name in LOCAL_ENVS
                                               else default_workers)
    }

    if env_name in LOCAL_ENVS:
        opts["reload"] = True
        opts["timeout"] = 86400
        logger.debug(pformat(opts))

    Application(app, opts).run()
