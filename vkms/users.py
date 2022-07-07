from collections import deque

from . import database as db


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
            # Идентификаторы групп передаются как положительные числа
            eff_id = str(abs(from_id))

            # Если идентификатор < 0, добавляем к группам
            if from_id < 0:
                group_ids.add(eff_id)

            # Если идентификатор > 0 но меньше 2000000000, добавляем к пользователям
            elif from_id < 2000000000:
                user_ids.add(eff_id)

        # Если у сообщения есть пересланные, то добавляем их в очередь
        if 'fwd_messages' in msg:
            queue.extend(msg['fwd_messages'])

        if 'reply_message' in msg:
            queue.append(msg['reply_message'])


def download(api, user_ids, group_ids):
    """
    Загружает имена участников переписки

    Args:
        api (vk.API): Объект, через который происходит обращение к
            методам VK API
        peer (dict): Объект (словарь) переписки, в который необходимо
            сохранить скачанные имена
    """
    if user_ids:
        yield api.users.get(user_ids=','.join(user_ids))

    if group_ids:
        yield api.groups.getById(group_ids=','.join(group_ids))

    return


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
