from json import load, dump


months = [
    ' ', 'января', 'февраля', 'марта',
    'апреля', 'мая', 'июня', 'июля',
    'августа', 'сентября', 'октября',
    'ноября', 'декабря'
]


def load_peer(out_dir, peer_id):
    with open(f'{out_dir}/.json/{peer_id}.json', 'r') as file:
        return load(file)


def dump_peer(out_dir, peer_id, peer):
    with open(f'{out_dir}/.json/{peer_id}.json', 'w') as file:
        dump(peer, file, indent=2)
