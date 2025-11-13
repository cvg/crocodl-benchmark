import json

def same_configs(config, path):
    if not path.exists():
        return False
    config_existing = read_config(path)
    return config == config_existing


def read_config(path):
    with open(path, 'r') as fid:
        return json.load(fid)


def write_config(config, path):
    if not config: return
    with open(path, 'w') as fid:
        json.dump(config, fid, indent=4)


read_keyframes = read_config
write_keyframes = write_config
def same_keyframes(keyframes, path):
    if not keyframes and not path.exists():
        return True
    if not path.exists():
        return False
    old_keyframes = read_keyframes(path)
    if not keyframes and not old_keyframes:
        return True
    if not keyframes or not old_keyframes:
        return False
    keyframes = [tuple(k) for k in keyframes]
    old_keyframes = [tuple(k) for k in old_keyframes]
    return set(keyframes) == set(old_keyframes)