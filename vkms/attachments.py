from hashlib import sha1
from operator import itemgetter
from os import makedirs

from requests import get


def download(out_dir, msgs):
    for msg in msgs:
        for atch in msg.atchs:
            atch.download(out_dir)


class Attachment:
    tp = 'unknown'
    url = None
    pf_dir = None

    def __init__(self, json):
        json

    def download(self, out_dir):
        if self.pf_dir is None:
            return

        makedirs(f'{out_dir}/{self.pf_dir}/', exist_ok=True)

        with open(f'{out_dir}/{self.pf_dir}/{self.hash}.jpg', 'wb') as file:
            file.write(get(self.url).content)


class Photo(Attachment):
    tp = 'photo'
    pf_dir = 'photos'

    def __init__(self, json):
        json['sizes'].sort(key=itemgetter('width', 'height'))
        self.url = json['sizes'][-1]['url']
        self.hash = sha1(self.url.encode('utf-8')).hexdigest()


class AudioMessage(Attachment):
    tp = 'audio_message'
    pf_dir = 'audio_messages'

    def __init__(self, json):
        self.url = json['link_mp3']
        self.hash = sha1(self.url.encode('utf-8')).hexdigest()


class Wall(Attachment):
    tp = 'wall'

    def __init__(self, json):
        self.url = f"vk.com/wall{json['from_id']}_{json['id']}"


_attachments = {atch.tp: atch for atch in Attachment.__subclasses__()}


def gen_attachment(json):
    return _attachments.get(json['type'], Attachment)(json[json['type']])
