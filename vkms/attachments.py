import logging
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait
from operator import itemgetter

from pathvalidate import sanitize_filename
from requests import get
from requests.exceptions import RequestException

log = logging.getLogger(__name__)


def download(out_dir, peer, nthreads, types):
    """
    Скачивает указанные переписки в формате JSON (результаты обращений к VK API)

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer (peers.Peer): Объект переписки
        nthreads (int): Количество потоков, загружающих вложения
    """
    # Создаем папку для хранения вложений
    (out_dir / 'attachments').mkdir(parents=True, exist_ok=True)

    # Обход сообщений в ширину
    queue = deque(peer.msgs)

    with ThreadPoolExecutor(nthreads, 'Thread-') as executor:
        tasks = []

        while queue:
            msg = queue.popleft()

            # Добавляем все скачиваемые вложения
            for atch in msg.atchs:
                if class_to_name.get(atch.__class__) in types:
                    tasks.append(executor.submit(atch.download, out_dir))

            # Если у сообщения есть пересланные, то добавляем их в очередь
            if msg.fwd_msgs:
                queue.extend(msg.fwd_msgs)

            if msg.reply_msg:
                queue.append(msg.reply_msg)

        wait(tasks)


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

    def get_path(self, out_dir):
        return (out_dir / 'attachments' / self.pf_dir / self.filename).resolve()

    def download(self, out_dir):
        """
        Загружает и сохраняет вложение

        Args:
            out_dir (str): Абсолютный путь к каталогу, в котором находится
                результат работы программы
        """
        log.debug(f'Downloading attachment {self.tp}, {self.filename}')

        if not self.url:
            log.warning('Downloading attachment skipped: URL not specified')
            return

        # Создаем папку для хранения вложений этого типа
        (out_dir / 'attachments' / self.pf_dir).mkdir(parents=True, exist_ok=True)

        # Если файл уже скачан, пропускаем его
        if os.path.exists(self.get_path(out_dir)):
            return

        attempts = 0

        # Есть 3 попытки для установления соединения
        # (если ошибка произошла на стороне сервера)
        while attempts < 3:
            try:
                with get(self.url, stream=True) as r:
                    if r.status_code >= 500:
                        attempts += 1
                        continue

                    # Если ошибка на нашей стороне - пропускаем это вложение
                    elif r.status_code >= 400:
                        log.error(
                            'Downloading attachment failed: HTTP code %s. Url: %s',
                            r.status_code, self.url
                        )
                        return

                    # Скачивание происходит порциями (чанками), т.к. максимальный
                    # размер вложения VK - 2ГБ
                    with open(self.get_path(out_dir), 'wb') as file:
                        for chunk in r.iter_content(chunk_size=(1 << 20) * 10):
                            file.write(chunk)

                        return

            except RequestException:
                attempts += 1

        log.error(
            'Downloading attachment failed: HTTP code > 500 or '
            'weak connection. Url: ' + self.url
        )


class Photo(FileAttachment):
    tp = 'photo'
    pf_dir = 'photos'

    def __init__(self, json):
        if json.get('sizes'):
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
        if json.get('deleted'):
            self.url = 'комментарий удалён'
        else:
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
        self.filename = f"{json['id']}.jpg"


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
        return {
            owner_id: {
                'reached': 'завершен',
                'canceled_by_initiator': 'пропущен',
                'canceled_by_receiver': 'отменен'
            },
            self.initiator_id: {
                'reached': 'завершен',
                'canceled_by_initiator': 'отменен',
                'canceled_by_receiver': 'отклонен'
            }
        }[owner_id][self.state]


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

class_to_name = {
    Photo: 'photos',
    Document: 'docs',
    Sticker: 'stickers',
    Gift: 'gifts',
    AudioMessage: 'audios',
    Graffiti: 'graffiti'
}


def gen_attachment(json):
    # Генерирует вложение по его JSON
    return _attachments.get(json['type'], Attachment)(json[json['type']])
