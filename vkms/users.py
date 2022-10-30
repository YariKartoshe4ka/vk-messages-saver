from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import chain

from . import database as db
from .utils import chunks


def collect(msg, user_ids, group_ids):
    # Обход сообщений в ширину
    queue = deque([msg])

    while queue:
        msg = queue.popleft()

        # Добавляем идентификатор отправителя
        from_ids = [msg['from_id']]

        # Добавляем идентификатор пользователя, над которым совершается
        # действие, если у сервисного сообщения такой есть
        if 'action' in msg and 'member_id' in msg['action']:
            from_ids.append(msg['action']['member_id'])

        for from_id in from_ids:
            # Если идентификатор < 0, добавляем к группам
            if from_id < 0:
                group_ids.add(abs(from_id))

            # Если идентификатор > 0 но меньше 2000000000, добавляем к пользователям
            elif from_id < 2000000000:
                user_ids.add(from_id)

        # Если у сообщения есть пересланные, то добавляем их в очередь
        if 'fwd_messages' in msg:
            queue.extend(msg['fwd_messages'])

        if 'reply_message' in msg:
            queue.append(msg['reply_message'])


def download(api, nthreads, user_ids, group_ids):
    """
    Загружает имена участников переписки

    Args:
        api (vk.API): Объект, через который происходит обращение к методам VK API
        user_ids (set): Идентификаторы участников (пользователей) беседы
        group_ids (set): Идентификаторы участников (групп) беседы

    Yields:
        list: Чанк загруженных пользователей, размер не превышает 5000
    """
    with ThreadPoolExecutor(nthreads, 'Thread-') as executor:
        tasks = []

        # Сначала загружаем пользователей
        for chunk in chunks(user_ids, 5000):
            for subchunk in chunks(chunk, 1000):
                tasks.append(executor.submit(
                    api.users.get,
                    user_ids=','.join(map(str, subchunk))
                ))

            yield list(chain.from_iterable(
                future.result()
                for future in as_completed(tasks)
            ))
            tasks.clear()

        # Затем загружаем сообщества
        for chunk in chunks(group_ids, 5000):
            for subchunk in chunks(chunk, 1000):
                tasks.append(executor.submit(
                    api.groups.getById,
                    group_ids=','.join(map(str, subchunk))
                ))

            yield list(chain.from_iterable(
                future.result()
                for future in as_completed(tasks)
            ))


def parse(session):
    """
    Получает имена пользователей из JSON для дальнейшей работы

    Args:
        peer (dict): Объект (словарь) переписки, в который уже
            были сохранены скачанные сообщения

    Returns:
        Dict[int, str]: Словарь для получения имени пользователя по его ID
    """
    users = {}

    for user_id, user_json in session.query(db.User.id, db.User.json):
        if user_id < 0:
            # Обрабатываем группы
            users[user_id] = user_json['name']

        else:
            # Обрабатываем пользователей
            users[user_id] = user_json['first_name']

            # Если пользователь был удален, то у него не будет фамилии
            if user_json.get('deactivated') != 'deleted':
                users[user_id] += ' ' + user_json['last_name']

    return users
