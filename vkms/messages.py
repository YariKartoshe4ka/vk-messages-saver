import datetime
from re import sub
from typing import Dict, List

from . import database as db
from .attachments import Attachment, gen_attachment
from .utils import months


def download(api, peer_id, max_msgs, start_msg_id, buf=5000):
    """
    Загружает сообщения переписки. В начале идут старые сообщения, в конце - новые

    Args:
        api (vk.API): Объект, через который происходит обращение к
            методам VK API
        peer_id (int): Идентификатор переписки, сообщения которой
            необходимо скачать
    """
    max_chunk = 200

    # Получаем количество сообщений в переписке, чтобы сформировать необходимый offset
    res = api.messages.getHistory(count=1, peer_id=peer_id)

    msgs = []
    processed = 0

    max_msgs = min(max_msgs, res['count'])

    # Повторяем действия выше, пока все сообщения не будут загружены
    while processed < max_msgs and res['items']:
        if start_msg_id is None:
            res = api.messages.getHistory(
                offset=res['count'] - min(max_msgs, res['count']) + processed,
                count=min(max_msgs - processed, max_chunk),
                peer_id=peer_id,
                rev=1
            )

        else:
            res = api.messages.getHistory(
                offset=-(processed + min(max_msgs - processed, max_chunk)),
                count=min(max_msgs - processed, max_chunk),
                peer_id=peer_id,
                start_message_id=start_msg_id
            )
            res['items'].reverse()

        msgs += res['items']

        processed += len(res['items'])
        max_msgs = min(max_msgs, res['count'])

        # Чтобы не нагружать память, возвращаем сообщения частями
        if not processed % buf:
            yield msgs
            msgs.clear()

    yield msgs


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
    # __slots__ = (
    #     'id',
    #     'from_id',
    #     'username',
    #     'date',
    #     'action',
    #     'text',
    #     'reply_msg',
    #     'is_expired',
    #     'is_edited',
    #     'geo',
    #     'fwd_msgs',
    #     'atchs',
    #     'text_parsed'
    # )

    def __init__(self, create_message, msg_id, json, usernames):
        # Идентификатор сообщения. Вычисляется немного необычным путем, т.к.
        # сообщения полученные из объектов `reply_message` и `fwd_messages`
        # могут иметь другие поля ID
        self.id: int = msg_id

        # Получение имени отправителя по его ID
        self.from_id = json['from_id']
        self.username: str = usernames[self.from_id]

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
            self.reply_msg = create_message(json['reply_message'])

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
            create_message(fwd_msg_json)
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

    @staticmethod
    def replace_mention(string, replace):
        """
        Заменяет обращения на указанную строку

        Args:
            string (str): Исходная строка
            replace (str): Строка, на которую следует изменить обращение

        Returns:
            str: обработанная строка
        """
        return sub(r'\[[@]?(?:club|id)\d+\|([^\]]+)\]', replace, string)

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


class MessagesFactory:
    _MAX_CACHE_SIZE = 3000
    _CACHE_CHUNK = 500

    def __init__(self, session, usernames):
        self.__leaked_ids: int = 0
        self._session = session
        self._usernames = usernames

        # Словарь для кеширования сообщений в формате id-сообщение
        self.__cache: Dict[int, Message] = {}

    def _free_cache(self):
        if len(self.__cache) == self._MAX_CACHE_SIZE:
            msg_ids = list(self.__cache.keys())

            for i in range(self._CACHE_CHUNK):
                del self.__cache[msg_ids[i]]

    def create_message(self, msg_json):
        self._free_cache()

        if 'id' not in msg_json:
            self.__leaked_ids += 1

        msg_id = msg_json.get('id', -self.__leaked_ids)

        if msg_id in self.__cache:
            return self.__cache[msg_id]

        msg = Message(self.create_message, msg_id, msg_json, self._usernames)
        self.__cache[msg_id] = msg

        return msg

    def parse(self):
        for msg_json, in self._session.query(db.Message.json).yield_per(self._MAX_CACHE_SIZE):
            yield self.create_message(msg_json)
