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
    """
    Абстрактный класс для представления любого объекта `attachment` из JSON
    Документация: [https://dev.vk.com/reference/objects/attachments-message]

    Args:
        json (dict): Объект вложения, полученный ранее благодаря VK API
    """

    # Уникальный тип вложения
    tp = 'unknown'

    def __init__(self, json):  # noqa: U100
        pass


class FileAttachment(Attachment):
    """
    Абстрактный подкласс `Attachment` для представления вложения,
    которое можно скачать (фото, документ и т.п.)
    """

    # Ссылка на загрузку файла
    url = None

    # Название директории, в которую будут сохраняться вложения этого типа
    pf_dir = None

    # Имя файла, под которым вложение будет сохранено (уникальное для каждого вложения)
    filename = None

    def download(self, out_dir):
        """
        Загружает и сохраняет вложение

        Args:
            out_dir (str): Абсолютный путь к каталогу, в котором находится
                результат работы программы
        """

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


class Call(Attachment):
    tp = 'call'

    def __init__(self, json):
        self.initiator_id = json['initiator_id']

        self.call_type = ''

        if json['receiver_id'] > 2000000000:
            self.call_type += 'групповой '

        if json['video']:
            self.call_type += 'видео'

        self.state = json['state']

        self.duration = '{M}:{S}'.format(
            M=json['duration'] // 60,
            S=str(json['duration'] % 60).zfill(2)
        )

    def get_state(self, owner_id):
        if self.state == 'reached':
            return 'завершен'

        if owner_id == self.initiator_id:
            if self.state == 'canceled_by_initiator':
                return 'отменен'

            if self.state == 'canceled_by_receiver':
                return 'отклонен'

        else:
            if self.state == 'canceled_by_initiator':
                return 'пропущен'

            if self.state == 'canceled_by_receiver':
                return 'отменен'


class Poll(Attachment):
    tp = 'poll'

    def __init__(self, json):
        self.title = json['question']
        self.mult = 'несколько вариантов' if json['multiple'] else 'один вариант'
        self.anon = 'анонимный' if json['anonymous'] else 'публичный'
        self.all_votes = json['votes']
        self.answers = json['answers']
        self.answer_ids = set(json['answer_ids'])


# Словарь формата тип-вложение для более быстрого создания вложений
_attachments = {
    atch.tp: atch
    for atch in Attachment.__subclasses__() + FileAttachment.__subclasses__()
}


def gen_attachment(json):
    """
    Генерирует вложение по его JSON

    Args:
        json (dict): Объект вложения, полученный ранее благодаря VK API

    Returns:
        Attachment: Сгенерированный объект вложения
    """
    return _attachments.get(json['type'], Attachment)(json[json['type']])
