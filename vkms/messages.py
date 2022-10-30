import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from re import sub

from . import database as db
from .attachments import gen_attachment
from .utils import months


def download(api, peer_id, nthreads, max_msgs, start_msg_id):
    """
    Загружает сообщения переписки. В начале идут старые сообщения, в конце - новые

    Args:
        api (vk.API): Объект, через который происходит обращение к методам VK API
        peer_id (int): Идентификатор переписки, сообщения которой необходимо скачать
        max_msgs (int): Кол-во сообщений, которое нужно сохранить (может быть меньше
            заявленного, если переписка содержит меньше сообщений)
        start_msg_id (int): Идентификатор сообщения, после которого следует сохранять
            сообщения (используется для дозаписи новых сообщений)

    Yields:
        list: Чанк загруженных сообщений, размер не превышает 5000
    """
    # Получаем количество сообщений в переписке, чтобы сформировать необходимый offset
    res = api.messages.getHistory(count=1, peer_id=peer_id)
    processed = 0

    max_msgs = min(max_msgs, res['count'])

    with ThreadPoolExecutor(nthreads, 'Thread-') as executor:
        tasks = []

        # Скачиваем, пока все сообщения не будут загружены
        while processed < max_msgs:
            if start_msg_id is None:
                tasks.append(executor.submit(
                    api.messages.getHistory,
                    offset=res['count'] - min(max_msgs, res['count']) + processed,
                    count=min(max_msgs - processed, 200),
                    peer_id=peer_id,
                    rev=1
                ))

            else:
                tasks.append(executor.submit(
                    api.messages.getHistory,
                    offset=-(processed + min(max_msgs - processed, 200)),
                    count=min(max_msgs - processed, 200),
                    peer_id=peer_id,
                    start_message_id=start_msg_id
                ))

            processed += 200

            # Чтобы не нагружать память, возвращаем сообщения частями
            if not processed % 5000:
                yield (
                    msg for future in as_completed(tasks)
                    for msg in future.result()['items'][::-1 + (not start_msg_id) * 2]
                )
                tasks.clear()

        yield (
            msg for future in as_completed(tasks)
            for msg in future.result()['items'][::-1 + (not start_msg_id) * 2]
        )


# Шаблоны текстов сервисных действий в формате тип-текст
#
# Args:
#     member: Имя инициатора действия
#     user: Имя пользователя, над которым выполняется действие
#     text: Новое название беседы
#     msg: Текст закрепленного сообщения
#
_actions = {
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
    '_chat_leave_user': '{member} вышел(-а) из беседы',
    '_chat_return_user': '{member} вернулся(-ась) в беседу'
}


class Message:
    """
    Класс для представления объекта `message` из JSON
    Документация: [https://dev.vk.com/reference/objects/message]

    Args:
        msg_id (int): Идентификатор сообщения
        json (dict): Объект сообщения полученный ранее благодаря VK API
        usernames (dict): Словарь для получения имени пользователя по его ID
        create_message (callable): Функция для создания себе подобных сообщений
    """
    __slots__ = (
        'id',
        'from_id',
        'username',
        'date',
        'action',
        'text',
        'reply_msg',
        'is_expired',
        'is_edited',
        'geo',
        'fwd_msgs',
        'atchs'
    )

    def __init__(self, msg_id, json, usernames, create_message):
        # Идентификатор сообщения
        self.id = msg_id

        # Получение имени отправителя по его ID
        self.from_id = json['from_id']
        self.username = usernames[self.from_id]

        # Получение времени отправления сообщения из формата Unixtime
        self.date = datetime.datetime.fromtimestamp(json['date'])

        # Информация о сервисном действии, `self.action` будет содержать
        # уже готовый текст или `None`
        self.action = None

        if 'action' in json:
            # Если пользователь исключил сам себя, значит он вышел из беседы
            if (json['action']['type'] == 'chat_kick_user'
                    and json['from_id'] == json['action']['member_id']):
                json['action']['type'] = '_chat_leave_user'

            # Если пользователь пригласил сам себя, значит он вернулся в беседу
            if (json['action']['type'] == 'chat_invite_user'
                    and json['from_id'] == json['action']['member_id']):
                json['action']['type'] = '_chat_return_user'

            # Генерация текста из шаблона
            self.action = _actions.get(json['action']['type'], 'unknown action').format(
                user=usernames.get(json['action'].get('member_id')),
                member=self.username,
                text=json['action'].get('text'),
                msg=json['action'].get('message')
            )

        # Текст сообщения (может быть пустым)
        self.text = json['text']

        # Объект сообщения, в ответ на которое было отправлено текущее
        self.reply_msg = (
            create_message(json['reply_message'])
            if 'reply_message' in json else None
        )

        # Флаг, является ли актуальным сообщение (для исчезающих сообщений)
        self.is_expired = json.get('is_expired')

        # Флаг, было ли сообщение отредактировано
        self.is_edited = 'update_time' in json

        # Координаты геолокации (если есть)
        self.geo = json['geo']['coordinates'].values() if 'geo' in json else None

        # Список пересланных сообщений, вместе образуют дерево
        self.fwd_msgs = [
            create_message(fwd_msg_json)
            for fwd_msg_json in json.get('fwd_messages', [])
        ]

        # Список медиавложений сообщения (фото, аудио и т.п.)
        self.atchs = [
            gen_attachment(atch_json)
            for atch_json in json['attachments']
        ]

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
        # Возвращает полную дату (день, месяц, год) отправки сообщения
        return self.date.strftime('%d {} %Y'.format(months[self.date.month]))

    def time(self):
        # Возвращает время (час, минута) отправки сообщения
        return self.date.strftime('%H:%M')


class MessagesFactory:
    """
    Класс отвечающий за создание сообщений. Реализован с оглядкой на эффективное
    использование памяти

    Args:
        session: Открытая сессия к БД нужной переписки
        usernames (dict): Словарь для получения имени пользователя по его ID
    """

    def __init__(self, session, usernames):
        self.__leaked_ids = 0
        self._session = session
        self._usernames = usernames

    def create_message(self, msg_json):
        # Если у сообщения нет ID, задаем ему мнимое
        if 'id' not in msg_json:
            self.__leaked_ids += 1

        msg_id = msg_json.get('id', -self.__leaked_ids)

        # Создаем и возвращаем новое сообщение
        return Message(msg_id, msg_json, self._usernames, self.create_message)

    def parse(self):
        """
        Парсит все доступные в БД сообщения

        Yields:
            Message: текущий объект сообщения
        """
        for msg_json, in self._session.query(db.Message.json).yield_per(5000):
            yield self.create_message(msg_json)
