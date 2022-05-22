import datetime
from json import dump
from operator import itemgetter
from hashlib import md5


def download(base_dir, api, peer_id):
    # from json import load
    # with open(f'{peer_id}.json') as file:
    #     return load(file)

    with open(f'{base_dir}/vkscripts/save.js', 'r') as file:
        code_template = file.read()

    code = code_template \
        .replace('PEERID', peer_id) \
        .replace('PROCESSED', '0')

    response = api.execute(code=code)
    messages = response['messages']

    while response['processed'] < response['count']:
        code = code_template \
            .replace('PEERID', peer_id) \
            .replace('PROCESSED', response['processed'])

        response = api.execute(code=code)
        messages += response['messages']

    with open(f'{peer_id}.json', 'w') as file:
        dump(messages, file, indent=2)

    return messages


class Message:
    _months = [
        ' ', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]

    def __init__(self, json, users):
        self.user = users[json['from_id']]

        # self.id = f"{json['peer_id']}_{json['conversation_message_id']}"
        # else:
        self.id = f"{json['from_id']}_{json['conversation_message_id']}"

        self.date = datetime.datetime.fromtimestamp(json['date'])
        self.text = json['text']

        self.fwd_msgs = [gen_message(fwd_msg_json, users) for fwd_msg_json in json.get('fwd_messages', [])]
        self.attachments = [get_attachment(at) for at in json['attachments']]

    @staticmethod
    def get_id_by_json(json):
        return f"{json['from_id']}_{json['conversation_message_id']}"

    def full_date(self):
        return self.date.strftime('%d {month} %Y'.format(month=self._months[self.date.month]))

    def time(self):
        return self.date.strftime('%H:%M')


parsed = {}


class AttachmentPhoto:
    def __init__(self, json):
        json['sizes'].sort(key=itemgetter('width', 'height'))
        self.url = json['sizes'][-1]['url']

    def __str__(self):
        return f"[фото: {md5(self.url.encode('utf-8')).hexdigest()}]"


class AttachmentWall:
    def __init__(self, json):
        self.url = f"vk.com/wall{json['from_id']}_{json['id']}"

    def __str__(self):
        return f"[пост: {self.url}]"

class Attachment:
    def __init__(self, json):
        pass

    def __str__(self):
        return '{unknown attachment}'


_attachments = {
    'photo': AttachmentPhoto,
    'wall': AttachmentWall
}


def get_attachment(json):
    return _attachments.get(json['type'], Attachment)(json[json['type']])


def gen_message(json, all_users):
    msg_id = Message.get_id_by_json(json)

    if msg_id not in parsed:
        parsed[msg_id] = Message(json, all_users)

    return parsed[msg_id]


def parse(peer_json, all_users):
    msgs = []

    for msg in reversed(peer_json):
        msgs.append(gen_message(msg, all_users))

    return parsed, msgs
