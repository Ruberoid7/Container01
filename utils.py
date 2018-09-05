def get_first_int(values, key, default=0):
    found = values.get(key, 0)
    if found:
        found = int(found)
    else:
        found = default
    return found
