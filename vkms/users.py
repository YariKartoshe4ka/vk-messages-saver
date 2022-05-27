from collections import deque


def download(api, peer):
    """
    Загружает имена участников переписки

    Args:
        api (vk.API): Объект, через который происходит обращение к
            методам VK API
        peer (dict): Объект (словарь) переписки, в который необходимо
            сохранить скачанные имена
    """
    # Идентификаторы пользователей и групп
    user_ids = set()
    group_ids = set()

    # Обход сообщений в ширину
    queue = deque(peer['messages'])

    if peer['info']['peer']['id'] < 2000000000:
        queue.append({'from_id': peer['info']['peer']['id']})

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

            # Если идентификатор > 0, добавляем к пользователям
            else:
                user_ids.add(eff_id)

        # Если у сообщения есть пересланные, то добавляем их в очередь
        if 'fwd_messages' in msg:
            queue.extend(msg['fwd_messages'])

        if 'reply_message' in msg:
            queue.append(msg['reply_message'])

    # Получаем имена пользователей и групп
    res = {'users': [], 'groups': []}

    if user_ids:
        res['users'].extend(api.users.get(user_ids=','.join(user_ids)))

    if group_ids:
        res['groups'].extend(api.groups.getById(group_ids=','.join(group_ids)))

    # Сохраняем имена
    peer['members'] = res


def parse(peer):
    """
    Получает имена пользователей из JSON для дальнейшей работы

    Args:
        peer (dict): Объект (словарь) переписки, в который уже
            были сохранены скачанные сообщения

    Returns:
        Dict[int, str]: Словарь для получения имени пользователя по его ID
    """
    users = {}

    # Обрабатываем пользователей
    for json in peer['members']['users']:
        users[json['id']] = json['first_name']

        # Если пользователь был удален, то у него не будет фамилии
        if json.get('deactivated') != 'deleted':
            users[json['id']] += ' ' + json['last_name']

    # Обрабатываем группы
    for json in peer['members']['groups']:
        users[-json['id']] = json['name']

    return users
