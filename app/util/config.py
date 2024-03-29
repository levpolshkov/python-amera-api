import os
import logging
from vyper import v

settings = v
logger = logging.getLogger(__name__)


def _get_default_args(args):
    return {k: args.get_default(k) for k in _get_args(args).keys()}


def _get_args(args):
    return vars(args.parse_known_args()[0])


def _setup_args(args):
    defaults = _get_default_args(args)
    args_dict = _get_args(args)
    for k, val in defaults.items():
        v.set_default(k, val)
        if v.get(k) != args_dict[k]:
            v.bind_arg(k, args_dict[k])


def _setup_overrides(overrides):
    for k, val in overrides.items():
        v.set(k, val)


def setup_vyper(parser, overrides):
    defaults = _get_default_args(parser)

    actual_overrides = \
        {k: val for k, val in overrides.items() if defaults[k] != val}

    _setup_args(parser)
    _setup_overrides(actual_overrides)

    env_prefix = v.get("environment_variables_prefix")
    # env_name = os.getenv(f"{env_prefix.upper()}_ENV_NAME", "LOCAL").lower()
    # print(f"VYPER ENV_NAME_ENV: {env_name}")
    v.set_env_prefix(env_prefix)
    v.set_env_key_replacer("-", "_")
    v.automatic_env()

    env_name = v.get('env_name')
    config_name = "config"
    if env_name.lower() == "local":
        config_name = f"config.local"

    print(f"VYPER ENV_NAME: {env_name}")
    print(f"VYPER CONFIG_NAME: {config_name}")
    logger.debug("VYPER ENV_NAME: {}".format(env_name))
    logger.debug("VYPER CONFIG_NAME: {}".format(config_name))

    v.add_config_path("config/local")
    v.add_config_path("config/build")
    v.set_config_type("toml")
    v.set_config_name(config_name)
    v.read_in_config()
    # Override logging for Vyper only
    logging.getLogger("vyper").setLevel(logging.ERROR)
