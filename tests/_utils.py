def check_two_dicts(a: dict, b: dict) -> bool:
    return all((k in a and a[k] == v for k, v in b.items()))
