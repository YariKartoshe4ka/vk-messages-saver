from json import dump, load

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
        dump(peer, file)


def parse_peer_ids(peer_ids):
    res = set()

    for peer_id in peer_ids.split(','):
        if not peer_id:
            continue

        if peer_id[0] == 'c' and peer_id[1:].isdigit():
            res.add(2000000000 + int(peer_id[1:]))
        elif peer_id.isdigit() or peer_id[0] == '-' and peer_id[1:].isdigit():
            res.add(int(peer_id))
        else:
            raise ValueError('Invalid peer ID: ' + peer_id)

    return res
