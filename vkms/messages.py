import datetime

from .attachments import gen_attachment
from .utils import months


def download(base_dir, api, peer_id, peer):
    with open(f'{base_dir}/vkscripts/messages.js', 'r') as file:
        code_tpl = file.read()

    code = code_tpl \
        .replace('PEERID', peer_id) \
        .replace('PROCESSED', '0')

    res = api.execute(code=code)
    msgs = res['messages']

    while res['processed'] < res['count']:
        code = code_tpl \
            .replace('PEERID', peer_id) \
            .replace('PROCESSED', res['processed'])

        res = api.execute(code=code)
        msgs += res['messages']

    msgs.reverse()
    peer['messages'] = msgs


def parse(peer, usernames):
    _msgs.clear()
    return [gen_message(msg, usernames) for msg in peer['messages']]


_msgs = {}


def gen_message(json, usernames):
    msg_id = Message.get_id_by_json(json)

    if msg_id not in _msgs:
        _msgs[msg_id] = Message(json, usernames)

    return _msgs[msg_id]


class Message:
    def __init__(self, json, usernames):
        self.id = Message.get_id_by_json(json)
        self.username = usernames[json['from_id']]

        self.date = datetime.datetime.fromtimestamp(json['date'])
        self.text = json['text']

        self.fwd_msgs = [
            gen_message(fwd_msg_json, usernames)
            for fwd_msg_json in json.get('fwd_messages', [])
        ]
        self.atchs = [
            gen_attachment(atch_json)
            for atch_json in json['attachments']
        ]

    @staticmethod
    def get_id_by_json(json):
        return '_'.join(map(str, (
            json['date'],
            json['from_id'],
            json['conversation_message_id']
        )))

    def full_date(self):
        return self.date.strftime('%d {} %Y'.format(months[self.date.month]))

    def time(self):
        return self.date.strftime('%H:%M')
