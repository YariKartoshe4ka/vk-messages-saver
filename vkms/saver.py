from os import makedirs


def save(out_dir, peer_id, fmt, msgs):
    """Конвертирует и сохраняет сообщения в удобном для чтения формате

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer_id (int): Идентификатор переписки, сообщения которой
            необходимо сохранить
        fmt (str): Формат, в котором нужно сохранить переписку
        msgs (List[Message]): Список всех сообщений переписки
    """
    globals()['save_' + fmt](out_dir, peer_id, msgs)


def save_txt(out_dir, peer_id, msgs):
    """Сохраняет переписку в формате TXT. Идея взята у hikiko4ern
    Ссылка: [https://github.com/hikiko4ern/vk_dump]
    """
    # Создаем папку для хранения переписки
    makedirs(f'{out_dir}/dialogs/txt/', exist_ok=True)

    # Сохраняем конвертированный текст
    with open(f'{out_dir}/dialogs/txt/{peer_id}.txt', 'w') as file:
        file.write(convert_txt(msgs))


def convert_txt(msgs):
    # Буффер текста переписки
    buf = ''

    prev_msg = None

    for msg in msgs:
        # Если предыдущего сообщения не было, пишем дату текущего сообщения
        if prev_msg is None:
            buf += f'        [{msg.full_date()}]\n'

        # Если предыдущее и текущее сообщения были отправлены в разные дни,
        # пишем дату текущего сообщения
        elif msg.date.day - prev_msg.date.day >= 1:
            buf += f'\n        [{msg.full_date()}]\n'
            prev_msg = None

        # Буффер текста текущего сообщения (каждый элемент - новая строка)
        text = []

        # Если сообщение является сервисным, добавляем текст действия
        if msg.action:
            text.append(f'[{msg.action}]')

        # Если сообщение отправлено в ответ на другое, обрабатываем другое
        # сообщение отдельно
        if msg.reply_msg:
            convert_txt([msg.reply_msg])

            for line in msg.reply_msg.text_parsed:
                text.append('{username} {line}'.format(
                    username=(
                        msg.reply_msg.username + '>'
                        if line == msg.reply_msg.text_parsed[0] else
                        ' ' * (len(msg.reply_msg.username) + 1)
                    ),
                    line=line
                ))

        # Добавляем текст самого сообщения (если есть)
        if msg.text:
            text.extend(msg.text.split('\n'))

        # Если есть пересланные сообщения, обрабатываем их рекурсивно
        for line in filter(None, convert_txt(msg.fwd_msgs).split('\n')):
            text.append('| ' + line)

        # Обрабатываем медиавложения
        for atch in msg.atchs:
            if atch.tp == 'photo':
                text.append(f'[фото: {atch.hash}]')
            elif atch.tp == 'audio_message':
                text.append(f'[голосвое сообщение: {atch.hash}]')
            elif atch.tp == 'wall':
                text.append(f'[пост: {atch.url}]')
            else:
                text.append('{uknown attachment}')

        # Кэшируем полученный текст
        msg.text_parsed = text

        # Записываем полученный текст в буффер переписки
        for line in text:
            if line == text[0]:
                if prev_msg and prev_msg.username == msg.username:
                    username = ' ' * (len(msg.username) + 1)
                else:
                    username = msg.username + ':'

                buf += f"[{msg.time()}] {username} {line}\n"
            else:
                buf += f"{' ' * 7} {' ' * len(msg.username)}  {line}\n"

        # Обновляем предыдущее сообщение
        prev_msg = msg

    # Возвращаем буффер
    return buf
