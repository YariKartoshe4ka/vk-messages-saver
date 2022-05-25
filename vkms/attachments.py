import os
from operator import itemgetter
from urllib.parse import urlparse

from pathvalidate import sanitize_filename
from requests import get


def download(out_dir, msgs):
    os.makedirs(f'{out_dir}/attachments/', exist_ok=True)

    for msg in msgs:
        for atch in msg.atchs:
            if isinstance(atch, FileAttachment):
                atch.download(out_dir)


class Attachment:
    tp = 'unknown'

    def __init__(self, json):  # noqa: U100
        pass


class FileAttachment(Attachment):
    url = None
    pf_dir = None
    filename = None

    def download(self, out_dir):
        os.makedirs(f'{out_dir}/attachments/{self.pf_dir}/', exist_ok=True)

        path = f'{out_dir}/attachments/{self.pf_dir}/{self.filename}'

        with open(path, 'wb') as file:
            file.write(get(self.url).content)


class Photo(FileAttachment):
    tp = 'photo'
    pf_dir = 'photos'

    def __init__(self, json):
        self.url = max(json['sizes'], key=itemgetter('width', 'height'))['url']
        self.filename = f"{json['owner_id']}_{json['id']}.jpg"


class Video(Attachment):
    tp = 'video'

    def __init__(self, json):
        self.filename = sanitize_filename(
            f"{json['title']}_{json['owner_id']}_{json['id']}.mp4",
            replacement_text='_'
        )


class Audio(Attachment):
    tp = 'audio'

    def __init__(self, json):
        self.title = f"{json['artist']} - {json['title']}"


class Document(FileAttachment):
    tp = 'doc'
    pf_dir = 'documents'

    def __init__(self, json):
        self.url = json['url']
        self.filename = sanitize_filename(
            f"{json['title']}_{json['owner_id']}_{json['id']}.{json['ext']}",
            replacement_text='_'
        )


class Link(Attachment):
    tp = 'link'

    def __init__(self, json):
        self.title = json['title']
        self.url = json['url']


class Wall(Attachment):
    tp = 'wall'

    def __init__(self, json):
        self.url = f"vk.com/wall{json['from_id']}_{json['id']}"


class WallReply(Attachment):
    tp = 'wall_reply'

    def __init__(self, json):
        self.url = f"vk.com/wall{json['owner_id']}_{json['post_id']}?reply={json['id']}"


class Sticker(FileAttachment):
    tp = 'sticker'
    pf_dir = 'stickers'

    def __init__(self, json):
        self.url = max(json['images'], key=itemgetter('width', 'height'))['url']
        self.filename = f"{json['product_id']}_{json['sticker_id']}.png"


class Gift(FileAttachment):
    tp = 'gift'
    pf_dir = 'gifts'

    def __init__(self, json):
        self.url = json['thumb_256']
        self.filename = str(json['id']) + os.path.splitext(urlparse(self.url).path)[1]


class AudioMessage(FileAttachment):
    tp = 'audio_message'
    pf_dir = 'audio_messages'

    def __init__(self, json):
        self.url = json['link_mp3']
        self.filename = f"{json['owner_id']}_{json['id']}.mp3"


class Graffiti(FileAttachment):
    tp = 'graffiti'
    pf_dir = 'graffiti'

    def __init__(self, json):
        self.url = json['url']
        self.filename = f"{json['owner_id']}_{json['id']}.png"


class Poll(Attachment):
    tp = 'poll'

    def __init__(self, json):
        self.title = json['question']
        self.mult = 'несколько вариантов' if json['multiple'] else 'один вариант'
        self.anon = 'анонимный' if json['anonymous'] else 'публичный'
        self.all_votes = json['votes']
        self.answers = json['answers']
        self.answer_ids = set(json['answer_ids'])


_attachments = {
    atch.tp: atch
    for atch in Attachment.__subclasses__() + FileAttachment.__subclasses__()
}


def gen_attachment(json):
    return _attachments.get(json['type'], Attachment)(json[json['type']])
