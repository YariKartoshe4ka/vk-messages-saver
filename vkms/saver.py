from os import makedirs
from re import sub

from pathvalidate import sanitize_filename


def save(out_dir, fmt, peer):
    """
    Конвертирует и сохраняет сообщения в удобном для чтения формате

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        fmt (str): Формат, в котором нужно сохранить переписку
        peer (peers.Peer): Объект переписки
    """
    globals()['save_' + fmt](out_dir, peer)


def save_txt(out_dir, peer):
    """
    Сохраняет переписку в формате TXT. Идея взята у hikiko4ern
    Ссылка: [https://github.com/hikiko4ern/vk_dump]
    """
    # Создаем папку для хранения переписки
    makedirs(f'{out_dir}/dialogs/txt/', exist_ok=True)

    path = '{out_dir}/dialogs/txt/{title}_{peer_id}.txt'.format(
        out_dir=out_dir,
        title=sanitize_filename(peer.title, replacement_text='_'),
        peer_id=peer.info['peer']['id']
    )

    # Сохраняем конвертированный текст
    with open(path, 'w') as file:
        file.write(convert_txt(peer.msgs, peer.info['account']['id']))


def convert_txt(msgs, account_id, is_reply=False):
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
        if not is_reply and msg.reply_msg:
            convert_txt([msg.reply_msg], account_id, True)

            for line in msg.reply_msg.text_parsed:
                text.append('{username} {line}'.format(
                    username=(
                        msg.reply_msg.username + '>'
                        if line == msg.reply_msg.text_parsed[0] else
                        ' ' * (len(msg.reply_msg.username) + 1)
                    ),
                    line=line
                ))

        # Добавляем текст самого сообщения (если есть), обрабатывая обращения
        if msg.text:
            text.extend([
                sub(r'\[(?:club|id)\d+\|([^\]]+)\]', r'\1', line)
                for line in msg.text.split('\n')
            ])

        # Если есть пересланные сообщения, обрабатываем их рекурсивно
        for line in filter(None, convert_txt(msg.fwd_msgs, account_id).split('\n')):
            text.append('| ' + line)

        # Добавляем место/геолокацию (если есть)
        if msg.geo:
            text.append('[место: {}, {}]'.format(*msg.geo))

        # Обрабатываем медиавложения
        for atch in msg.atchs:
            if atch.tp == 'photo':
                text.append(f'[фото: {atch.filename}]')
            elif atch.tp == 'video':
                text.append(f'[видео: {atch.filename}]')
            elif atch.tp == 'audio':
                text.append(f'[аудио: {atch.title}]')
            elif atch.tp == 'doc':
                text.append(f'[документ: {atch.filename}]')
            elif atch.tp == 'link':
                text.append(f'[ссылка: {atch.title} ({atch.url})]')
            elif atch.tp == 'wall':
                text.append(f'[пост: {atch.url}]')
            elif atch.tp == 'wall_reply':
                text.append(f'[комментарий: {atch.url}]')
            elif atch.tp == 'sticker':
                text.append(f'[стикер: {atch.filename}]')
            elif atch.tp == 'gift':
                text.append(f'[подарок: {atch.filename}]')
            elif atch.tp == 'audio_message':
                text.append(f'[голосвое сообщение: {atch.filename}]')
            elif atch.tp == 'graffiti':
                text.append(f'[граффити: {atch.filename}]')

            elif atch.tp == 'call':
                text.append('[{tp}звонок: {state}{duration}]'.format(
                    tp=atch.call_type,
                    state=atch.get_state(account_id),
                    duration=f' ({atch.duration})' if atch.state == 'reached' else ''
                ))

            elif atch.tp == 'poll':
                pool_text = [f'[опрос: "{atch.title}", {atch.anon}, {atch.mult}]']
                max_len = len(pool_text[0])

                for ans in atch.answers:
                    pool_text.append(
                        '  ["{text}":   {{indent}}{is_voted}{rate}% ({votes}/{all_votes})]'.format(
                            text=ans['text'],
                            is_voted='✓ ' if ans['id'] in atch.answer_ids else '',
                            rate=round(ans['rate']),
                            votes=ans['votes'],
                            all_votes=atch.all_votes
                        )
                    )
                    max_len = max(max_len, len(pool_text[-1]) - len('{indent}'))

                for line in pool_text:
                    text.append(line.format(
                        indent=' ' * (max_len - len(line) + len('{indent}'))
                    ))
            else:
                text.append('[uknown attachment]')

        # Если сообщение является исчезающим
        if msg.is_expired:
            text.append('[Сообщение исчезло]')

        # Если сообщение было отредактировано, добавляем заметку
        elif msg.is_edited:
            text.append('(ред.)')

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
