from collections import deque
from json import dump


def download(base_dir, api, peer_json):
    # from json import load
    # with open('users.json') as file:
    #     return load(file)

    user_ids = set()
    group_ids = set()

    queue = deque(peer_json)

    while queue:
        msg = queue.popleft()

        from_id = msg['from_id']
        eff_id = str(abs(from_id))

        if from_id < 0:
            group_ids.add(eff_id)
        else:
            user_ids.add(eff_id)

        if 'fwd_messages' in msg:
            queue.extend(msg['fwd_messages'])

    res = {'users': [], 'groups': []}

    if user_ids:
        res['users'].extend(api.users.get(user_ids=','.join(user_ids)))

    if group_ids:
        res['groups'].extend(api.groups.getById(group_ids=','.join(group_ids)))

    with open('users.json', 'w') as file:
        dump(res, file, indent=2)

    return res


class User:
    def __init__(self, json):
        self.id = json['id']
        self.name = json['first_name'] + ' ' + json['last_name']


class Group:
    def __init__(self, json):
        self.id = -json['id']
        self.name = json['name']


def parse(users_json):
    users = {}

    for json in users_json['users']:
        user = User(json)
        users[user.id] = user

    for json in users_json['groups']:
        user = Group(json)
        users[user.id] = user

    return users
