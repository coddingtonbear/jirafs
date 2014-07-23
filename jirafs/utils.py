import getpass
import os

from jira.client import JIRA
from six.moves import configparser, input

from . import constants


def convert_to_boolean(string):
    if string.upper().strip() in ['Y', 'YES']:
        return True
    elif string.upper().strip() in ['N', 'NO']:
        return False
    return None


def get_user_input(message, options=None, boolean=False, password=False):
    value = None
    while value is None:
        if not password:
            raw_value = input(message + " ")
        else:
            raw_value = getpass.getpass(message + " ")

        if options and raw_value not in options:
            print("'%s' is not a valid response" % raw_value)
            continue
        elif boolean:
            result = convert_to_boolean(raw_value)
            if result is not None:
                value = result
            else:
                print("'%s' is not a valid response" % raw_value)
        elif raw_value.strip():
            value = raw_value
        else:
            print("Please enter a response")

    return value


def get_config(additional_configs=None):
    filenames = [
        os.path.expanduser('~/%s' % constants.GLOBAL_CONFIG)
    ]
    if additional_configs:
        filenames.append(additional_configs)

    parser = configparser.ConfigParser()
    parser.read(filenames)
    return parser


def get_default_jira_server():
    config = get_config()

    if not config.has_section(constants.CONFIG_JIRA):
        config.add_section(constants.CONFIG_JIRA)

    if not config.has_option(constants.CONFIG_JIRA, 'server'):
        value = get_user_input(
            "Default JIRA URL: "
        )
        config.set(constants.CONFIG_JIRA, 'server', value)

    with open(
            os.path.expanduser('~/%s' % constants.GLOBAL_CONFIG), 'w'
    ) as global_config:
        config.write(global_config)

    return config.get(constants.CONFIG_JIRA, 'server')


def get_jira(domain=None):
    # Must happen before loading config; we may be making changes
    default_domain = get_default_jira_server()
    config = get_config()

    login_data = {}

    if domain is None:
        section = constants.CONFIG_JIRA
    elif default_domain == domain:
        section = constants.CONFIG_JIRA
    else:
        section = domain

    if not config.has_section(section):
        config.add_section(section)

    if domain is not None:
        login_data['server'] = domain
    else:
        login_data['server'] = default_domain

    if not config.has_option(section, 'username'):
        value = get_user_input(
            "JIRA Username (%s):" % login_data['server']
        )
        login_data['username'] = value
        config.set(section, 'username', value)
    else:
        login_data['username'] = config.get(section, 'username')

    if not config.has_option(section, 'password'):
        value = get_user_input(
            "JIRA Password (%s):" % login_data['server'],
            password=True,
        )
        login_data['password'] = value

        save = get_user_input("Save JIRA Password (Y/N)?", boolean=True)
        if save:
            config.set(section, 'password', value)
    else:
        login_data['password'] = config.get(section, 'password')

    basic_auth = (
        login_data.pop('username'),
        login_data.pop('password'),
    )
    jira = JIRA(login_data, basic_auth=basic_auth)

    with open(
            os.path.expanduser('~/%s' % constants.GLOBAL_CONFIG), 'w'
    ) as global_config:
        config.write(global_config)

    return jira


def lazy_get_jira():
    return lambda domain: get_jira(domain)
