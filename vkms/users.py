from collections import deque


def download(base_dir, api, peer_id, peer):
    user_ids = set()
    group_ids = set()

    queue = deque(peer['messages'])

    if int(peer_id) < 2000000000:
        queue.append({'from_id': int(peer_id)})

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

    peer['members'] = res


def parse(peer):
    users = {}

    for json in peer['members']['users']:
        users[json['id']] = json['first_name'] + ' ' + json['last_name']

    for json in peer['members']['groups']:
        users[-json['id']] = json['name']

    return users
