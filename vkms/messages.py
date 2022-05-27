import datetime
from typing import Dict, List, Tuple

from .attachments import Attachment, gen_attachment
from .utils import months


def download(api, peer_id, peer, max_msgs):
    """
    Загружает сообщения переписки. В начале идут старые сообщения, в конце - новые

    Args:
        api (vk.API): Объект, через который происходит обращение к
            методам VK API
        peer_id (int): Идентификатор переписки, сообщения которой
            необходимо скачать
        peer (dict): Объект (словарь) переписки, в который необходимо
            сохранить скачанные сообщения
    """
    # Получаем часть сообщений
    res = api.messages.getHistory(count=200, peer_id=peer_id)
    msgs = res['items']

    processed = len(msgs)

    # Повторяем действия выше, пока все сообщения не будут загружены
    while processed < min(res['count'], max_msgs):
        res = api.messages.getHistory(offset=processed, count=200, peer_id=peer_id)
        msgs += res['items']

        processed += len(res['items'])

    # Переворачиваем сообщения, чтобы в начале
    # оказались старые, а в конце - новые
    msgs.reverse()

    # Сохраняем сообщения
    peer['messages'] = msgs


# Шаблоны текстов сервисных действий в формате тип-текст
#
# Args:
#     member: Имя инициатора действия
#     user: Имя пользователя, над которым выполняется действие
#     text: Новое название беседы
#     msg: Текст закрепленного сообщения
#
_actions: Dict[str, str] = {
    'chat_photo_update': '{member} обновил(-a) фотографию беседы',
    'chat_photo_remove': '{member} удалил(-a) фотографию беседы',
    'chat_create': '{member} создал(-а) беседу "{text}"',
    'chat_title_update': '{member} изменил(-а) название беседы на "{text}"',
    'chat_invite_user': '{member} пригласил(-а) {user}',
    'chat_kick_user': '{member} исключил(-а) {user}',
    'chat_pin_message': '{member} закрепил(-а) сообщение "{msg}"',
    'chat_unpin_message': '{member} открепил(-а) сообщение',
    'chat_invite_user_by_link': '{member} присоединился(-ась) к беседе по ссылке',
    'conversation_style_update': '{member} изменил(-а) оформление чата',
    'chat_screenshot': '{member} сделал(-а) скриншот беседы',
    '_chat_leave_user': '{member} вышел(-а) из беседы'
}


class Message:
    """
    Класс для представления объекта `message` из JSON
    Документация: [https://dev.vk.com/reference/objects/message]

    Args:
        json (dict): Объект сообщения полученный ранее благодаря VK API
        usernames (dict): Словарь для получения имени пользователя по его ID
    """

    def __init__(self, json, usernames):
        # Идентификатор сообщения. Вычисляется немного необычным путем, т.к.
        # сообщения полученные из объектов `reply_message` и `fwd_messages`
        # могут иметь другие поля ID
        self.id: tuple = Message.get_id_by_json(json)

        # Получение имени отправителя по его ID
        self.username: str = usernames[json['from_id']]

        # Получение времени отправления сообщения из формата Unixtime
        self.date = datetime.datetime.fromtimestamp(json['date'])

        # Информация о сервисном действии, `self.action` будет содержать
        # уже готовый текст или `None`
        self.action: str | None = None

        if 'action' in json:
            # Если пользователь исключил сам себя, значит он вышел из беседы
            if (json['action']['type'] == 'chat_kick_user'
                    and json['from_id'] == json['action']['member_id']):
                json['action']['type'] = '_chat_leave_user'

            # Генерация текста из шаблона
            self.action = _actions.get(json['action']['type'], 'unknown action').format(
                user=usernames.get(json['action'].get('member_id')),
                member=self.username,
                text=json['action'].get('text'),
                msg=json['action'].get('message')
            )

        # Текст сообщения (может быть пустым)
        self.text: str = json['text']

        # Объект сообщения, в ответ на которое было отправлено текущее
        self.reply_msg: Message = None

        if 'reply_message' in json:
            self.reply_msg = gen_message(json['reply_message'], usernames)

        # Флаг, является ли актуальным сообщение (для исчезающих сообщений)
        self.is_expired = json.get('is_expired')

        # Флаг, было ли сообщение отредактировано
        self.is_edited = 'update_time' in json

        # Координаты геолокации (если есть)
        self.geo = None

        if 'geo' in json:
            self.geo = json['geo']['coordinates'].values()

        # Список пересланных сообщений, вместе образуют дерево
        self.fwd_msgs: List[Message] = [
            gen_message(fwd_msg_json, usernames)
            for fwd_msg_json in json.get('fwd_messages', [])
        ]

        # Список медиавложений сообщения (фото, аудио и т.п.)
        self.atchs: List[Attachment] = [
            gen_attachment(atch_json)
            for atch_json in json['attachments']
        ]

    @staticmethod
    def get_id_by_json(json):
        """
        Функция для получения идентификатора сообщения из JSON

        Args:
            json (dict): Объект сообщения полученный ранее благодаря VK API

        Returns:
            Tuple[int, int, int]: Идентификатор
        """
        return (json['date'], json['from_id'], json['conversation_message_id'])

    def full_date(self):
        """
        Возвращает полную дату (день, месяц, год) отправки сообщения

        Returns:
            str: Полная дата
        """
        return self.date.strftime('%d {} %Y'.format(months[self.date.month]))

    def time(self):
        """
        Возвращает время (час, минута) отправки сообщения

        Returns:
            str: Время отправки
        """
        return self.date.strftime('%H:%M')


# Словарь для кеширования сообщений в формате id-сообщение
_msgs: Dict[Tuple[int, int, int], Message] = {}


def parse(peer, usernames):
    """
    Парсит сообщения из JSON в объекты `Message` для дальнейшей работы

    Args:
        peer (dict): Объект (словарь) переписки, в который уже
            были сохранены скачанные сообщения
        usernames (dict): Словарь для получения имени пользователя по его ID

    Returns:
        List[Message]: Список объектов сообщений
    """
    # Очистка кеша сообщений
    _msgs.clear()

    # Генерация сообщений
    return [gen_message(msg, usernames) for msg in peer['messages']]


def gen_message(json, usernames):
    """
    Генерирует и кеширует созданное сообщение по его ID

    Args:
        json (dict): Объект сообщения полученный ранее благодаря VK API
        usernames (dict): Словарь для получения имени пользователя по его ID

    Returns:
        Message: Сгенерированный объект сообщения
    """
    msg_id = Message.get_id_by_json(json)

    if msg_id not in _msgs:
        _msgs[msg_id] = Message(json, usernames)

    return _msgs[msg_id]
