import settings


def get_first_int(values, key, default=0):
    found = values.get(key, 0)
    if found:
        found = int(found)
    else:
        found = default
    return found


def get_config_value(key, selector_config=None):
    # ToDo: rewrite - test will fail if 0 or None was passed...
    if selector_config is None:
        selector_config = settings.DEFAULT_CONFIG
    found = selector_config.get(key)
    if found:
        found = int(found)
    else:
        found = int(settings.DEFAULT_CONFIG[key])
    return found


def no_op(num):
    return num
