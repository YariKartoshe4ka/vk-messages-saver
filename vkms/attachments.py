from hashlib import sha1
from operator import itemgetter


class AttachmentPhoto:
    def __init__(self, json):
        json['sizes'].sort(key=itemgetter('width', 'height'))
        self.url = json['sizes'][-1]['url']

    def __str__(self):
        return f"[фото: {sha1(self.url.encode('utf-8')).hexdigest()}]"


class AttachmentWall:
    def __init__(self, json):
        self.url = f"vk.com/wall{json['from_id']}_{json['id']}"

    def __str__(self):
        return f"[пост: {self.url}]"


class Attachment:
    url = None

    def __str__(self):
        return '{unknown attachment}'


_attachments = {
    'photo': AttachmentPhoto,
    'wall': AttachmentWall
}


def gen_attachment(json):
    return _attachments.get(json['type'], Attachment)(json[json['type']])
